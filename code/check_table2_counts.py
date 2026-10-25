"""Check Table 2 partition and class counts against the raw files for seeds 17-36.
Usage: python3 check_table2_counts.py <dir with Zenodo files> <dir with run_pilot_v2.py>"""
import sys, pandas as pd
sys.path.insert(0, sys.argv[2]); import run_pilot_v2 as R
D=sys.argv[1].rstrip('/')+'/'
tr=pd.read_csv(D+'UNSW_NB15_testing-set.csv',sep='\t',header=None,names=R.UNSW_COLUMNS,low_memory=False)
te=pd.read_csv(D+'UNSW_NB15_training-set.csv',sep='\t',header=None,names=R.UNSW_COLUMNS,low_memory=False)
y=tr.label.to_numpy()
print('official training partition (Zenodo testing-set file):',len(y),'benign',int((y==0).sum()),'malicious',int((y==1).sum()))
print('official test partition (Zenodo training-set file):',len(te),'benign',int((te.label==0).sum()),'malicious',int((te.label==1).sum()))
seen=set()
for s in range(17,37):
    parts=R.stratified_split(y,s); seen.add(tuple((int((y[p]==0).sum()),int((y[p]==1).sum())) for p in parts))
print('initial/validation/adaptation (benign, malicious) across seeds 17-36:',seen)
