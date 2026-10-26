"""Reproducible finite-scenario Type I error study of GaitSPM production inference.

Results default to the private paper directory. See research/monte_carlo/README.md.
No resampling until success, no significance-based stopping, no spm1d version switch.
"""
from __future__ import annotations
import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_name] = '1'
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import sys
import time
import warnings
from collections import Counter

import numpy as np
import pandas as pd
import scipy
from scipy.ndimage import gaussian_filter1d
from scipy.stats import beta, binomtest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'vendor'))
sys.path.insert(0, str(ROOT/'app'))
import gaitspm_engine as E

SEED = 20261026
Q = 101
ALPHA = .05
VARIABLES = ['HipFlexion', 'KneeFlexion', 'AnkleDorsiflexion']
EFFECTS = ['group', 'condition', 'interaction']


def scenarios():
    items = []
    for design in E.ADVANCED_DESIGNS:
        base = dict(design=design, n=[30,30], fwhm=10., fields=1, rho=0.,
                    covariance='cs', variance='equal', null='global', category='assumptions_met')
        options = [
            ('baseline', {}), ('small_n', {'n':[12,12]}), ('large_n', {'n':[60,60]}),
            ('rough', {'fwhm':5.}), ('smooth', {'fwhm':20.}),
            ('family_independent', {'fields':3}), ('family_correlated', {'fields':3,'rho':.8}),
            ('partial_null', {'fields':3,'rho':.5,'null':'partial'}),
        ]
        for label, changes in options:
            items.append({**base, **changes, 'id':design+'_'+label})
    extra = [
        ('ancova_unbalanced', 'ancova', dict(n=[12,36])),
        ('ancova_small_group_high_variance', 'ancova', dict(n=[12,36],variance='small_high',category='assumption_violation')),
        ('ancova_large_group_high_variance', 'ancova', dict(n=[12,36],variance='large_high',category='assumption_violation')),
        ('glm_predictor_dependent_variance', 'glm', dict(variance='predictor',category='assumption_violation')),
        ('anova2_unequal_variance', 'anova2', dict(variance='cell',category='assumption_violation')),
        ('anova2onerm_nonspherical', 'anova2onerm', dict(covariance='ar1',category='assumption_violation')),
    ]
    for label, design, changes in extra:
        base = next(x for x in items if x['id']==design+'_baseline')
        items.append({**base, **changes, 'id':label})
    return items


def smooth_noise(rng, shape, fwhm):
    """Gaussian kernel on padded white noise, cropped and variance-normalized.

    Padding prevents circular endpoint dependence; normalization is theoretical,
    never per-realization moment matching. FWHM uses spm1d's kernel convention.
    """
    sigma = fwhm / np.sqrt(8*np.log(2))
    radius = int(4*sigma + .5)
    kernel = np.exp(-.5*(np.arange(-radius,radius+1)/sigma)**2)
    kernel /= kernel.sum()
    raw = rng.standard_normal((*shape, Q+2*radius))
    return gaussian_filter1d(raw, sigma, axis=-1, mode='constant', truncate=4)[...,radius:radius+Q] / np.sqrt(np.sum(kernel**2))


def generate(case, replicate, seed=SEED):
    """Independent streams by stable scenario ID and replicate, not worker order."""
    code = int.from_bytes(hashlib.sha256(case['id'].encode()).digest()[:4], 'little')
    rng = np.random.default_rng(np.random.SeedSequence([seed, code, replicate]))
    design, m = case['design'], case['fields']
    factorial = design in ('anova2','anova2onerm')
    nc = 3 if factorial else 1
    rows=[]
    for a,n in enumerate(case['n']):
        for b in range(nc):
            for i in range(n):
                sub=f'g{a}s{i:03d}' + (f'c{b}' if design=='anova2' else '')
                rows.append((sub, f'G{a}', f'C{b}', 'L', a, b))
    meta=pd.DataFrame(rows, columns=['subject','group','condition','side','A','B'])
    nrows=len(meta)
    labels=meta.subject.tolist()
    # Correlation is imposed before mean effects; all marginal residual SDs are 1
    # except in explicitly labelled variance-violation scenarios.
    if design=='anova2onerm':
        nsub=sum(case['n'])
        white=smooth_noise(rng,(nsub,nc,m+1),case['fwhm'])
        C=.5*np.ones((nc,nc))+.5*np.eye(nc) if case['covariance']=='cs' else .8**np.abs(np.subtract.outer(np.arange(nc),np.arange(nc)))
        white=np.einsum('ab,ibmq->iamq', np.linalg.cholesky(C), white)
        ids={s:i for i,s in enumerate(dict.fromkeys(labels))}
        noise=np.stack([white[ids[s],b] for s,b in zip(labels,meta.B)])
    else:
        noise=smooth_noise(rng,(nrows,m+1),case['fwhm'])
    Y=np.sqrt(case['rho'])*noise[:,0:1,:]+np.sqrt(1-case['rho'])*noise[:,1:,:]
    A=meta.A.to_numpy();B=meta.B.to_numpy()
    x=rng.normal(size=nrows)+(.8*A if design=='ancova' else 0)
    z=.35*x+np.sqrt(1-.35**2)*rng.normal(size=nrows)
    meta['speed']=x;meta['age']=z
    if case['variance']=='small_high':Y[A==0]*=3
    elif case['variance']=='large_high':Y[A==1]*=3
    elif case['variance']=='predictor':Y*=np.where(x>0,3.,1.)[:,None,None]
    elif case['variance']=='cell':Y[(A==1)&(B==2)]*=3
    bump=np.exp(-.5*((np.arange(Q)-50)/15)**2)
    if design=='ancova':Y+=(.6*x+.3*z)[:,None,None]*bump
    elif design=='glm':Y+=(.6*z)[:,None,None]*bump
    if case['null']=='partial':
        # Only variable 0 has a nonnull target: adjusted group, x coefficient,
        # or factorial group main effect. Condition and interaction stay null.
        Y[:,0,:]+=(x if design=='glm' else A)[:,None]*1.5*bump
    names=EFFECTS if factorial else ['contrast']
    null_mask=np.ones((m,len(names)),bool)
    if case['null']=='partial':null_mask[0,0]=False
    cfg=dict(design=design,mode='param',equal_var=True,alpha=ALPHA,two_tailed=True,
             field_correction='bonferroni',field_count=m,groups=['G0','G1'],
             cond=None if factorial else 'C0',cond_levels=['C0','C1','C2'] if factorial else None,
             group_filter=None,side_mode='L',covariates=['speed','age'],contrast=[0,1,0],
             iterations=5000,posthoc=False,band_group=None,lang='en')
    models=[]
    for j in range(m):
        if factorial:
            codes={s:i for i,s in enumerate(sorted(set(labels)))}
            model=dict(Y=Y[:,j,:], A=A, B=B, SUBJ=np.array([codes[s] for s in labels]))
        else:
            cols=[np.ones(nrows)]+([A] if design=='ancova' else [])+[x-x.mean(),z-z.mean()]
            model=dict(Y=Y[:,j,:],X=np.column_stack(cols),contrast=np.array([0,1,0,0] if design=='ancova' else [0,1,0]))
        models.append(model)
    return models, meta, cfg, null_mask


def canonical(models, meta):
    parts=[]
    for var,model in zip(VARIABLES,models):
        n=len(meta)
        part=meta[['subject','group','condition','side']].loc[meta.index.repeat(Q)].reset_index(drop=True)
        part['variable']=var;part['node']=np.tile(np.arange(Q),n);part['value']=model['Y'].ravel()
        parts.append(part)
    return pd.concat(parts,ignore_index=True)


def evaluate(models,cfg):
    m=len(models); names=EFFECTS if cfg['design'].startswith('anova2') else ['contrast']
    crossed=np.zeros((m,len(names)),bool);confirmed=crossed.copy();details={}
    for j,model in enumerate(models):
        inferred,alpha,effect_count=E.infer_model_fields(model,cfg)
        for k,name in enumerate(names):
            field,inf=inferred[name]
            if not np.isfinite(inf.z).all() or not np.isfinite(inf.zstar):
                raise ValueError('Nonfinite statistic or threshold')
            clusters=E.extract_clusters(inf,np.asarray(inf.z))
            if any(not np.isfinite(c['p']) for c in clusters):raise ValueError('Nonfinite cluster probability')
            result=dict(alpha=alpha,effect_count=effect_count,family_alpha=ALPHA,clusters=clusters)
            E.apply_field_correction({'field':result},cfg)
            crossed[j,k]=bool(inf.h0reject)
            confirmed[j,k]=bool(E.confirmed_clusters(result))
            details[j,k]=(field,inf,result)
    return crossed,confirmed,details


def verify_end_to_end(models,meta,cfg,details):
    """Checkpoint through actual participant preparation, inference and correction."""
    c=canonical(models,meta);vm=E.classify_variables(VARIABLES[:len(models)])
    names=EFFECTS if cfg['design'].startswith('anova2') else ['contrast']
    for k,name in enumerate(names):
        rs,_=E.run_analysis(c,meta.sample(frac=1,random_state=17),vm,{**cfg,'factor_effect':name})
        for j,var in enumerate(vm.variable):
            r=rs[var]
            if 'error' in r:raise AssertionError(r['error'])
            _,inf,expected=details[j,k]
            np.testing.assert_allclose(r['z'],inf.z,rtol=1e-9,atol=1e-9)
            np.testing.assert_allclose(r['zstar'],inf.zstar,rtol=1e-10,atol=1e-10)
            if r['h0reject']!=bool(inf.h0reject):raise AssertionError('Decision mismatch')
            got=E.confirmed_clusters(r);want=E.confirmed_clusters(expected)
            if len(got)!=len(want):raise AssertionError('Confirmed cluster count mismatch')
            for a,b in zip(got,want):
                np.testing.assert_allclose([a[x] for x in ('x0','x1','p','p_field_adj')],
                                           [b[x] for x in ('x0','x1','p','p_field_adj')],rtol=1e-9,atol=1e-9)


def chunk_job(case,start,stop,seed,path):
    begin=time.perf_counter();rows=[];cross=[];warns=Counter()
    for rep in range(start,stop):
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter('always')
            models,meta,cfg,mask=generate(case,rep,seed)
            a,b,details=evaluate(models,cfg)
            if rep==start:verify_end_to_end(models,meta,cfg,details)
        warns.update(str(w.message) for w in seen)
        cross.append(a);rows.append(b)
    tmp=Path(str(path)+'.tmp')
    with tmp.open('wb') as f:
        np.savez_compressed(f,crossed=np.asarray(cross),confirmed=np.asarray(rows),null_mask=mask,
                            start=start,stop=stop,scenario=case['id'],seed=seed,
                            warnings=json.dumps(dict(warns)),seconds=time.perf_counter()-begin)
    tmp.replace(path)
    return case['id'],start,stop


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance(reps,seed,batch):
    sources=['research/monte_carlo/monte_carlo.py','research/monte_carlo/README.md','app/gaitspm_engine.py','app/gaitspm_app.py']
    vendor=hashlib.sha256()
    for p in sorted((ROOT/'vendor/spm1d').rglob('*.py')):
        vendor.update(str(p.relative_to(ROOT)).encode());vendor.update(p.read_bytes())
    return dict(protocol='gaitspm-mc-1',replicates=reps,seed=seed,batch_size=batch,
                scenarios=scenarios(),alpha=ALPHA,nodes=Q,
                sources={x:sha(ROOT/x) for x in sources},vendor_sha256=vendor.hexdigest(),
                environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                                 pandas=pd.__version__,spm1d=E.spm1d.__version__,platform=platform.platform()))


def interval(k,n):
    return (0. if k==0 else float(beta.ppf(.025,k,n-k+1)),
            1. if k==n else float(beta.ppf(.975,k+1,n-k)))


def summarize(out,manifest):
    rows=[];warnings_all=Counter()
    for case in manifest['scenarios']:
        parts=sorted((out/'chunks').glob(case['id']+'__*.npz'))
        crossed=[];confirmed=[];next_rep=0
        for path in parts:
            with np.load(path,allow_pickle=False) as z:
                if int(z['start'])!=next_rep or str(z['scenario'])!=case['id']:raise ValueError('Missing or overlapping chunk')
                next_rep=int(z['stop']);mask=z['null_mask'];crossed.append(z['crossed']);confirmed.append(z['confirmed'])
                warnings_all.update(json.loads(str(z['warnings'])))
        if next_rep!=manifest['replicates']:raise ValueError('Incomplete scenario: '+case['id'])
        arrays={'threshold':np.concatenate(crossed),'confirmed_cluster':np.concatenate(confirmed)}
        names=EFFECTS if case['design'].startswith('anova2') else ['contrast']
        for endpoint,a in arrays.items():
            events=[('family','all_true_nulls',np.any(a[:,mask],axis=1),ALPHA)]
            for j in range(case['fields']):
                for k,name in enumerate(names):
                    if mask[j,k]:events.append((VARIABLES[j],name,a[:,j,k],ALPHA/(case['fields']*len(names))))
            for var,effect,event,nominal in events:
                count=int(event.sum());n=len(event);p=count/n;lo,hi=interval(count,n)
                rows.append(dict(scenario=case['id'],design=case['design'],category=case['category'],null=case['null'],
                                 n0=case['n'][0],n1=case['n'][1],fwhm=case['fwhm'],fields=case['fields'],rho=case['rho'],
                                 endpoint=endpoint,variable=var,effect=effect,rejections=count,replicates=n,rate=p,
                                 ci95_low=lo,ci95_high=hi,mc_se=np.sqrt(p*(1-p)/n),nominal=nominal,
                                 inflation_p=float(binomtest(count,n,nominal,alternative='greater').pvalue)))
    frame=pd.DataFrame(rows)
    # Exploratory multiplicity screen only for primary family outcomes satisfying assumptions.
    selected=(frame.endpoint=='threshold')&(frame.variable=='family')&(frame.category=='assumptions_met')
    frame['holm_inflation_p']=np.nan
    frame.loc[selected,'holm_inflation_p']=E.adjust_pvalues(frame.loc[selected,'inflation_p'].to_numpy(),'holm')
    frame.to_csv(out/'summary.csv',index=False)
    (out/'warnings.json').write_text(json.dumps(dict(warnings_all),indent=2)+'\n',encoding='utf-8')
    plot_summary(frame,out)
    fam=frame[(frame.endpoint=='threshold')&(frame.variable=='family')]
    lines=['# Monte Carlo results — finite scenario study','',
           'Private research output. Numerical concordance and empirical error control are different claims.',
           f"Completed {len(fam)} scenarios × {manifest['replicates']} replicates; spm1d {manifest['environment']['spm1d']}.",
           'Primary endpoint: at least one true-null field crosses its corrected threshold. Secondary endpoint: at least one confirmed true-null cluster.',
           'Exact 95% binomial intervals are marginal, not simultaneous. No general validity, equivalence or clinical claim follows from this finite study.',
           'Partial-null scenarios count false rejections only; variable 0 has a real target effect. Factorial group effects alone are nonnull in that variable.',
           'Per-field rates are assessed against alpha/(variables × effects), not 0.05. Bonferroni can be conservative.',
           'Every chunk checks its first replicate through the full application; all replicates use the shared production inference and correction functions.',
           '', '| Scenario | Assumptions | False positives / N | Rate | Exact 95% CI |',
           '|---|---|---:|---:|---|']
    for r in fam.itertuples():lines.append(f'| {r.scenario} | {r.category} | {r.rejections}/{r.replicates} | {r.rate:.4f} | {r.ci95_low:.4f}–{r.ci95_high:.4f} |')
    lines+=['','Use summary.csv for every field, endpoint and exploratory Holm-adjusted inflation test. A nonsignificant inflation test is not evidence of equivalence.',
            'Warnings are counted in warnings.json. No failed replication is silently omitted: any exception stops completion and leaves the run incomplete.',
            'Refer to the frozen manifest.json for source hashes, scenario definitions, seed, environment and execution scope.']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    checks={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
    (out/'SHA256SUMS.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')


def plot_summary(frame,out):
    import matplotlib.pyplot as plt
    fam=frame[(frame.endpoint=='threshold')&(frame.variable=='family')].reset_index(drop=True)
    fig,ax=plt.subplots(figsize=(11,13))
    for i,r in fam.iterrows():
        color='#D95319' if r['category']=='assumption_violation' else '#0072BD'
        ax.errorbar(r['rate'],i,xerr=[[r['rate']-r.ci95_low],[r.ci95_high-r['rate']]],fmt='o',color=color,capsize=2)
    ax.axvline(.05,color='black',linestyle='--',linewidth=1,label='Nominal family alpha = 0.05')
    ax.set_yticks(range(len(fam)),fam.scenario);ax.invert_yaxis()
    ax.set_xlabel('Familywise false-positive rate (exact marginal 95% binomial CI)')
    ax.set_title('GaitSPM · finite-scenario Type I error study\nBlue: assumptions met; orange: assumption violations')
    ax.legend();ax.grid(axis='x',alpha=.2);fig.tight_layout()
    for ext in ('png','svg','pdf'):fig.savefig(out/('familywise_error.'+ext),dpi=250)
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--replicates',type=int,default=5000)
    ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--batch-size',type=int,default=100)
    ap.add_argument('--seed',type=int,default=SEED)
    ap.add_argument('--output',type=Path,default=ROOT/'paper/monte_carlo_runs')
    ap.add_argument('--plan-only',action='store_true')
    args=ap.parse_args()
    if min(args.replicates,args.workers,args.batch_size)<1:ap.error('Positive counts required')
    if E.spm1d.__version__!='0.4.53':raise SystemExit('This protocol is pinned to spm1d 0.4.53')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);(out/'chunks').mkdir(exist_ok=True)
    plan=provenance(args.replicates,args.seed,args.batch_size)
    path=out/'manifest.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old['plan']!=plan:raise SystemExit('Manifest mismatch: use a new output directory; do not mix source versions or plans')
    else:
        path.write_text(json.dumps(dict(frozen_utc=datetime.now(timezone.utc).isoformat(),plan=plan),indent=2)+'\n',encoding='utf-8')
    if args.plan_only:print(path);return
    tasks=[]
    for case in plan['scenarios']:
        for start in range(0,args.replicates,args.batch_size):
            stop=min(start+args.batch_size,args.replicates);dest=out/'chunks'/f"{case['id']}__{start:06d}.npz"
            if not dest.exists():tasks.append((case,start,stop,args.seed,dest))
    print(f'{len(plan["scenarios"])} scenarios, {args.replicates} replicates each, {len(tasks)} remaining chunks',flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs=[pool.submit(chunk_job,*t) for t in tasks]
        for i,f in enumerate(as_completed(jobs),1):
            try:label,start,stop=f.result()
            except Exception as error:
                (out/'failure.txt').write_text(repr(error),encoding='utf-8')
                for j in jobs:j.cancel()
                raise
            print(f'{i}/{len(jobs)} {label} {start}:{stop}',flush=True)
    summarize(out,plan)
    print('Completed: '+str(out/'report.md'),flush=True)


if __name__=='__main__':main()
