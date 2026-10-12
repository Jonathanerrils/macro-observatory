import unittest
import numpy as np
import pandas as pd
from macro.research import block_bootstrap, breakdown, chronological_holdout, report_bundle
import zipfile,io,json

class ResearchTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(321); x=rng.normal(size=400)
        self.frame=pd.DataFrame({'x':x,'y':pd.Series(x).shift(3)+rng.normal(0,.05,400)},index=None)
    def test_bootstrap_reproducible(self):
        pair=self.frame[['x','y']]
        a,d1=block_bootstrap(pair,reps=100)
        b,d2=block_bootstrap(pair,reps=100)
        np.testing.assert_equal(d1,d2); self.assertEqual(a,b)
    def test_perfect_dependence_interval(self):
        x=np.arange(100,dtype=float)
        r,_=block_bootstrap(np.column_stack([x,2*x]),reps=100)
        self.assertAlmostEqual(r['lower'],1); self.assertAlmostEqual(r['upper'],1)
    def test_missing_rows_preserved(self):
        pair=self.frame.copy(); pair.iloc[30:50]=np.nan
        r,_=block_bootstrap(pair,reps=100)
        self.assertEqual(r['periods'],400); self.assertEqual(r['overlap'],377)
    def test_constant_rejected(self):
        with self.assertRaises(ValueError): block_bootstrap(np.ones((100,2)),reps=100)
    def test_block_too_large_rejected(self):
        with self.assertRaises(ValueError): block_bootstrap(self.frame.iloc[:30],block=11,reps=100)
    def test_known_training_lag_and_holdout_skill(self):
        result,_,_=chronological_holdout(self.frame,'x','y',max_lag=6)
        self.assertEqual(result['selected_lag'],3)
        self.assertGreater(result['skill_vs_training_mean'],.95)
    def test_holdout_cannot_change_training_selection_or_fit(self):
        original,_,_=chronological_holdout(self.frame,'x','y',max_lag=6)
        modified=self.frame.copy(); modified.iloc[280:,1]=np.arange(120)*100
        altered,_,_=chronological_holdout(modified,'x','y',max_lag=6)
        for key in ['selected_lag','intercept','slope','train_correlation']:
            self.assertEqual(original[key],altered[key])
        self.assertEqual(original['test_start'],'286')
    def test_breakdown_detects_constructed_flip(self):
        rng=np.random.default_rng(8); x=rng.normal(size=200)
        y=np.concatenate([x[:100],-x[100:]])
        result=breakdown(pd.DataFrame({'x':x,'y':y}),window=100,reps=100)
        self.assertLess(result['delta_upper'],-1.9)
    def test_report_contains_reproducible_panel(self):
        blob=report_bundle(self.frame,{'source':'synthetic'},{},{'table':self.frame.head()})
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            self.assertIn('report.html',z.namelist())
            self.assertIn('panel_sha256',json.loads(z.read('manifest.json')))
    def test_spearman_bootstrap(self):
        x=np.arange(100)
        r,_=block_bootstrap(np.column_stack([x,x**3]),method='spearman',reps=100)
        self.assertAlmostEqual(r['correlation'],1)

if __name__=='__main__': unittest.main()
