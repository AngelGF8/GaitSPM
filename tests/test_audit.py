"""Independent numerical, parser, regression and export checks. No clinical validation."""
import io
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd
from scipy import stats
from scipy.ndimage import gaussian_filter1d

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'app'))
import gaitspm_engine as E
from simulation import synthetic_catalog, synthetic_dataset


def config(canon, **kwargs):
    cfg = dict(design='ttest2', alpha=.05, two_tailed=True, mode='param', iterations=5000,
        seed=2026, field_correction='bonferroni', equal_var=True, side_mode='mean',
        posthoc=True, band_group=None, band_k=1, lang='es', groups=list(canon.group.unique()),
        cond=str(canon.condition.iloc[0]), cond_levels=None, side_levels=['L','R'],
        group_filter=None, covariate='technical_score')
    cfg.update(kwargs)
    return cfg


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c, cls.meta, cls.covs, cls.vm = synthetic_dataset('03_hip_oa')

    def test_01_six_bases_moments(self):
        all_ids = set()
        for item in synthetic_catalog():
            key = item['key']; c,m,_,vm = synthetic_dataset(key)
            self.assertEqual(c.subject.nunique(),60)
            self.assertEqual(m.groupby('group').subject.nunique().tolist(),[30,30])
            self.assertFalse(set(m.subject)&all_ids); all_ids.update(m.subject)
            self.assertEqual(E.canonical_quality(c)['completeness_pct'],100.)
            if int(key[:2]) > 6: continue
            cal = pd.read_csv(ROOT/'datasets/synthetic'/key/'calibration.csv')
            np.testing.assert_allclose(cal.target_mean,cal.simulated_mean,atol=1e-7)
            np.testing.assert_allclose(cal.target_sd,cal.simulated_sd,atol=1e-7)
        self.assertEqual(len(all_ids),sum(d['n_total'] for d in synthetic_catalog()))

    def test_02_all_parsers(self):
        roles={x:x for x in ['subject','group','condition','side']}
        def ordered(c):
            return c.astype({'subject':str,'group':str,'condition':str,'side':str,'variable':str}).sort_values(E.CANON_COLS[:-1]).reset_index(drop=True)
        for item in synthetic_catalog():
            folder=ROOT/'datasets/synthetic'/item['key']; expected=ordered(synthetic_dataset(item['key'])[0])
            names = [item['key']+'.csv', item['key']+'.xlsx'] if item.get('source_kind') == 'bundled_csv' else ['curves_wide.csv','curves_wide_es.csv',item['key']+'.xlsx']
            for name in names:
                df,_=E.read_upload((folder/name).read_bytes(),name)
                got=E.canon_from_wide(df,E.find_curve_blocks(df.columns),roles)[0]
                np.testing.assert_allclose(ordered(got).value,expected.value,atol=1e-7)
            if item.get('source_kind') == 'bundled_csv': continue
            df=pd.read_csv(folder/'curves_long.csv')
            got=E.canon_from_long(df,{**roles,'variable':'variable','node':'node','value':'value'})[0]
            np.testing.assert_allclose(ordered(got).value,expected.value,atol=1e-7)
            df=pd.read_csv(folder/'curves_transposed.csv')
            got=E.canon_from_transposed(df,df.columns[0],'|',dict(enumerate(['subject','group','condition','side','variable'])))[0]
            np.testing.assert_allclose(ordered(got).value,expected.value,atol=1e-7)

    def test_03_t_statistics_and_threshold(self):
        for equal in [True,False]:
            cfg=config(self.c,equal_var=equal)
            rs,_=E.run_analysis(self.c,self.meta,self.vm,cfg)
            for var,r in rs.items():
                self.assertNotIn('error',r)
                gs,_=E.prepare_between(self.c,var,cfg['groups'],cfg['cond'],'mean')
                a,b=[x['Y'] for x in gs]
                np.testing.assert_allclose(r['z'],stats.ttest_ind(a,b,axis=0,equal_var=equal).statistic,rtol=1e-9)
                ref=E.spm1d.stats.ttest2(a,b,equal_var=equal).inference(.05/3,two_tailed=True)
                self.assertAlmostEqual(r['zstar'],ref.zstar,10)

    def test_04_cluster_and_failed_family_regression(self):
        r={'alpha':.025,'family_alpha':.05,'clusters':[{'p':.001},{'p':.2}]}
        rs={'ok':r,'failed':{'error':'fixture'}}
        E.apply_field_correction(rs,{'alpha':.05,'field_correction':'bonferroni','field_count':2})
        self.assertEqual([c['p'] for c in E.confirmed_clusters(r)],[.001])
        self.assertEqual([c['p_field_adj'] for c in r['clusters']],[.002,.4])
        E.apply_field_correction(rs,{'alpha':.05,'field_correction':'bonferroni','field_count':2})
        self.assertEqual(r['clusters'][1]['p_field_adj'],.4)
        with self.assertRaises(ValueError):E.apply_field_correction(rs,{'alpha':.05,'field_correction':'holm'})

    def test_05_missing_edges_and_duplicates(self):
        y=E.resample1(np.arange(10,91),np.arange(10,91))
        self.assertTrue(np.isnan(y[:10]).all() and np.isnan(y[91:]).all())
        a=np.arange(101,dtype=float);a[0]=np.nan;a[40:60]=np.nan
        got=E.resample_rows(np.arange(101),a[None,:])[0]
        self.assertTrue(np.isnan(got[0]) and np.isnan(got[40:60]).all())
        with self.assertRaises(ValueError):E.resample1([0]*10,[1]*10)
        with self.assertRaises(ValueError):E.validate_subject_column(pd.DataFrame({'subject':['a',None]}),{'subject':'subject'})

    def test_06_validation_and_covariate(self):
        c=self.c.copy();c['subject']=c.subject.astype(str);ids=c.subject.unique();c.loc[c.subject==ids[30],'subject']=ids[0]
        with self.assertRaises(ValueError):E.run_analysis(c,self.meta,self.vm,config(c))
        with self.assertRaises(ValueError):E.run_analysis(self.c,self.meta,pd.concat([self.vm,self.vm.iloc[:1]]),config(self.c))
        meta=self.meta.copy();meta['technical_score']=1.
        rs,_=E.run_analysis(self.c,meta,self.vm,config(self.c,design='regress'))
        self.assertTrue(all('constant covariate' in r['error'] for r in rs.values()))

    def test_07_snpm_rng_and_resolution(self):
        cfg=config(self.c,mode='nonparam',iterations=500,field_count=1)
        np.random.seed(83);state=np.random.get_state()
        a=E.run_one(self.c,self.meta,self.vm.iloc[0],cfg)
        after=np.random.get_state();np.testing.assert_array_equal(state[1],after[1]);self.assertEqual(state[2:],after[2:])
        b=E.run_one(self.c,self.meta,self.vm.iloc[0],cfg)
        self.assertEqual(a['zstar'],b['zstar']);self.assertEqual(a['clusters'],b['clusters'])
        self.assertEqual(a['iterations_actual'],500)
        Y=np.random.default_rng(7).normal(size=(3,101))
        with self.assertRaises(ValueError):E._np_infer(E.spm1d.stats.nonparam.ttest(Y),.05,iterations=5000)

    def test_08_rm_effect_independent_formula(self):
        rng=np.random.default_rng(81);Y=rng.normal(size=(12,3,101));Y+=rng.normal(size=(12,1,101))*3
        gs=[Y[:,i] for i in range(3)];got=E.eta2p_rm_curve(gs)
        grand=Y.mean((0,1));cond=Y.mean(0);sub=Y.mean(1)
        sscond=12*((cond-grand)**2).sum(0)
        sse=((Y-sub[:,None,:]-cond[None,:,:]+grand)**2).sum((0,1))
        np.testing.assert_allclose(got,sscond/(sscond+sse),rtol=1e-10)

    def test_09_exports_and_style_no_reinference(self):
        cfg=config(self.c);rs,bands=E.run_analysis(self.c,self.meta,self.vm,cfg);r=next(iter(rs.values()));before=r['z'].copy()
        for lang in ['es','en']:
            table=E.results_table(rs,lang)
            self.assertIn('Joint' if lang=='en' else 'Articulación',table.columns)
            self.assertIn('Bonferroni',E.methods_text(cfg,rs,lang));self.assertTrue(E.results_text(rs,cfg,lang))
            table.to_csv(index=False);buf=io.BytesIO();table.to_excel(buf,index=False,engine='openpyxl');self.assertGreater(len(buf.getvalue()),4000)
            for mode in ['sd','ci95']:
                style={**cfg,'interval_mode':mode,'band_colors':['#008866'],'show_interval_edges':True,'show_cluster_bars':True}
                f=E.fig_detail(r,None,lang,style)
                for fmt in ['png','svg','pdf']:self.assertGreater(len(E.fig_to_bytes(f,fmt,100)),1000)
                E.plt.close(f)
        np.testing.assert_array_equal(before,r['z'])
        self.assertTrue(np.isfinite(E.plot_style({'interval_alpha':float('nan')})['interval_alpha']))

    def test_10_html_engine_identity(self):
        import re
        html=(ROOT/'app/gaitspm.html').read_text(encoding="utf-8")
        embedded=re.search(r'<script[^>]*id="py-engine"[^>]*>(.*?)</script>',html,re.S).group(1)
        self.assertEqual(embedded.strip(),(ROOT/'app/gaitspm_engine.py').read_text(encoding="utf-8").strip())


if __name__=='__main__':unittest.main(verbosity=2)
