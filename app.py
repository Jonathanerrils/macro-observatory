from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from macro.engine import CATALOG, demo, transform, correlations, rolling_pair, lead_lag, quality
from macro.data import read_csv, refresh

st.set_page_config(page_title='Macro Observatory',page_icon='🌐',layout='wide')
st.markdown('### MACRO OBSERVATORY')
st.title('Global macro · Cross-market research')
st.caption('Local research console / transparent transforms / auditable snapshots')
folder=Path(__file__).parent/'data'
with st.sidebar:
    st.header('Research workspace')
    source=st.radio('Data source',['Synthetic demo','Saved FRED snapshot','Upload CSV'])
    uploaded=st.file_uploader('Wide CSV: date, series1, series2…',type='csv') if source=='Upload CSV' else None
    st.divider()
    st.subheader('Download latest FRED data')
    codes=st.multiselect('Series',list(CATALOG),default=['DEXUSEU','DEXJPUS','DTWEXBGS','DGS2','DGS10','VIXCLS','SP500','DCOILWTICO'],format_func=lambda x:CATALOG[x][0])
    start=st.date_input('Start date',pd.Timestamp('2022-01-01'))
    if st.button('Refresh snapshot',disabled=not codes):
        try:
            with st.spinner('Downloading and recording source hashes…'):
                _,errors=refresh(folder,codes,str(start))
            st.success('Snapshot saved. Select Saved FRED snapshot above.')
            for code,error in errors.items(): st.warning(f'{code}: {error}')
        except Exception as exc: st.error(str(exc))
try:
    if source=='Synthetic demo': raw=demo()
    elif source=='Saved FRED snapshot': raw=read_csv(folder/'latest.csv')
    elif uploaded is not None: raw=read_csv(uploaded)
    else: st.info('Upload a dated numeric CSV to begin.'); st.stop()
except Exception as exc: st.error(f'Cannot load panel: {exc}'); st.stop()
if source=='Synthetic demo':
    st.warning('SYNTHETIC DEMO — these are generated observations, not market history or trading signals.')
else:
    st.warning('Latest observations may be revised. Observation dates are not publication dates. This panel is not point-in-time safe for backtesting.')
with st.sidebar:
    frequency=st.selectbox('Sampling',['Weekly','Daily','Monthly'],index=0)
    freq={'Daily':'B','Weekly':'W-FRI','Monthly':'ME'}[frequency]
    method=st.selectbox('Correlation',['pearson','spearman'])
    minimum=st.slider('Minimum pair overlap',5,100,30)
    window=st.slider('Rolling window (sample periods)',10,120,30)
    selected=st.multiselect('Analysis universe',list(raw),default=list(raw)[:8],format_func=lambda x:CATALOG.get(x,(x,))[0])
    modes={}
    with st.expander('Series transformations',expanded=False):
        for code in selected:
            default=CATALOG.get(code,('', '', 'difference'))[2]
            opts=['return','difference','log return','level']
            modes[code]=st.selectbox(code,opts,index=opts.index(default),key='mode_'+code)
if len(selected)<2: st.info('Select at least two series.'); st.stop()
changes=transform(raw[selected],freq,modes)
first,last=changes.index.min().date(),changes.index.max().date()
dates=st.date_input('Analysis interval',(first,last),min_value=first,max_value=last)
if len(dates)!=2: st.stop()
changes=changes.loc[str(dates[0]):str(dates[1])]
matrix,counts=correlations(changes,method,minimum)
a,b,c,d=st.columns(4)
a.metric('Series',len(selected)); b.metric('Sample periods',len(changes))
c.metric('Sampling',frequency); d.metric('Latest observation',raw.index.max().strftime('%d %b %Y'))
tabs=st.tabs(['Macro monitor','Correlation engine','Pair laboratory','Data quality & export','Research validation'])
with tabs[0]:
    st.subheader('Indicator monitor')
    rows=[]
    for code in raw:
        s=raw[code].dropna()
        rows.append({'Indicator':CATALOG.get(code,(code,'Custom'))[0],'Group':CATALOG.get(code,(code,'Custom'))[1],
                     'Latest':s.iloc[-1],'Previous':s.iloc[-2],'Change':s.iloc[-1]-s.iloc[-2],
                     'Observation date':s.index[-1].date()})
    st.dataframe(pd.DataFrame(rows),width='stretch',hide_index=True)
    if {'DGS2','DGS10'}.issubset(raw):
        curve=raw.DGS10-raw.DGS2
        st.plotly_chart(px.line(curve,title='US yield curve: 10Y minus 2Y (percentage points)'),width='stretch')
    st.caption('US-focused macro starter with major FX crosses and cross-market indicators. ECB, IMF, OECD and broader country coverage are next-stage adapters.')
with tabs[1]:
    st.subheader('Dependence across transformed observations')
    st.plotly_chart(go.Figure(go.Heatmap(z=matrix.values,x=matrix.columns,y=matrix.index,zmin=-1,zmax=1,
                       colorscale='RdBu',reversescale=True,colorbar={'title':'r'})),width='stretch')
    st.caption('Pairwise complete observations; missing periods are not forward filled. Each pair may use a different sample.')
    st.dataframe(matrix,width='stretch')
    st.subheader('Pairwise sample counts'); st.dataframe(counts,width='stretch')
    if 'level' in modes.values(): st.warning('Level correlations can be spurious for trending series. Use changes or returns for market dependence analysis.')
with tabs[2]:
    left,right=st.columns(2)
    driver=left.selectbox('Driver',selected,index=0)
    target=right.selectbox('Target',[x for x in selected if x!=driver])
    pair=changes[[driver,target]].dropna()
    st.plotly_chart(px.scatter(pair,x=driver,y=target,title='Aligned transformed observations'),width='stretch')
    rolling=rolling_pair(changes,driver,target,window,method)
    st.plotly_chart(px.line(rolling,title=f'Rolling {method} correlation · {window} complete consecutive periods'),width='stretch')
    recent=changes.tail(window); prior=changes.iloc[-2*window:-window]
    def pair_r(p):
        q=p[[driver,target]].dropna()
        return q.iloc[:,0].corr(q.iloc[:,1],method=method) if len(q)>=minimum else np.nan
    r1,r0=pair_r(recent),pair_r(prior)
    st.write(f'Recent non-overlapping window: {r1:.3f} · Prior window: {r0:.3f}')
    if np.isfinite(r1) and np.isfinite(r0) and abs(r1-r0)>=.3:
        st.info('Large descriptive correlation change (≥0.30). Inspect overlap and events before interpreting it.')
    lag=st.slider('Maximum lead/lag (sample periods)',1,20,8)
    result=lead_lag(changes,driver,target,lag,minimum,method)
    st.plotly_chart(px.bar(result,x='lag',y='correlation',title='Exploratory lead/lag dependence'),width='stretch')
    st.caption('Positive lag: earlier driver aligned with later target. Lag scans are exploratory, have multiple-testing bias and do not establish causality or predictive value.')
    st.dataframe(result,hide_index=True)
with tabs[3]:
    st.subheader('Coverage and freshness')
    st.dataframe(quality(raw),width='stretch')
    st.caption('Age uses observation date, not release date. Monthly series naturally have more missing dates in a mixed-frequency panel.')
    config={'source':source,'frequency':frequency,'method':method,'minimum':minimum,'window':window,
            'transforms':modes,'date_range':[str(x) for x in dates],'point_in_time_safe':False}
    st.download_button('Download transformed panel',changes.to_csv(index_label='date'),'transformed_panel.csv','text/csv')
    st.download_button('Download correlation matrix',matrix.to_csv(),'correlations.csv','text/csv')
    st.download_button('Download sample counts',counts.to_csv(),'sample_counts.csv','text/csv')
    st.download_button('Download research settings',json.dumps(config,indent=2),'research_settings.json','application/json')
    st.download_button('Download source panel',raw.to_csv(index_label='date'),'source_panel.csv','text/csv')

with tabs[4]:
    from macro.research_ui import render
    render(changes,config)
