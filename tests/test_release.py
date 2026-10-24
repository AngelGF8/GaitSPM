"""v1.4 regression tests for data loss, identity, pairing and real teaching outputs."""
import io,json,sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from test_audit import E,ROOT,config
from simulation import synthetic_catalog,synthetic_dataset,example_recipe

def bridge():
    ns=dict(E.__dict__)
    exec((ROOT/'app/simulation.py').read_text(encoding="utf-8"),ns)
    exec((ROOT/'app/bridge.py').read_text(encoding="utf-8"),ns)
    return ns

class ReleaseTests(unittest.TestCase):
    def test_spanish_decimal_and_quoted_delimiters(self):
        text='subject;group;HipFlexion_0;HipFlexion_1\n"A,1";Case;1,25;2,25\n"B,1";Control;3,25;4,25\n'
        df,info=E.read_upload(text.encode(),'es.csv')
        self.assertEqual(info['sep'],';');self.assertEqual(df.iloc[0,0],'A,1')
        self.assertAlmostEqual(E._to_numeric(df.HipFlexion_0).iloc[0],1.25)
        text='node,A|Case|BASE|L|HipFlexion,B|Control|BASE|L|HipFlexion\n0,1.2,3.4\n1,2.3,4.5\n'
        self.assertEqual(E.sniff_csv(text),(',','.'))

    def test_duplicate_mapping_and_side_conflict(self):
        with self.assertRaisesRegex(ValueError,'roles'):
            E.validate_subject_column(pd.DataFrame({'id':['x']}),{'subject':'id','group':'id'})
        c=pd.DataFrame({'variable':['LHipFlexion'],'side':['Right']})
        with self.assertRaisesRegex(ValueError,'conflicting'):
            E.merge_side_tokens(c)

    def test_complementary_side_gaps_do_not_make_a_patient(self):
        records=[]
        for side in ['L','R']:
            for i in range(101):
                if (side=='L' and i<20) or (side=='R' and i>80):continue
                records.append(dict(subject='S',group='A',condition='B',side=side,variable='HipFlexion',node=i,value=float(i)))
        ids,Y,drop=E._subject_curves(pd.DataFrame(records),'HipFlexion',cond='B')
        self.assertEqual(ids,[]);self.assertIn('S',drop)

    def test_trials_cannot_fill_each_others_missing_edges(self):
        rows=[]
        for trial in ['T1','T2']:
            for i in range(101):
                if (trial=='T1' and i<20) or (trial=='T2' and i>80):continue
                rows.append(dict(subject='S',group='A',condition='B',side='L',variable='HipFlexion',trial=trial,node=i,value=float(i)))
        df=pd.DataFrame(rows);c,_,_=E.canon_from_long(df,{k:k for k in df.columns})
        self.assertEqual(E.canonical_quality(c)['complete_curves'],0)

    def test_covariate_not_silently_averaged_across_sides(self):
        c,m,_,vm=synthetic_dataset('06_acl');right=m.copy();right['side']='R';right['technical_score']+=10
        with self.assertRaisesRegex(ValueError,'varies within'):
            E.prepare_regress(c,pd.concat([m,right]),vm.variable.iloc[0],'technical_score','BASE',None,'mean')

    def test_repeated_statistics_match_independent_calculation(self):
        for key in ['07_ms_fatigue','08_acl_retest']:
            c,m,_,vm=synthetic_dataset(key);cfg=config(c,**example_recipe(key))
            rs,_=E.run_analysis(c,m,vm,cfg)
            for var,r in rs.items():
                self.assertNotIn('error',r)
                ids,Ys=E.prepare_levels(c,var,'condition',cfg['cond_levels'],None,cfg['group_filter'],'L')
                self.assertEqual(len(ids),30);self.assertEqual(r['n_included'],30)
                if key=='08_acl_retest':
                    np.testing.assert_allclose(r['z'],stats.ttest_rel(Ys[0],Ys[1],axis=0).statistic,rtol=1e-9)
                    self.assertEqual(len(E.confirmed_clusters(r)),0)
                else:
                    Y=np.stack(Ys,axis=1);n,k,_=Y.shape
                    grand=Y.mean((0,1));ss=n*((Y.mean(0)-grand)**2).sum(0)
                    residual=Y-Y.mean(1)[:,None,:]-Y.mean(0)[None,:,:]+grand
                    F=(ss/(k-1))/((residual**2).sum((0,1))/((n-1)*(k-1)))
                    np.testing.assert_allclose(r['z'],F,rtol=1e-8)
                    self.assertTrue(E.confirmed_clusters(r))

    def test_example_import_recognition_and_edited_rejection(self):
        ns=bridge()
        key='03_hip_oa';df,info=E.read_upload((ROOT/f'datasets/synthetic/{key}/{key}.xlsx').read_bytes(),key+'.xlsx')
        self.assertEqual(info['hoja'],'Curves_Wide')
        roles={k:k for k in ['subject','group','condition','side']}
        c,m,cov=E.canon_from_wide(df,E.find_curve_blocks(df.columns),roles)
        ns['_store'](c,m,cov);self.assertEqual(ns['STATE']['example']['key'],key)
        c.loc[c.index[0],'value']+=1;ns['_store'](c,m,cov);self.assertIsNone(ns['STATE']['example'])

    def test_actual_interpretation_and_all_import_formats(self):
        ns=bridge();fixtures={};matrix=[]
        def call(name,*args):
            r=json.loads(ns[name](*args));self.assertTrue(r['ok'],r);return r
        for d in synthetic_catalog():
            key=d['key'];p=call('js_load_synthetic',key);self.assertEqual(p['n_subj'],60)
            c,m,_,vm=synthetic_dataset(key);cfg=config(c,**d['recipe'],vars=vm.variable.tolist())
            call('js_run_init',json.dumps(cfg))
            for var in cfg['vars']:call('js_run_var',var)
            done=call('js_run_done');self.assertFalse(done['errors'])
            explanation=call('js_explain');texts=call('js_texts')
            self.assertTrue(explanation['summaries'])
            for r in explanation['summaries']:
                self.assertTrue(all(x['n']==30 for x in r['samples']))
                matrix.append({'dataset':key,'variable':r['variable'],'design':cfg['design'],'n_included':r['n'],'clusters':len(r['clusters'])})
            en=call('js_set_language','en');done_en=call('js_run_done')
            fixtures[key]={'payload':p,'cfg':cfg,'done':done,'done_en':done_en,'explain':explanation,'texts':texts}
        out=ROOT/'audit-v1.4';out.mkdir(exist_ok=True)
        (out/'ui-fixtures.json').write_text(json.dumps({'catalog':synthetic_catalog(),'examples':fixtures}), encoding="utf-8")
        pd.DataFrame(matrix).to_csv(out/'example-results.csv',index=False)

if __name__=='__main__':unittest.main(verbosity=2)
