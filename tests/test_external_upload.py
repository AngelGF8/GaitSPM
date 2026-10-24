"""Real HTTP upload-to-export test using independent public kinematic CSV values."""
import base64
import hashlib
import io
import json
import sys
import threading
import unittest
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from test_audit import E,ROOT,config
import serve

FIX=ROOT/'tests/fixtures/movementrx'
OUT=ROOT/'audit-v1.4.1'

class ExternalUploadTests(unittest.TestCase):
    def test_identity_fields_survive_import(self):
        for separator,decimal in [(',', '.'),(';', ',')]:
            records=[separator.join(['subject','group','KneeSagittal_0'])]
            for sid,grp,value in [('001','A','1.25'),('1','B','2.50'),('NA','A','3.75')]:
                records.append(separator.join([sid,grp,value.replace('.',decimal)]))
            df,_=E.read_upload(('\n'.join(records)+'\n').encode(),'external_ids.csv')
            self.assertEqual(df.subject.tolist(),['001','1','NA'])
            np.testing.assert_allclose(E._to_numeric(df.KneeSagittal_0),[1.25,2.5,3.75])
        bad=b'subject,KneeSagittal_0, KneeSagittal_0\nS1,1,2\n'
        with self.assertRaisesRegex(ValueError,'duplicate column'):E.read_upload(bad,'duplicates.csv')

    def test_transposed_duplicate_or_missing_identity_tokens_rejected(self):
        df=pd.DataFrame({'node':range(101),'S1_KneeSagittal':np.arange(101)})
        with self.assertRaisesRegex(ValueError,'duplicate token'):
            E.canon_from_transposed(df,'node','_',{0:'subject',1:'subject'})
        with self.assertRaisesRegex(ValueError,'missing identity'):
            E.canon_from_transposed(df,'node','_',{0:'variable',2:'subject'})

    def test_external_csv_real_http_roundtrip(self):
        raw=(FIX/'original/L_KneeX_Ang_Ref.csv').read_bytes()
        self.assertEqual(hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest(),'b971c393d1fa5219e49ba7755ce784189e36c4f8')
        original=pd.read_csv(io.BytesIO(raw)).to_numpy(float)
        adapted=(FIX/'movementrx_import_test.csv').read_bytes()
        np.testing.assert_array_equal(original,pd.read_csv(io.BytesIO(adapted)).iloc[:,4:].to_numpy(float))
        server=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        token='ExternalAuditMovementRx'
        sequence=[]
        def post(route,data):
            req=urllib.request.Request(base+route,data,headers={'X-GaitSPM-Session':token,'Origin':base})
            with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
        def call(name,*args,ok=True):
            r=post('/api/call',json.dumps({'name':name,'args':args}).encode())
            sequence.append({'operation':name,'ok':r['ok']})
            self.assertEqual(r['ok'],ok,r)
            return r
        try:
            self.assertTrue(post('/api/upload',raw)['ok'])
            raw_parse=call('js_parse_upload','L_KneeX_Ang_Ref.csv','')
            self.assertEqual(raw_parse['nrows'],20)
            raw_rejection=call('js_apply_wide',json.dumps({}),ok=False)
            self.assertIn('subject ID',raw_rejection['error'])
            self.assertTrue(post('/api/upload',adapted)['ok'])
            parsed=call('js_parse_upload','movementrx_import_test.csv','')
            self.assertEqual(parsed['structure'],'wide')
            mapped=call('js_apply_wide',json.dumps({x:x for x in ['subject','group','condition','side']}))
            self.assertEqual(mapped['n_subj'],20)
            self.assertEqual(mapped['group_counts'],{'TestA':10,'TestB':10})
            self.assertEqual(mapped['quality']['complete_curves'],20)
            self.assertIsNone(mapped['example'])
            ns=serve.get_session(token)
            cfg=config(ns['STATE']['canon'],vars=['KneeSagittal'],equal_var=False,side_mode='L',groups=['TestA','TestB'],cond='REFERENCE')
            call('js_run_init',json.dumps(cfg))
            run=call('js_run_var','KneeSagittal');self.assertTrue(run['okv'],run)
            done=call('js_run_done');self.assertFalse(done['errors'])
            expl=call('js_explain');summary=expl['summaries'][0]
            self.assertEqual([s['n'] for s in summary['samples']],[10,10])
            computed=ns['STATE']['results']['KneeSagittal']
            expected=stats.ttest_ind(original[::2],original[1::2],axis=0,equal_var=False).statistic
            np.testing.assert_allclose(computed['z'],expected,rtol=1e-11,atol=1e-11)
            OUT.mkdir(exist_ok=True)
            formats={}
            for name in ('js_table_csv','js_table_xlsx'):
                r=call(name);blob=base64.b64decode(r['b64']);self.assertGreater(len(blob),100)
                formats[name]=len(blob)
                if name=='js_table_xlsx':self.assertTrue(blob.startswith(b'PK'))
            for fmt in ('png','svg','pdf'):
                r=call('js_export_detail','KneeSagittal',fmt,150);blob=base64.b64decode(r['b64'])
                self.assertGreater(len(blob),100)
                formats[fmt]=len(blob)
                if fmt=='png':self.assertTrue(blob.startswith(b'\x89PNG'));(OUT/'external-result.png').write_bytes(blob)
                if fmt=='pdf':self.assertTrue(blob.startswith(b'%PDF'))
                if fmt=='svg':self.assertIn(b'<svg',blob)
            call('js_set_language','en');done_en=call('js_run_done');self.assertIn('Joint',done_en['table']['columns'])
            # Invalid rerun must not relabel the previous statistical result.
            badcfg={**cfg,'alpha':0};call('js_run_init',json.dumps(badcfg),ok=False)
            self.assertNotIn('results',ns['STATE']);self.assertNotIn('cfg',ns['STATE'])
            # Failed new upload must not leave the preceding dataframe available.
            post('/api/upload',b'not_a_csv');call('js_parse_upload','invalid.csv','',ok=False)
            self.assertNotIn('updf',ns['STATE']);self.assertNotIn('canon',ns['STATE'])
            call('js_apply_wide',json.dumps({'subject':'subject'}),ok=False)
            evidence={'source':json.loads((FIX/'provenance.json').read_text()),
              'transport':'Actual loopback HTTP upload and API calls; no mocked backend',
              'native_original':'Rejected for missing participant ID; not directly compatible',
              'adapted_csv':'Accepted after explicit header and metadata adaptation; curve values unchanged',
              'participants':mapped['n_subj'],'group_counts':mapped['group_counts'],
              'quality':mapped['quality'],'max_abs_t_error_vs_scipy':float(abs(computed['z']-expected).max()),
              'summary':summary,'exports_bytes':formats,'operations':sequence,
              'clinical_claim':False,'browser_rendering_tested':False}
            (OUT/'external-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
            print('External CSV: original identity omission rejected; adapted 20×101 accepted; Welch matches SciPy; exports and state invalidation passed.')
        finally:
            server.shutdown();server.server_close();thread.join()
            if token in serve.SESSIONS:serve.SESSIONS.pop(token)['tmp'].cleanup()

if __name__=='__main__':unittest.main(verbosity=2)
