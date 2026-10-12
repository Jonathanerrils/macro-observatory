import hashlib
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from .research import block_bootstrap, breakdown, chronological_holdout, report_bundle


def render(frame, source_settings):
    st.subheader('Cross-Market Correlation Research Engine')
    st.caption('Reproducible block resampling · non-overlapping windows · frozen chronological holdout')
    a,b=st.columns(2)
    driver=a.selectbox('Research driver',list(frame),key='research_driver')
    target=b.selectbox('Research target',[x for x in frame if x!=driver],key='research_target')
    with st.form('research_settings'):
        c1,c2,c3=st.columns(3)
        block=c1.number_input('Block length (sample periods)',1,30,5)
        reps=c2.selectbox('Bootstrap replicates',[300,500,1000,2000],index=1)
        seed=c3.number_input('Random seed',0,1000000,42)
        c1,c2,c3=st.columns(3)
        window=c1.number_input('Each breakdown window',20,500,60)
        train_fraction=c2.slider('Training fraction',.5,.85,.7,.05)
        max_lag=c3.slider('Maximum positive lag',1,20,8)
        run=st.form_submit_button('Run research',type='primary')
    settings={**source_settings,'driver':driver,'target':target,'block':block,'replicates':reps,
              'seed':seed,'breakdown_window':window,'train_fraction':train_fraction,'max_lag':max_lag}
    fingerprint=hashlib.sha256((frame.to_csv()+json.dumps(settings,sort_keys=True)).encode()).hexdigest()
    if run:
        outputs={}; tables={}; errors={}
        pair=frame[[driver,target]]
        kwargs={'block':int(block),'reps':int(reps),'seed':int(seed),'minimum':source_settings['minimum'],
                'method':source_settings['method']}
        with st.spinner('Resampling paired blocks and evaluating the untouched holdout…'):
            try:
                outputs['correlation_interval'],draws=block_bootstrap(pair,**kwargs)
                tables['bootstrap_draws']=pd.DataFrame({'correlation':draws})
            except ValueError as e: errors['Correlation interval']=str(e)
            try: outputs['breakdown']=breakdown(pair,int(window),**kwargs)
            except ValueError as e: errors['Breakdown']=str(e)
            try:
                outputs['holdout'],tables['training_lag_scan'],tables['holdout_predictions']=chronological_holdout(
                    frame,driver,target,max_lag,train_fraction,source_settings['minimum'],source_settings['method'])
            except ValueError as e: errors['Holdout']=str(e)
        outputs['errors']=errors
        st.session_state['research_run']={'fingerprint':fingerprint,'settings':settings,'outputs':outputs,'tables':tables,
                                          'bundle':report_bundle(frame,settings,outputs,tables)}
    saved=st.session_state.get('research_run')
    if not saved: st.info('Choose a pair and run research. Results are computed only when you submit.'); return
    if saved['fingerprint']!=fingerprint:
        st.warning('Inputs changed. Run research again to update the results.'); return
    outputs=saved['outputs']; tables=saved['tables']
    for title,error in outputs['errors'].items(): st.warning(f'{title}: {error}')
    if 'correlation_interval' in outputs:
        ci=outputs['correlation_interval']; a,b,c=st.columns(3)
        a.metric('Correlation',f"{ci['correlation']:.3f}")
        b.metric('95% percentile interval',f"[{ci['lower']:.3f}, {ci['upper']:.3f}]")
        c.metric('Pair overlap',ci['overlap'])
        st.plotly_chart(px.histogram(tables['bootstrap_draws'],x='correlation',nbins=40,title='Circular-block bootstrap distribution'),width='stretch')
    if 'breakdown' in outputs:
        r=outputs['breakdown']
        st.subheader('Correlation change between adjacent windows')
        st.write(f"Prior: {r['prior']['correlation']:.3f} → Recent: {r['recent']['correlation']:.3f}")
        st.write(f"Change: {r['delta']:.3f}; approximate 95% interval [{r['delta_lower']:.3f}, {r['delta_upper']:.3f}]")
        st.caption('Interval excludes zero: '+str(r['interval_excludes_zero'])+'. Independent window bootstrap; this is not a calibrated regime detector or a multiple-testing-adjusted result.')
    if 'holdout' in outputs:
        r=outputs['holdout']; st.subheader('Chronological holdout')
        st.write(f"Training-selected lag: {r['selected_lag']} · Embargo: {r['embargo_periods']} periods · Holdout overlap: {r['test_overlap']}")
        a,b,c=st.columns(3)
        a.metric('Training correlation',f"{r['train_correlation']:.3f}")
        b.metric('Holdout correlation',f"{r['test_correlation']:.3f}")
        c.metric('MSE skill vs training mean',f"{r['skill_vs_training_mean']:.1%}")
        st.caption('Positive skill means lower squared error than a frozen training-mean forecast. Negative skill means worse. Correlation alone is not predictive performance.')
        st.dataframe(tables['training_lag_scan'],hide_index=True,width='stretch')
        st.plotly_chart(px.line(tables['holdout_predictions'],title='Untouched holdout: actual, frozen OLS forecast and baseline'),width='stretch')
    st.warning('Observation-time analysis only: latest-revised data are not historically tradable inputs. Repeated tuning on this holdout turns it into development data. Bootstrap uncertainty depends on stationarity and block length.')
    st.download_button('Download research report + reproducibility bundle',saved['bundle'],'cross_market_research.zip','application/zip')
