"""Public, deterministic end-to-end concordance with direct spm1d calls.
Run: python tests/test_spm1d_validation.py [--report]
"""
import json
from pathlib import Path
import sys
import unittest
import warnings
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from test_audit import E, config, ROOT

REPORT = []


def fixture(independent=False, signal=True):
    rng = np.random.default_rng(39271)
    n, q = 12, 101
    bump = np.exp(-((np.arange(q)-55)/13)**2) * (1 if signal else 0)
    rows, arrays, covariates = [], {}, {}
    for a in range(3):
        baseline = gaussian_filter1d(rng.normal(size=(n,q)), 4, axis=1)
        speed = rng.uniform(.8,1.8,n)
        for b in range(3):
            Y = baseline + gaussian_filter1d(rng.normal(size=(n,q)),3,axis=1)
            Y += (a*.45+b*.4+a*b*.3+speed[:,None]*.5)*bump
            arrays[a,b] = Y
            covariates[a,b] = speed
            for i, y in enumerate(Y):
                sub = f'g{a}s{i:02d}' + (f'c{b}' if independent else '')
                rows.append(dict(subject=sub,group=f'G{a}',condition=f'C{b}',side='L',speed=speed[i],
                                 **{f'HipFlexion_{j}':v for j,v in enumerate(y)}))
    raw = pd.DataFrame(rows)
    canon, meta, _ = E.canon_from_wide(raw,E.find_curve_blocks(raw.columns),
                                      {k:k for k in ('subject','group','condition','side')})
    return canon, meta, E.classify_variables(['HipFlexion']), arrays, covariates


class ConcordanceTests(unittest.TestCase):
    def compare(self, label, result, reference):
        self.assertNotIn('error',result,result)
        np.testing.assert_allclose(result['z'],reference.z,rtol=1e-10,atol=1e-10)
        self.assertAlmostEqual(result['zstar'],float(reference.zstar),10)
        self.assertEqual(result['h0reject'],bool(reference.h0reject))
        clusters=sorted(reference.clusters or [],key=lambda c:c.endpoints[0])
        self.assertEqual(len(result['clusters']),len(clusters))
        errors=[]
        for got,ref in zip(result['clusters'],clusters):
            np.testing.assert_allclose([got['x0'],got['x1']],ref.endpoints,rtol=0,atol=1e-9)
            self.assertAlmostEqual(got['p'],float(ref.P),10)
            errors.append(abs(got['p']-float(ref.P)))
        REPORT.append(dict(case=label,max_statistic_error=float(np.max(abs(result['z']-reference.z))),
                           threshold_error=abs(result['zstar']-float(reference.zstar)),
                           clusters=len(clusters),max_cluster_p_error=max(errors,default=0.0)))

    def test_existing_designs(self):
        c,m,vm,ys,xs=fixture()
        for name in ['student','welch','paired_cond','anova1','anova1rm','regress']:
            d='ttest2' if name in ('student','welch') else name
            cfg=config(c,design=d,groups=['G0','G1'] if d=='ttest2' else ['G0','G1','G2'],
                       cond='C0',cond_levels=['C0','C1'] if d=='paired_cond' else ['C0','C1','C2'],
                       group_filter='G0' if d in ('paired_cond','anova1rm','regress') else None,
                       equal_var=name!='welch',covariate='speed',posthoc=False)
            result=E.run_analysis(c,m,vm,cfg)[0]['HipFlexion']
            if d=='ttest2':ref=E.spm1d.stats.ttest2(ys[0,0],ys[1,0],equal_var=name!='welch')
            elif d=='paired_cond':ref=E.spm1d.stats.ttest_paired(ys[0,0],ys[0,1])
            elif d=='anova1':ref=E.spm1d.stats.anova1(np.vstack([ys[a,0] for a in range(3)]),np.repeat(range(3),12),equal_var=True)
            elif d=='anova1rm':ref=E.spm1d.stats.anova1rm(np.vstack([ys[0,b] for b in range(3)]),np.repeat(range(3),12),np.tile(range(12),3))
            else:ref=E.spm1d.stats.regress(ys[0,0],xs[0,0])
            infer=ref.inference(.05,interp=True,**({} if d.startswith('anova') else {'two_tailed':True}))
            self.compare(name,result,infer)

    def test_glm_ancova(self):
        c,m,vm,ys,xs=fixture()
        for d in ['glm','ancova']:
            cfg=config(c,design=d,cond='C0',groups=['G0','G1'],covariates=['speed'],contrast=[0,1])
            if d=='glm':cfg['group_filter']='G0'
            r=E.run_analysis(c,m.sample(frac=1,random_state=7),vm,cfg)[0]['HipFlexion']
            Y=ys[0,0] if d=='glm' else np.vstack([ys[0,0],ys[1,0]])
            x=xs[0,0] if d=='glm' else np.concatenate([xs[0,0],xs[1,0]])
            X=np.column_stack([np.ones(len(x)),x-x.mean()]) if d=='glm' else np.column_stack([np.ones(len(x)),np.repeat([0,1],12),x-x.mean()])
            contrast=[0,1] if d=='glm' else [0,1,0]
            ref=E.spm1d.stats.glm(Y,X,contrast).inference(.05,two_tailed=True,interp=True)
            self.compare(d,r,ref)
            E.fig_to_bytes(E.fig_detail(r,None,'en',cfg),'svg')
            self.assertTrue(E.methods_text(cfg,{'HipFlexion':r},'en'))
            self.assertTrue(E.results_text({'HipFlexion':r},cfg,'en'))

    def test_factorial_effects(self):
        for d in ['anova2','anova2onerm']:
            c,m,vm,ys,_=fixture(independent=d=='anova2')
            Y=np.vstack([ys[a,b] for a in range(3) for b in range(3)])
            A=np.repeat(range(3),36);B=np.tile(np.repeat(range(3),12),3)
            subjects=np.concatenate([np.tile(np.arange(12)+a*12,3) for a in range(3)])
            refs=getattr(E.spm1d.stats,d)(Y,A,B,*([subjects] if d=='anova2onerm' else []),equal_var=True)
            for idx,effect in enumerate(['group','condition','interaction']):
                cfg=config(c,design=d,groups=['G0','G1','G2'],cond=None,cond_levels=['C0','C1','C2'],factor_effect=effect)
                r=E.run_analysis(c,m,vm,cfg)[0]['HipFlexion']
                self.compare(d+'/'+effect,r,refs[idx].inference(.05/3,interp=True))
                self.assertEqual(r['n_included'],108 if d=='anova2' else 36)
                for cluster in r['clusters']:self.assertAlmostEqual(cluster['p_field_adj'],min(1,3*cluster['p']))
                E.fig_to_bytes(E.fig_detail(r,None,'en',cfg),'svg')
                self.assertTrue(E.results_text({'HipFlexion':r},cfg,'en'))

    def test_two_fields_factor_family_and_bridge(self):
        c,m,vm,ys,_=fixture()
        c2=pd.concat([c,c.assign(variable='KneeFlexion')],ignore_index=True)
        vm2=E.classify_variables(['HipFlexion','KneeFlexion'])
        cfg=config(c2,design='anova2onerm',groups=['G0','G1','G2'],cond=None,
                   cond_levels=['C0','C1','C2'],factor_effect='interaction')
        rs,_=E.run_analysis(c2,m,vm2,cfg)
        for r in rs.values():
            self.assertNotIn('error',r)
            self.assertAlmostEqual(r['alpha'],.05/6)
            for cluster in r['clusters']:
                self.assertAlmostEqual(cluster['p_field_adj'],min(1,6*cluster['p']))
        for design in E.ADVANCED_DESIGNS:
            data,meta,mapping,_,_=fixture(independent=design=='anova2')
            ns=dict(E.__dict__)
            exec((ROOT/'app/simulation.py').read_text(encoding='utf-8'),ns)
            exec((ROOT/'app/bridge.py').read_text(encoding='utf-8'),ns)
            ns['_store'](data,meta,['speed'])
            cfg=config(data,design=design,cond='C0' if design in ('glm','ancova') else None,
                       groups=['G0','G1'],cond_levels=['C0','C1'],covariates=['speed'],
                       contrast=[0,1],vars=['HipFlexion'])
            def call(name,*args):
                result=json.loads(ns[name](*args));self.assertTrue(result['ok'],result);return result
            call('js_run_init',json.dumps(cfg));call('js_run_var','HipFlexion')
            self.assertFalse(call('js_run_done')['errors'])
            self.assertIsNotNone(call('js_explain')['summaries'][0]['model'])
            call('js_texts');call('js_table_csv');call('js_fig_detail','HipFlexion',80)

    def test_null_and_permutation(self):
        c,m,vm,ys,_=fixture(signal=False)
        cfg=config(c,groups=['G0','G1'],cond='C0',posthoc=False)
        self.compare('null/Student',E.run_analysis(c,m,vm,cfg)[0]['HipFlexion'],
                     E.spm1d.stats.ttest2(ys[0,0],ys[1,0],equal_var=True).inference(.05,two_tailed=True,interp=True))
        cfg.update(mode='nonparam',iterations=100,seed=2026)
        got=E.run_analysis(c,m,vm,cfg)[0]['HipFlexion']
        old=np.random.get_state()
        try:
            np.random.seed(2026)
            ref=E.spm1d.stats.nonparam.ttest2(ys[0,0],ys[1,0]).inference(.05,iterations=100,two_tailed=True)
        finally:np.random.set_state(old)
        self.compare('permutation/Student/100',got,ref)

    def test_invalid_models_and_missing_cases(self):
        c,m,vm,_,_=fixture()
        def run(**kw):
            cfg=config(c,design='glm',cond='C0',covariates=['speed'],contrast=[0,1],**kw)
            return E.run_analysis(c,m,vm,cfg)[0]['HipFlexion']
        self.assertIn('error',run(mode='nonparam'))
        self.assertIn('error',run(equal_var=False))
        bad=m.copy();bad['speed']=1.
        cfg=config(c,design='glm',cond='C0',covariates=['speed'],contrast=[0,1])
        self.assertIn('error',E.run_analysis(c,bad,vm,cfg)[0]['HipFlexion'])
        bad=m.copy();bad.loc[bad.subject.eq('g0s00'),'speed']=np.nan
        r=E.run_analysis(c,bad,vm,cfg)[0]['HipFlexion']
        self.assertNotIn('error',r);self.assertIn('g0s00',r['excluded_subjects'])
        cfg=config(c,design='anova2',groups=['G0','G1'],cond=None,cond_levels=['C0','C1'])
        self.assertIn('Repeated subject',E.run_analysis(c,m,vm,cfg)[0]['HipFlexion']['error'])
        cfg['design']='anova2onerm'
        incomplete=c[~(c.subject.eq('g0s00')&c.condition.eq('C0'))]
        self.assertIn('balanced',E.run_analysis(incomplete,m,vm,cfg)[0]['HipFlexion']['error'])


if __name__=='__main__':
    report='--report' in sys.argv
    if report:sys.argv.remove('--report')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',UserWarning)
        result=unittest.main(exit=False)
    if report and result.result.wasSuccessful():
        folder=ROOT/'docs/validation';folder.mkdir(parents=True,exist_ok=True)
        (folder/'concordance.json').write_text(json.dumps({'spm1d':E.spm1d.__version__,'seed':39271,'cases':REPORT},indent=2)+'\n',encoding='utf-8')
        lines=['# Validated against spm1d','', 'Generated by `python tests/test_spm1d_validation.py --report`. Seed 39271; spm1d '+E.spm1d.__version__+'.', '',
               'These are software concordance checks, not clinical validation. The direct reference uses independently assembled arrays and the bundled upstream spm1d. Tolerances: statistic 1e-10, threshold/p 10 decimal places, endpoints 1e-9 nodes. Full fields, cluster counts, endpoints, p-values and rejection decisions are asserted. This does not independently validate spm1d itself.', '',
               '| Case | Max statistic error | Threshold error | Clusters | Max cluster p error |','|---|---:|---:|---:|---:|']
        lines += [f"| {r['case']} | {r['max_statistic_error']:.3g} | {r['threshold_error']:.3g} | {r['clusters']} | {r['max_cluster_p_error']:.3g} |" for r in REPORT]
        (folder/'index.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sys.exit(not result.result.wasSuccessful())
