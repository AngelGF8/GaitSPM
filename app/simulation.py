"""Deterministic, literature-calibrated synthetic benchmarks, NOT patient data.

Each example has 60 unique people: 30 controls and 30 cases, one indexed limb,
one or more conditions and 101 nodes. The finite samples match selected scalar means
and sample SDs; this is moment matching, not an iid clinical sample. Waveform
shapes, phase timings and covariance are explicit simulation assumptions.
"""
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
from scipy.stats import norm

# metric, control mean/SD, case mean/SD; degrees throughout.
SYNTHETIC_SPECS = [
 dict(key='01_fai', title_es='FAI sintomático', title_en='Symptomatic FAI', group='FAIS', short='Hao · 2025',
      citation='Hao et al. (2025), Table 2, FAIS without BDDH', url='https://doi.org/10.1186/s12891-025-08727-4',
      population='Symptomatic FAIS without borderline dysplasia; published n=14/group.',
      anchors=[['HipFlexion','ROM',46.86,3.79,46.11,5.82],['HipAdduction','ROM',15.83,2.81,15.35,2.11],['HipRotation','ROM',16.23,4.99,20.99,8.77]]),
 dict(key='02_knee_oa', title_es='Artrosis de rodilla', title_en='Knee osteoarthritis', group='KOA', short='Huang · 2008',
      citation='Huang et al. (2008), Table 3, severe medial knee OA', url='https://doi.org/10.1016/j.medengphy.2008.02.006',
      population='Severe medial knee OA. Published phase values assigned to stated synthetic nodes; phases were not digitised.',
      anchors=[['HipFlexion','node_0',27.57,4.66,22.77,7.47],['KneeFlexion','node_12',17.26,9.01,9.78,6.44],['AnkleDorsiflexion','node_45',6.82,5.60,6.99,4.62]]),
 dict(key='03_hip_oa', title_es='Artrosis de cadera', title_en='Hip osteoarthritis', group='HOA', short='Bahr · 2021 · PreOP',
      citation='Bahr et al. (2021), Table 2, preoperative hip vs controls', url='https://doi.org/10.12659/MSM.934558',
      population='Unilateral hip osteoarthritis before THA, n=23; healthy controls n=39. Same source as THA, independently simulated IDs.',
      anchors=[['HipFlexion','ROM',43.61,4.78,25.27,9.93],['HipAdduction','ROM',10.89,2.02,5.43,2.83],['HipRotation','ROM',13.23,3.90,18.80,6.61]]),
 dict(key='05_hip_arthroplasty', title_es='Artroplastia de cadera', title_en='Hip arthroplasty', group='THA', short='Bahr · 2021 · PostOP',
      citation='Bahr et al. (2021), Table 2, postoperative hip vs controls', url='https://doi.org/10.12659/MSM.934558',
      population='Postoperative S-ROM total hip arthroplasty; n=23 cases, n=39 controls. Separate cross-sectional synthetic base, not a longitudinal pairing with base 03.',
      anchors=[['HipFlexion','ROM',43.61,4.78,33.14,8.55],['HipAdduction','ROM',10.89,2.02,7.15,2.80],['HipRotation','ROM',13.23,3.90,18.52,7.79]]),
 dict(key='06_acl', title_es='Reconstrucción LCA', title_en='ACL reconstruction', group='ACLR', short='Noehren · 2013',
      citation='Noehren et al. (2013), Table 2, walking (not running)', url='https://pmc.ncbi.nlm.nih.gov/articles/PMC4313379/',
      population='Females after ACL reconstruction, mean 5.2 years since surgery. Knee flexion sign reversed to flexion-positive; SD unchanged. Scalar loading-response values assigned to synthetic nodes.',
      anchors=[['HipFlexion','node_0',26.1,7.4,20.0,7.4],['KneeFlexion','node_12',20.1,5.1,18.5,5.0]]),
 dict(key='04_multiple_sclerosis', title_es='Esclerosis múltiple', title_en='Multiple sclerosis', group='MS', short='Lencioni · 2016',
      citation='Lencioni et al. (2016), Table 1, speed-matched controls', url='https://doi.org/10.3389/fnhum.2016.00620',
      population='Multiple sclerosis, published n=17 cases and n=12 speed-matched controls; EDSS 5.8 ± 0.8, slow gait. Selected neurological scenario.',
      anchors=[['HipFlexion','ROM',38,5,35,11],['KneeFlexion','ROM',56,5,46,15],['AnkleDorsiflexion','ROM',33,7,26,6]]),

]


EXTRA_SPECS = [
 dict(key='07_ms_fatigue', base='04_multiple_sclerosis', group='MS',
      title_es='Esclerosis múltiple · fatiga y recuperación', title_en='Multiple sclerosis · fatigue and recovery',
      short='Tres condiciones · RM-ANOVA', citation='GaitSPM educational simulation, 2026', url='',
      population='Simulación longitudinal: 30 MS y 30 controles, BASE/FATIGUE/RECOVERY. Los cambios son supuestos didácticos, no efectos clínicos publicados.'),
 dict(key='08_acl_retest', base='06_acl', group='ACLR',
      title_es='LCA · repetición sin cambio sistemático', title_en='ACL · repeat measurement without systematic change',
      short='Dos condiciones · t pareada', citation='GaitSPM educational simulation, 2026', url='',
      population='Simulación longitudinal: 30 ACLR y 30 controles, TEST/RETEST. Generador sin cambio sistemático; un resultado no significativo no prueba equivalencia.')
]


def example_recipe(key):
    spec = synthetic_spec(key)
    recipe = dict(design='ttest2', groups=['Control', spec['group']], cond='BASE',
                  cond_levels=None, group_filter=None, side_mode='L', mode='param',
                  equal_var=False, alpha=.05, two_tailed=True, field_correction='bonferroni')
    if key == '07_ms_fatigue':
        recipe.update(design='anova1rm', groups=None, cond=None,
                      cond_levels=['BASE','FATIGUE','RECOVERY'], group_filter='MS', equal_var=True)
    elif key == '08_acl_retest':
        recipe.update(design='paired_cond', groups=None, cond=None,
                      cond_levels=['TEST','RETEST'], group_filter='ACLR', equal_var=True)
    return recipe


def synthetic_catalog():
    items = SYNTHETIC_SPECS + EXTRA_SPECS
    return [{**{k:v for k,v in d.items() if k != 'anchors'},
             'n_vars':len(synthetic_spec(d['key'])['anchors']), 'n_total':60,'n_cases':30,'n_controls':30,
             'n_conditions':3 if d['key']=='07_ms_fatigue' else (2 if d['key']=='08_acl_retest' else 1),
             'recipe':example_recipe(d['key'])}
            for d in sorted(items,key=lambda x:x['key'])]


def synthetic_spec(key):
    extra=next((d for d in EXTRA_SPECS if d['key']==key),None)
    if extra:
        return {**extra, 'anchors':synthetic_spec(extra['base'])['anchors']}
    return next(d for d in SYNTHETIC_SPECS if d['key']==key)


def _moments(n, mean, sd, rng, positive=False):
    z=norm.ppf((np.arange(n)+.5)/n)
    if positive and mean + sd * (z.min()-z.mean())/z.std(ddof=1) <= 0:
        z=np.exp(z*np.sqrt(np.log1p((sd/mean)**2)))
    z=(z-z.mean())/z.std(ddof=1)
    return mean+sd*rng.permutation(z)


def synthetic_dataset(key, seed=260905):
    if key in {d['key'] for d in EXTRA_SPECS}:
        return repeated_dataset(key, seed)
    spec=synthetic_spec(key)
    rng=np.random.default_rng(int(seed)+int(key[:2])*1009)
    t=np.arange(101,dtype=float)
    knots=np.array([0,12,30,45,60,73,87,100])
    profiles={
      'HipFlexion':[28,21,3,-9,4,25,35,28],
      'HipAdduction':[1,6,7,2,-3,-6,-2,1],
      'HipRotation':[2,7,4,-1,-5,-6,-1,2],
      'KneeFlexion':[4,18,6,6,35,64,32,4],
      'AnkleDorsiflexion':[0,-5,4,10,-17,0,3,0],
    }
    records=[]; people=[]
    for gi,grp in enumerate(['Control',spec['group']]):
      ids=[f'{key[:2]}{"C" if gi==0 else "P"}{i+1:02d}' for i in range(30)]
      # Technical covariate; no implied clinical association.
      score=_moments(30,50,10,rng)
      for i,s in enumerate(ids):people.append(dict(subject=s,group=grp,condition='BASE',side='L',synthetic=True,technical_score=float(score[i])))
      for var,metric,cm,cs,pm,ps in spec['anchors']:
        anchors=_moments(30,cm if gi==0 else pm,cs if gi==0 else ps,rng,positive=metric=='ROM')
        base=PchipInterpolator(knots,profiles[var])(t)
        for i,s in enumerate(ids):
          noise=gaussian_filter1d(rng.normal(0,1,101),4,mode='wrap')
          noise-=noise.mean();noise/=max(noise.std(),1e-9)
          y=base+noise*.7
          if metric=='ROM':
            y=(y-y.min())/np.ptp(y)*anchors[i]
            # Offsets are assumptions, not recovered patient hip orientation.
            baseline={'HipFlexion':-8,'HipAdduction':-6,'HipRotation':-7,'KneeFlexion':3,'AnkleDorsiflexion':-16}[var]
            y=y+baseline+rng.normal(0,1.4)
          else:
            node=int(metric.split('_')[1]);y=y+(anchors[i]-y[node])
          records.append(pd.DataFrame(dict(subject=s,group=grp,condition='BASE',side='L',variable=var,node=np.arange(101),value=y)))
    canon=pd.concat(records,ignore_index=True)
    vm=pd.DataFrame([{'variable':a[0],'joint':'hip' if a[0].startswith('Hip') else ('knee' if a[0].startswith('Knee') else 'ankle'),'plane':'frontal' if 'Adduction' in a[0] else ('transverse' if 'Rotation' in a[0] else 'sagittal')} for a in spec['anchors']])
    return canon,pd.DataFrame(people),['technical_score'],vm


def repeated_dataset(key, seed=260905):
    spec=synthetic_spec(key)
    base, people, covs, vm=synthetic_dataset(spec['base'], int(seed)+int(key[:2])*1009)
    base['subject']=base.subject.str.replace(r'^\d{2}',key[:2],regex=True)
    people['subject']=people.subject.str.replace(r'^\d{2}',key[:2],regex=True)
    rng=np.random.default_rng(int(seed)+int(key[:2])*8009)
    levels=['BASE','FATIGUE','RECOVERY'] if key=='07_ms_fatigue' else ['TEST','RETEST']
    records=[]; metadata=[]
    for condition in levels:
        p=people.copy();p['condition']=condition;metadata.append(p)
    for (_,_,var), curve in base.groupby(['subject','group','variable'],sort=False):
        # Shared subject baseline plus independent condition noise: no pseudo-replication.
        y0=curve.value.to_numpy();t=curve.node.to_numpy()
        for j,condition in enumerate(levels):
            noise=gaussian_filter1d(rng.normal(size=101),4,mode='wrap')
            noise=noise/max(noise.std(),1e-9)*1.1+rng.normal(0,.5)
            delta=np.zeros(101)
            if key=='07_ms_fatigue' and j:
                amplitude={'HipFlexion':-3.0,'KneeFlexion':-7.0,'AnkleDorsiflexion':-3.5}[var]
                amplitude*=1 if str(curve.group.iloc[0])=='MS' else .15
                delta=amplitude*np.exp(-.5*((t-70)/12)**2)*(1 if j==1 else .15)
            row=curve.copy();row['condition']=condition;row['value']=y0+noise+delta;records.append(row)
    return pd.concat(records,ignore_index=True),pd.concat(metadata,ignore_index=True),covs,vm
