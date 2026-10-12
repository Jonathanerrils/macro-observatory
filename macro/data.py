import io
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.parse import urlencode
import pandas as pd
from .engine import CATALOG, validate

def fetch_fred(code, start='2022-01-01'):
    if code not in CATALOG:
        raise ValueError('Unknown catalog series')
    url='https://fred.stlouisfed.org/graph/fredgraph.csv?'+urlencode({'id':code,'cosd':start})
    with urlopen(url,timeout=20) as response:
        raw=response.read()
    table=pd.read_csv(io.BytesIO(raw),na_values=['.'])
    table.iloc[:,0]=pd.to_datetime(table.iloc[:,0])
    s=pd.Series(pd.to_numeric(table[code],errors='raise').to_numpy(),index=table.iloc[:,0],name=code)
    return s,raw,url

def refresh(folder, codes, start):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    snapshot=folder/'raw'/stamp; snapshot.mkdir(parents=True)
    series=[]; records=[]; errors={}
    for code in codes:
        try:
            s,raw,url=fetch_fred(code,start)
            series.append(s)
            (snapshot/f'{code}.csv').write_bytes(raw)
            records.append({'series':code,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),
                            'retrieved_utc':stamp,'vintage':'latest revised; not point-in-time'})
        except Exception as exc:
            errors[code]=str(exc)
    (snapshot/'manifest.json').write_text(json.dumps({'series':records,'errors':errors},indent=2))
    if not series:
        raise ValueError('No series downloaded. Check internet access or upload a CSV.')
    frame=validate(pd.concat(series,axis=1))
    save_snapshot(frame,folder,stamp)
    return frame,errors

def save_snapshot(frame,folder,stamp):
    import duckdb
    folder=Path(folder)
    long=frame.rename_axis('date').reset_index().melt('date',var_name='series',value_name='value').dropna()
    long['snapshot']=stamp
    with duckdb.connect(str(folder/'macro.duckdb')) as db:
        db.execute('CREATE TABLE IF NOT EXISTS observations AS SELECT * FROM long LIMIT 0')
        db.execute('INSERT INTO observations SELECT * FROM long')
    frame.to_csv(folder/'latest.csv',index_label='date')

def read_csv(file):
    table=pd.read_csv(file)
    if 'date' not in table:
        # Supports FRED single-series exports as well as wide panels.
        table=table.rename(columns={table.columns[0]:'date'})
    return validate(table.set_index('date').replace('.',float('nan')))
