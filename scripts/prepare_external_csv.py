"""Adapt an unmodified public MovementRx reference CSV for an import smoke test.

No curve values are simulated, resampled, reordered or changed. Labels TestA/TestB
are an arbitrary alternating split for SOFTWARE TESTING ONLY, not clinical groups.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'tests/fixtures/movementrx'
ORIGINAL=DIRECTORY/'original/L_KneeX_Ang_Ref.csv'
EXPECTED_BLOB='b971c393d1fa5219e49ba7755ce784189e36c4f8'

def main():
    raw=ORIGINAL.read_bytes()
    assert hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()==EXPECTED_BLOB
    curves=pd.read_csv(ORIGINAL).to_numpy(float)
    assert curves.shape==(20,101) and np.isfinite(curves).all()
    frame=pd.DataFrame(curves,columns=[f'KneeSagittal_{i}' for i in range(101)])
    meta=pd.DataFrame({'subject':[f'MRX{i+1:02d}' for i in range(20)],
        'group':['TestA' if i%2==0 else 'TestB' for i in range(20)],
        'condition':'REFERENCE','side':'L'})
    out=DIRECTORY/'movementrx_import_test.csv'
    pd.concat([meta,frame],axis=1).to_csv(out,index=False,float_format='%.15g')
    reloaded=pd.read_csv(out).iloc[:,4:].to_numpy(float)
    np.testing.assert_allclose(curves,reloaded,rtol=0,atol=1e-12)
    info={'source_repository':'https://github.com/aalhossary/MovementRx',
      'commit':'70f97b52b55e476fa52f9e733a98cefe55532c18',
      'source_path':'spmclient/res/refData/kinematic/L_KneeX_Ang_Ref.csv',
      'source_git_blob':EXPECTED_BLOB,'original_sha256':hashlib.sha256(raw).hexdigest(),
      'adapted_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
      'article':'https://doi.org/10.1038/s41598-023-29635-4',
      'attribution':'Alhossary A, Pataky T, Ang WT, Chua KSG, Kwong WH, Donnelly CJ. MovementRx (2023).',
      'upstream_license':'GNU GPL v3, LICENSE retained',
      'participants':20,'nodes':101,'variable':'KneeSagittal','units':'degrees',
      'adaptation':'Original 101 measurement columns renamed to KneeSagittal_0..100; added row IDs, side L, REFERENCE condition and arbitrary alternating TestA/TestB labels. No alteration of curve values or signs. Original knee sign convention retained.',
      'interpretation_limit':'TestA/TestB are artificial test labels within the same reference cohort, not diagnoses or interventions. Statistical outputs serve only to test software; they are not clinical findings.'}
    (DIRECTORY/'provenance.json').write_text(json.dumps(info,indent=2)+'\n', encoding="utf-8")
    print(json.dumps({'path':str(out),'participants':20,'groups':{'TestA':10,'TestB':10},'max_value_change':float(abs(curves-reloaded).max())}))

if __name__=='__main__':main()
