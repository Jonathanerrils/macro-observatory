"""Reproduce a single predeclared pair study without the dashboard."""
import argparse
from pathlib import Path
from macro.data import read_csv
from macro.engine import CATALOG, demo, transform
from macro.research import block_bootstrap, breakdown, chronological_holdout, report_bundle
import pandas as pd

parser=argparse.ArgumentParser()
parser.add_argument('--csv',help='Wide level panel; otherwise uses clearly synthetic demo')
parser.add_argument('--driver',default='DEXUSEU'); parser.add_argument('--target',default='DTWEXBGS')
parser.add_argument('--frequency',choices=['B','W-FRI','ME'],default='W-FRI')
parser.add_argument('--method',choices=['pearson','spearman'],default='pearson')
parser.add_argument('--block',type=int,default=5); parser.add_argument('--reps',type=int,default=500)
parser.add_argument('--window',type=int,default=60); parser.add_argument('--max-lag',type=int,default=8)
parser.add_argument('--minimum',type=int,default=30); parser.add_argument('--seed',type=int,default=42)
parser.add_argument('--driver-transform',choices=['return','difference','log return','level'])
parser.add_argument('--target-transform',choices=['return','difference','log return','level'])
parser.add_argument('--output',default='research_outputs/study.zip')
args=parser.parse_args()
raw=read_csv(args.csv) if args.csv else demo()
modes={args.driver:args.driver_transform or CATALOG.get(args.driver,('','','difference'))[2],
       args.target:args.target_transform or CATALOG.get(args.target,('','','difference'))[2]}
frame=transform(raw[[args.driver,args.target]],args.frequency,modes)
settings={**vars(args),'transforms':modes,'source':'CSV latest observations' if args.csv else 'SYNTHETIC DEMO',
          'point_in_time_safe':False,'train_fraction':.7}
kwargs=dict(block=args.block,reps=args.reps,seed=args.seed,minimum=args.minimum,method=args.method)
ci,draws=block_bootstrap(frame,**kwargs)
change=breakdown(frame,args.window,**kwargs)
holdout,scan,predictions=chronological_holdout(frame,args.driver,args.target,args.max_lag,.7,args.minimum,args.method)
results={'correlation_interval':ci,'breakdown':change,'holdout':holdout}
blob=report_bundle(frame,settings,results,{'bootstrap_draws':pd.DataFrame({'correlation':draws}),
                                       'training_lag_scan':scan,'holdout_predictions':predictions})
output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(blob)
print('Saved',output)
print('Source:',settings['source'])
print('Correlation:',round(ci['correlation'],3),'interval:',round(ci['lower'],3),round(ci['upper'],3))
print('Selected lag:',holdout['selected_lag'],'Holdout MSE skill:',round(holdout['skill_vs_training_mean'],4))
