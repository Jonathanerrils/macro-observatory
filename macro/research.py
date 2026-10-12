"""Dependence research with reproducible circular-block bootstrap and frozen holdout."""
import hashlib
import io
import json
import zipfile
from html import escape
import numpy as np
import pandas as pd
from scipy.stats import rankdata


def _corr(values, method='pearson', minimum=20):
    values=np.asarray(values,dtype=float)
    values=values[np.isfinite(values).all(axis=1)]
    if len(values)<minimum: return np.nan
    if method=='spearman': values=np.column_stack([rankdata(values[:,i]) for i in range(2)])
    elif method!='pearson': raise ValueError('Use pearson or spearman')
    centered=values-values.mean(axis=0)
    denom=np.sqrt((centered[:,0]**2).sum()*(centered[:,1]**2).sum())
    return float(np.clip((centered[:,0]*centered[:,1]).sum()/denom,-1,1)) if denom>0 else np.nan


def block_bootstrap(pair, block=5, reps=500, confidence=.95, minimum=20, seed=42, method='pearson'):
    """Resample paired rows in circular contiguous blocks, keeping missing calendar bins."""
    values=np.asarray(pair,dtype=float)
    n=len(values)
    if values.ndim!=2 or values.shape[1]!=2: raise ValueError('Provide exactly two columns')
    if not 0<confidence<1 or reps<100 or minimum<3: raise ValueError('Invalid bootstrap settings')
    if not 1<=block<=max(1,n//3): raise ValueError('Block length must be at most one third of the sample')
    observed=_corr(values,method,minimum)
    if not np.isfinite(observed): raise ValueError('Insufficient overlap or constant series')
    rng=np.random.default_rng(seed); draws=[]
    for _ in range(reps):
        starts=rng.integers(0,n,size=int(np.ceil(n/block)))
        idx=((starts[:,None]+np.arange(block))%n).ravel()[:n]
        draws.append(_corr(values[idx],method,minimum))
    draws=np.asarray(draws); draws=draws[np.isfinite(draws)]
    if len(draws)<.9*reps: raise ValueError('Too many invalid replicates; increase sample coverage')
    alpha=(1-confidence)/2
    lo,hi=np.quantile(draws,[alpha,1-alpha])
    result={'correlation':observed,'lower':float(lo),'upper':float(hi),
            'overlap':int(np.isfinite(values).all(axis=1).sum()),'periods':n,
            'block_length':block,'replicates':reps,'valid_replicates':len(draws),
            'confidence':confidence,'seed':seed,'method':method}
    return result,draws


def breakdown(pair, window=60, **settings):
    if len(pair)<2*window: raise ValueError(f'Need at least {2*window} sampled periods')
    prior=pair.iloc[-2*window:-window]; recent=pair.iloc[-window:]
    old,d0=block_bootstrap(prior,**settings)
    new,d1=block_bootstrap(recent,**{**settings,'seed':settings.get('seed',42)+1})
    size=min(len(d0),len(d1)); delta=d1[:size]-d0[:size]
    alpha=(1-settings.get('confidence',.95))/2
    lo,hi=np.quantile(delta,[alpha,1-alpha])
    return {'prior':old,'recent':new,'delta':new['correlation']-old['correlation'],
            'delta_lower':float(lo),'delta_upper':float(hi),
            'prior_start':str(prior.index[0]),'prior_end':str(prior.index[-1]),
            'recent_start':str(recent.index[0]),'recent_end':str(recent.index[-1]),
            'interval_excludes_zero':bool(lo>0 or hi<0)}


def chronological_holdout(frame,driver,target,max_lag=8,train_fraction=.7,minimum=30,method='pearson'):
    """Choose positive lag on training only, embargo max_lag rows, freeze OLS coefficients."""
    if driver==target or max_lag<1 or not .5<=train_fraction<=.85:
        raise ValueError('Invalid holdout settings')
    n=len(frame); split=int(n*train_fraction); test_start=split+max_lag
    if test_start>=n: raise ValueError('Not enough observations after embargo')
    candidates=[]; aligned={}
    for lag in range(1,max_lag+1):
        pair=pd.DataFrame({'x':frame[driver].shift(lag),'y':frame[target]})
        aligned[lag]=pair
        train=pair.iloc[:split].dropna()
        candidates.append({'lag':lag,'train_correlation':_corr(train,method,minimum),'train_overlap':len(train)})
    scores=pd.DataFrame(candidates)
    eligible=scores.dropna(subset=['train_correlation'])
    if eligible.empty: raise ValueError('No lag has enough nonconstant training observations')
    best=int(eligible.loc[eligible.train_correlation.abs().idxmax(),'lag'])
    train=aligned[best].iloc[:split].dropna()
    test=aligned[best].iloc[test_start:].dropna()
    if len(test)<minimum: raise ValueError('Selected lag has insufficient holdout coverage')
    design=np.column_stack([np.ones(len(train)),train.x])
    if np.linalg.matrix_rank(design)<2: raise ValueError('Constant training predictor')
    intercept,slope=np.linalg.lstsq(design,train.y,rcond=None)[0]
    prediction=intercept+slope*test.x
    baseline=float(train.y.mean())
    mse=float(np.mean((test.y-prediction)**2)); base_mse=float(np.mean((test.y-baseline)**2))
    output=pd.DataFrame({'actual':test.y,'prediction':prediction,'training_mean_baseline':baseline})
    result={'selected_lag':best,'train_periods':split,'embargo_periods':max_lag,
            'train_end':str(frame.index[split-1]),'test_start':str(frame.index[test_start]),
            'train_overlap':len(train),'test_overlap':len(test),'intercept':float(intercept),'slope':float(slope),
            'train_correlation':_corr(train,method,minimum),'test_correlation':_corr(test,method,minimum),
            'test_mse':mse,'baseline_mse':base_mse,'skill_vs_training_mean':1-mse/base_mse if base_mse>0 else np.nan}
    return result,scores,output


def report_bundle(frame,settings,results,tables):
    csv=frame.to_csv(index_label='date').encode()
    manifest={'settings':settings,'results':results,'panel_sha256':hashlib.sha256(csv).hexdigest(),
              'limitations':['Latest-revised observation data; not point-in-time safe.',
                'Bootstrap assumes local stationarity; block length and sample choice affect coverage.',
                'Breakdown uses independent window resampling and ignores dependence across their boundary.',
                'One chronological holdout; repeated user tuning compromises its independence.',
                'Lag selection is exploratory. No corrected p-values, causality or tradable edge claimed.',
                'OLS predicts transformed observations; no position sizing, costs or trading backtest.']}
    blob=json.dumps(manifest,indent=2,default=str)
    body='<html><head><meta charset="utf-8"><title>Cross-Market Research Report</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px}pre{white-space:pre-wrap}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #bbb}</style></head><body><h1>Cross-Market Research Report</h1><p>Reproducible dependence analysis. Review the data source and limitations before interpreting results.</p><pre>'+escape(blob)+'</pre>'
    for name,table in tables.items(): body+='<h2>'+escape(name)+'</h2>'+table.to_html(escape=True)
    body+='</body></html>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.html',body); z.writestr('manifest.json',blob); z.writestr('transformed_panel.csv',csv)
        for name,table in tables.items(): z.writestr(name+'.csv',table.to_csv(index_label='date'))
    return out.getvalue()
