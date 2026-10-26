"""Deterministic harness checks, not a Monte Carlo acceptance test."""
from pathlib import Path
import sys
import tempfile
import unittest
import warnings
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/monte_carlo'))
import monte_carlo as M


class MonteCarloTests(unittest.TestCase):
    def test_inventory_and_null_masks(self):
        cases=M.scenarios()
        self.assertEqual(len(cases),38)
        self.assertEqual(len({c['id'] for c in cases}),38)
        self.assertEqual(sum(c['category']=='assumption_violation' for c in cases),5)
        for case in cases:
            models,meta,cfg,mask=M.generate(case,0)
            expected=case['fields']*(3 if case['design'].startswith('anova2') else 1)
            self.assertEqual(int(mask.sum()),expected-(case['null']=='partial'))
            self.assertEqual(len(models),case['fields'])
            self.assertTrue(all(np.isfinite(x['Y']).all() for x in models))

    def test_all_scenarios_full_pipeline_parity(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            for case in M.scenarios():
                with self.subTest(scenario=case['id']):
                    models,meta,cfg,mask=M.generate(case,1)
                    _,_,details=M.evaluate(models,cfg)
                    M.verify_end_to_end(models,meta,cfg,details)

    def test_streams_and_partial_null_means(self):
        for design in M.E.ADVANCED_DESIGNS:
            case=next(x for x in M.scenarios() if x['id']==design+'_partial_null')
            models,meta,cfg,_=M.generate(case,7)
            again=M.generate(case,7)[0];other=M.generate(case,8)[0]
            np.testing.assert_array_equal(models[0]['Y'],again[0]['Y'])
            self.assertFalse(np.array_equal(models[0]['Y'],other[0]['Y']))
            null=M.generate({**case,'null':'global'},7)[0]
            bump=np.exp(-.5*((np.arange(M.Q)-50)/15)**2)
            factor=meta.speed.to_numpy() if design=='glm' else meta.A.to_numpy()
            np.testing.assert_allclose(models[0]['Y']-null[0]['Y'],1.5*factor[:,None]*bump,atol=1e-14)
            np.testing.assert_array_equal(models[1]['Y'],null[1]['Y'])

    def test_generator_variance_smoothness_and_covariance(self):
        rng=np.random.default_rng(44)
        for fwhm in (5.,10.,20.):
            noise=M.smooth_noise(rng,(10000,),fwhm)
            np.testing.assert_allclose(noise.var(axis=0)[[0,50,100]],1.,atol=.05)
            sigma=fwhm/np.sqrt(8*np.log(2))
            correlation=np.corrcoef(noise[:,45],noise[:,50])[0,1]
            self.assertAlmostEqual(correlation,np.exp(-25/(4*sigma*sigma)),delta=.035)
            self.assertLess(abs(np.corrcoef(noise[:,0],noise[:,-1])[0,1]),.04)
        case=next(x for x in M.scenarios() if x['id']=='anova2onerm_family_correlated')
        models,meta,_,_=M.generate({**case,'n':[2000,2000]},0)
        a=models[0]['Y'][:,50];b=models[1]['Y'][:,50]
        self.assertAlmostEqual(np.corrcoef(a,b)[0,1],.8,delta=.03)
        cells=[a[(meta.A==0)&(meta.B==i)] for i in range(3)]
        for i in (1,2):self.assertAlmostEqual(np.corrcoef(cells[0],cells[i])[0,1],.5,delta=.05)

    def test_intervals_and_atomic_chunk_resume_data(self):
        lo,hi=M.interval(250,5000)
        self.assertLess(lo,.05);self.assertGreater(hi,.05)
        self.assertEqual(M.interval(0,5000)[0],0.)
        self.assertEqual(M.interval(5000,5000)[1],1.)
        case=M.scenarios()[0]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'chunk.npz'
            M.chunk_job(case,0,2,M.SEED,path)
            with np.load(path,allow_pickle=False) as z:
                self.assertEqual(z['crossed'].shape,(2,1,1))
                self.assertEqual(int(z['stop']),2)
                self.assertEqual(z['confirmed'].dtype,np.dtype(bool))
            self.assertFalse(Path(str(path)+'.tmp').exists())


if __name__=='__main__':unittest.main(verbosity=2)
