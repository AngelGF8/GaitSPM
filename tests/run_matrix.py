"""Extended reproducible audit. Generates machine-readable results, not a clinical certificate."""
import json, sys, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from test_audit import E, ROOT, config, synthetic_catalog, synthetic_dataset

warnings.filterwarnings('ignore',category=FutureWarning)
started=time.time();rows=[]
OUT=ROOT/'.test-output/matrix'
OUT.mkdir(parents=True,exist_ok=True)
for item in synthetic_catalog():
    c,m,_,vm=synthetic_dataset(item['key'])
    for label,settings in [('Student',{}),('Welch',{'equal_var':False}),('SnPM',{'mode':'nonparam','iterations':5000})]:
        cfg=config(c,**settings);rs,_=E.run_analysis(c,m,vm,cfg)
        for var,r in rs.items():
            rows.append(dict(dataset=item['key'],test=label,variable=var,ok='error' not in r,
                error=r.get('error',''),alpha=r.get('alpha'),threshold=r.get('zstar'),
                clusters=len(E.confirmed_clusters(r)),iterations_actual=r.get('iterations_actual')))
        print(item['key'],label,'errors',sum('error' in r for r in rs.values()),flush=True)

# A separate iid Gaussian-field null experiment: never use moment-matched bases for FWER.
rng=np.random.default_rng(901);null_rejects=0;repetitions=200
for rep in range(repetitions):
    rejected=False
    for field in range(3):
        a=gaussian_filter1d(rng.normal(size=(10,101)),4,axis=1)
        b=gaussian_filter1d(rng.normal(size=(10,101)),4,axis=1)
        rejected |= bool(E.spm1d.stats.ttest2(a,b,equal_var=True).inference(.05/3,two_tailed=True).h0reject)
    null_rejects+=rejected
# Wilson interval describes Monte Carlo uncertainty; no binary certification threshold.
rate=null_rejects/repetitions;z=1.96;den=1+z*z/repetitions
mid=(rate+z*z/(2*repetitions))/den
half=z*np.sqrt(rate*(1-rate)/repetitions+z*z/(4*repetitions**2))/den
summary=dict(analyses=len(rows),failed=sum(not r['ok'] for r in rows),permutations_requested=5000,
    null_experiment=dict(seed=901,families=repetitions,variables_per_family=3,rejections=int(null_rejects),
        rate=rate,wilson95=[mid-half,mid+half],scope='Independent smooth Gaussian fields only'),
    seconds=round(time.time()-started,2))
pd.DataFrame(rows).to_csv(OUT/'dataset-test-matrix.csv',index=False)
(OUT/'matrix-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
assert not summary['failed'], 'See dataset-test-matrix.csv'
