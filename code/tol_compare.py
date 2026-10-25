import sys,pandas as pd,numpy as np
a=pd.read_csv(sys.argv[1]); b=pd.read_csv(sys.argv[2])
k=['arm','round']; m=a.merge(b,on=k,suffixes=('_a','_b'))
out={}
for c in a.columns:
    if c in k or any(w in c.lower() for w in ('seconds','wall','time')): continue
    x,y=m[c+'_a'],m[c+'_b']
    if pd.api.types.is_numeric_dtype(x): out[c]=float(np.nanmax(np.abs(x-y))) if len(x) else 0
    elif (x.astype(str)!=y.astype(str)).any(): out[c]='TEXT DIFF'
bad={c:v for c,v in out.items() if v=='TEXT DIFF' or v>1e-6}
print(len(m),'rows; max abs diff overall',max(v for v in out.values() if v!='TEXT DIFF'),'; cols over 1e-6:',bad)
