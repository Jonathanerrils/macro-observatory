import unittest
import numpy as np
import pandas as pd
from macro.engine import validate, transform, correlations, rolling_pair, lead_lag, demo

class EngineTests(unittest.TestCase):
    def test_missing_period_is_not_zero_return(self):
        x=pd.DataFrame({'x':[100,np.nan,121,133.1]},index=pd.bdate_range('2024-01-01',periods=4))
        y=transform(x,'B',{'x':'return'})
        self.assertTrue(y.x.iloc[:3].isna().all())
        self.assertAlmostEqual(y.x.iloc[3],10)
    def test_pair_counts_and_gate(self):
        x=pd.DataFrame({'a':[1,2,3,np.nan],'b':[2,4,np.nan,8]})
        r,n=correlations(x,minimum=3)
        self.assertEqual(n.loc['a','b'],2)
        self.assertTrue(np.isnan(r.loc['a','b']))
    def test_positive_lag_means_driver_leads(self):
        rng=np.random.default_rng(7); a=rng.normal(size=200)
        x=pd.DataFrame({'a':a,'b':pd.Series(a).shift(2)})
        result=lead_lag(x,'a','b',5).set_index('lag')
        self.assertAlmostEqual(result.loc[2,'correlation'],1)
    def test_duplicate_dates_rejected(self):
        with self.assertRaises(ValueError):
            validate(pd.DataFrame({'x':[1,2]},index=['2024-01-01']*2))
    def test_rolling_missing_is_not_bridged(self):
        x=pd.DataFrame({'a':[1,2,np.nan,4,5,6],'b':[2,4,6,8,10,12]})
        y=rolling_pair(x,'a','b',3)
        self.assertTrue(np.isnan(y.iloc[4])); self.assertAlmostEqual(y.iloc[5],1)
    def test_negative_price_log_is_missing(self):
        x=pd.DataFrame({'x':[10,-1,12]},index=pd.bdate_range('2024-01-01',periods=3))
        self.assertTrue(transform(x,'B',{'x':'log return'}).isna().all().all())
    def test_spearman_monotonic(self):
        x=pd.DataFrame({'a':range(30),'b':np.arange(30)**3})
        r,_=correlations(x,'spearman',20)
        self.assertAlmostEqual(r.loc['a','b'],1)
    def test_demo_and_monthly_pipeline(self):
        x=validate(demo()); y=transform(x,'ME',{'DEXUSEU':'return'})
        r,n=correlations(y,minimum=10)
        self.assertGreater(n.loc['DEXUSEU','DGS2'],10)
        self.assertEqual(r.shape,(13,13))

if __name__=='__main__': unittest.main()
