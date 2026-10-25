"""Eight reproducible teaching datasets. Never real patient data."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from simulation import synthetic_catalog,synthetic_spec,synthetic_dataset
SEED=260905

def main():
    payload=[];all_checks=[]
    for d in synthetic_catalog():
        if d.get('source_kind') == 'bundled_csv':
            continue  # Preserve the uploaded CSV and workbook verbatim.
        key=d['key'];spec=synthetic_spec(key);c,m,covs,vm=synthetic_dataset(key,SEED)
        out=ROOT/'datasets/synthetic'/key;out.mkdir(parents=True,exist_ok=True)
        c.to_csv(out/'curves_long.csv',index=False,float_format='%.10f')
        m.to_csv(out/'participants.csv',index=False,float_format='%.10f')
        keys=['subject','group','condition','side']
        wide=m[keys+['technical_score']].copy()
        for var in vm.variable:
            p=c[c.variable.eq(var)].pivot(index=keys,columns='node',values='value')
            p.columns=[f'{var}_{int(n)}' for n in p.columns]
            wide=wide.merge(p.reset_index(),on=keys,validate='one_to_one')
        for fname in ['curves_wide.csv',key+'.csv']:
            wide.to_csv(out/fname,index=False,float_format='%.10f')
        wide.to_csv(out/'curves_wide_es.csv',index=False,sep=';',decimal=',',float_format='%.10f')
        tr={'node':np.arange(101)}
        for (s,g,cond,side,var),v in c.groupby(keys+['variable'],sort=False):
            tr['|'.join([s,g,cond,side,var])]=v.sort_values('node').value.to_numpy()
        pd.DataFrame(tr).to_csv(out/'curves_transposed.csv',index=False,float_format='%.10f')
        checks=[]
        if int(key[:2])<=6:
            for var,metric,cm,cs,pm,ps in spec['anchors']:
                for group,tm,ts in [('Control',cm,cs),(spec['group'],pm,ps)]:
                    a=c[c.variable.eq(var)&c.group.eq(group)].pivot(index='subject',columns='node',values='value').to_numpy()
                    vals=np.ptp(a,axis=1) if metric=='ROM' else a[:,int(metric.split('_')[1])]
                    assert np.isclose(vals.mean(),tm,atol=1e-10) and np.isclose(vals.std(ddof=1),ts,atol=1e-10)
                    checks.append(dict(dataset=key,variable=var,metric=metric,group=group,n=len(vals),target_mean=tm,target_sd=ts,simulated_mean=float(vals.mean()),simulated_sd=float(vals.std(ddof=1)),units='deg',source=d['url']))
            pd.DataFrame(checks).to_csv(out/'calibration.csv',index=False,float_format='%.8f')
        all_checks+=checks
        assumptions=[
            'SYNTHETIC DATA. No real patients. Not a sample-size calculation.',
            '60 unique participants: 30 cases + 30 controls per example; repeated conditions do not increase independent n.',
            'Angles in degrees; 101 nodes = 0–100% of an already segmented gait cycle.',
            'L is an indexed simulated limb, not necessarily the clinically affected left side.',
            'First six examples preserve v1.3 scalar literature anchors by finite-sample moment matching; temporal shapes and covariance are assumed.',
            'Positive ROM anchors use positive skewed quantiles when normal quantiles would produce a negative ROM.',
            'Examples 07/08 add fully hypothetical repeated conditions. No published treatment or fatigue effect is reproduced.',
            'technical_score is a random numerical teaching covariate, not a validated clinical score.',
            'Cohorts are independent across files. Do not pair example 03 with 05 or pool controls.',
            'p-values and cluster locations are calculated from these synthetic arrays, not from the cited publications.',
        ]
        meta={**d,'seed':SEED,'anchors':spec['anchors'],'n_subjects':60,'n_nodes':101,'synthetic':True,'assumptions':assumptions}
        (out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n', encoding="utf-8")
        intro=f'# {d["title_en"]}\n\n30 cases + 30 controls; {d["n_conditions"]} condition(s). SYNTHETIC DATA.\n\n'
        source=f'Scalar parameters retained from v1.3: [{d["citation"]}]({d["url"]}).' if d['url'] else 'Hypothetical teaching scenario added in v1.4. No published clinical effects.'
        (out/'README.md').write_text(intro+source+'\n\n'+d['population']+'\n\nRecommended configuration: `'+json.dumps(d['recipe'],ensure_ascii=False)+'`.\n\nLoad '+key+'.csv or the Curves_Wide sheet in '+key+'.xlsx. Guided mode recognizes the original datasets and proposes settings. Edited files require manual review.\n\n'+'\n'.join('- '+x for x in assumptions)+'\n', encoding="utf-8")
        payload.append({'spec':meta,'wide':[wide.columns.tolist()]+wide.values.tolist(),'people':[m.columns.tolist()]+m.values.tolist(),'checks':checks})
    dest=ROOT/'datasets/synthetic';pd.DataFrame(all_checks).to_csv(dest/'calibration_all.csv',index=False,float_format='%.8f')
    (dest/'catalog.json').write_text(json.dumps(synthetic_catalog(),ensure_ascii=False,indent=2), encoding="utf-8")
    (ROOT/'datasets/workbook_inputs.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False), encoding="utf-8")
    print(f'{len(payload)} examples; {sum(d["n_total"] for d in synthetic_catalog())} unique synthetic participants in the full catalog; 30 per group; {len(all_checks)} calibrated moments')

if __name__=='__main__':main()
