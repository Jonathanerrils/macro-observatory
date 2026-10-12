"""Research calculations: no imputation, no causal interpretation."""
import numpy as np
import pandas as pd

CATALOG = {
 'DEXUSEU': ('EUR/USD', 'FX', 'return'),
 'DEXJPUS': ('USD/JPY', 'FX', 'return'),
 'DEXUSUK': ('GBP/USD', 'FX', 'return'),
 'DTWEXBGS': ('Broad US dollar', 'FX', 'return'),
 'DGS2': ('US 2Y yield', 'Rates', 'difference'),
 'DGS10': ('US 10Y yield', 'Rates', 'difference'),
 'VIXCLS': ('VIX', 'Risk', 'difference'),
 'SP500': ('S&P 500', 'Equities', 'return'),
 'DCOILWTICO': ('WTI oil', 'Commodities', 'difference'),
 'DCOILBRENTEU': ('Brent oil', 'Commodities', 'difference'),
 'CPIAUCSL': ('US CPI', 'Macro', 'return'),
 'UNRATE': ('US unemployment', 'Macro', 'difference'),
 'FEDFUNDS': ('Fed funds rate', 'Macro', 'difference'),
}

def validate(frame):
    frame = frame.copy()
    frame.index = pd.to_datetime(frame.index, errors='raise')
    if frame.index.hasnans or frame.index.duplicated().any():
        raise ValueError('Dates must be valid and unique.')
    if frame.columns.duplicated().any() or frame.empty:
        raise ValueError('Provide a nonempty panel with unique series names.')
    frame = frame.sort_index().apply(pd.to_numeric, errors='raise').astype(float)
    if np.isinf(frame.to_numpy()).any():
        raise ValueError('Infinite values are not supported.')
    if frame.notna().sum().min() < 2:
        raise ValueError('Each series needs at least two numeric observations.')
    return frame

def transform(frame, frequency, modes):
    # Resample before transforming. Empty bins stay missing; never pad returns.
    levels = frame.resample(frequency).last()
    result = pd.DataFrame(index=levels.index)
    for col in levels:
        s = levels[col]
        mode = modes.get(col, 'difference')
        if mode == 'return':
            result[col] = s.pct_change(fill_method=None).where(s.shift(1) != 0) * 100
        elif mode == 'log return':
            result[col] = np.log(s.where(s > 0)).diff() * 100
        elif mode == 'difference':
            result[col] = s.diff()
        elif mode == 'level':
            result[col] = s
        else:
            raise ValueError(f'Unknown transform {mode}')
    return result.replace([np.inf, -np.inf], np.nan)

def correlations(frame, method='pearson', minimum=30):
    valid = frame.notna().astype(int)
    counts = valid.T @ valid
    matrix = frame.corr(method=method, min_periods=minimum)
    return matrix, counts

def rolling_pair(frame, a, b, window, method='pearson'):
    def calc(chunk):
        pair = chunk[[a,b]].dropna()
        if len(pair) != window:
            return np.nan
        return pair.iloc[:,0].corr(pair.iloc[:,1], method=method)
    return pd.Series([calc(frame.iloc[max(0,i-window+1):i+1]) for i in range(len(frame))],
                     index=frame.index, name=f'{window}-period {method}')

def lead_lag(frame, driver, target, max_lag, minimum=30, method='pearson'):
    rows = []
    for lag in range(-max_lag, max_lag+1):
        # Positive lag: driver at t-lag versus target at t.
        pair = pd.concat([frame[driver].shift(lag),frame[target]],axis=1).dropna()
        r = pair.iloc[:,0].corr(pair.iloc[:,1],method=method) if len(pair)>=minimum else np.nan
        rows.append({'lag':lag, 'correlation':r, 'overlap':len(pair)})
    return pd.DataFrame(rows)

def quality(frame, asof=None):
    asof = pd.Timestamp(asof or pd.Timestamp.now().date())
    rows=[]
    for col in frame:
        s=frame[col].dropna()
        rows.append({'series':col,'observations':len(s),'missing_pct':100*frame[col].isna().mean(),
                     'first':s.index.min(),'last':s.index.max(),
                     'age_days':(asof.normalize()-s.index.max().normalize()).days,
                     'constant':s.nunique()<2})
    return pd.DataFrame(rows).set_index('series')

def demo():
    rng=np.random.default_rng(42)
    index=pd.bdate_range('2022-01-03','2026-09-30')
    n=len(index); risk=rng.normal(0,1,n); dollar=rng.normal(0,1,n)
    frame=pd.DataFrame(index=index)
    for code,start,beta in [('DEXUSEU',1.10,-.5),('DEXJPUS',115,.5),('DEXUSUK',1.35,-.35),
                            ('DTWEXBGS',110,.6),('SP500',4500,-.15)]:
        frame[code]=start*np.exp(np.cumsum((beta*dollar+.3*risk+rng.normal(0,.6,n))*.004))
    frame['DGS2']=3+np.cumsum(rng.normal(0,.015,n))
    frame['DGS10']=frame.DGS2+.4+np.cumsum(rng.normal(0,.01,n))
    frame['VIXCLS']=np.maximum(9,20+4*risk)
    frame['DCOILWTICO']=75+np.cumsum(rng.normal(0,.6,n))
    frame['DCOILBRENTEU']=frame.DCOILWTICO+5+rng.normal(0,.5,n)
    monthly=pd.date_range(index.min(),index.max(),freq='MS')
    for code,values in [('CPIAUCSL',280*np.exp(np.arange(len(monthly))*.002)),
                        ('UNRATE',4+rng.normal(0,.15,len(monthly))),
                        ('FEDFUNDS',np.full(len(monthly),4.5))]:
        # Observation dates, not genuine publication dates. Synthetic only.
        frame[code]=pd.Series(values,index=monthly).reindex(index)
    return frame
