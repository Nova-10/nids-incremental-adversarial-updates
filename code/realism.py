"""Raw-unit perturbation sizes and feature-relation checks for the frozen (initial) model.
Re-creates each seed's split, preprocessing, initial model, fixed threshold and evaluation cohort
with the archived runner functions, attacks the cohort, and maps the perturbed features back to raw units."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/repro_v6'); import run_pilot_v2 as R
D='/home/claude/repro_v6/data/UNSW-NB15/'
tr=pd.read_csv(D+'UNSW_NB15_testing-set.csv',sep='\t',header=None,names=R.UNSW_COLUMNS,low_memory=False)
te=pd.read_csv(D+'UNSW_NB15_training-set.csv',sep='\t',header=None,names=R.UNSW_COLUMNS,low_memory=False)
raw_X,y,raw_Xt,yt=R.prepare_raw(tr,te)
F=R.PERTURB_FEATURES; out={'per_seed':{}}
for seed in [17,18,19,20,21]:
    init,val,adapt=R.stratified_split(y,seed)
    (X,Xt),cont=R.fit_preprocessor(raw_X.iloc[init],[raw_X,raw_Xt])
    nums=[c for c in raw_X.columns if pd.api.types.is_numeric_dtype(raw_X[c])]
    ref=raw_X.iloc[init][nums].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan)
    med=ref.median().fillna(0); ref=ref.fillna(med); lo,hi=ref.min(),ref.max(); sc=(hi-lo).replace(0,1)
    clean=R.MLP(X.shape[1],seed); clean.train(X[init],y[init],epochs=5,seed=seed)
    thr=R.select_threshold_at_fpr(clean,X[val],y[val],.05)
    elig=np.flatnonzero((yt==1)&(clean.prob(Xt)>=thr))
    ev=np.random.default_rng(seed+1000).choice(elig,min(len(elig),1000),replace=False)
    x0=Xt[ev]; res={}
    advs={'FGSM-like':R.attack(clean,x0,cont,.03,1),'BIM-like':R.attack(clean,x0,cont,.03,5),
          'decision-only':R.decision_only_attack(clean,x0,cont,thr,.03,50,seed+1)[0]}
    def raw(xm):  # perturbed features back to raw units
        return {f:xm[:,nums.index(f)]*sc[f]+lo[f] for f in F}
    r0=raw(x0)
    res['eps_raw']={f:float(.03*sc[f]) for f in F}
    res['cohort_median_raw']={f:float(np.median(r0[f])) for f in F}
    for name,xa in advs.items():
        ra=raw(xa); changed=np.any(np.abs(xa[:,cont]-x0[:,cont])>1e-9,axis=1)
        # relations that hold in every training row (checked separately)
        tcp_ok=np.isclose(ra['tcprtt'],ra['synack']+ra['ackdat'],atol=1e-6)
        sp=raw_Xt.iloc[ev]['spkts'].to_numpy(float); dp=raw_Xt.iloc[ev]['dpkts'].to_numpy(float)
        pos=ra['dur']>0
        rate_ok=np.ones(len(ev),bool); rate_ok[pos]=np.isclose(ra['rate'][pos],(sp[pos]+dp[pos]-1)/ra['dur'][pos],rtol=1e-3)
        rate_ok[~pos]=ra['rate'][~pos]==0
        orig_tcp=np.isclose(r0['tcprtt'],r0['synack']+r0['ackdat'],atol=1e-6)
        pos0=r0['dur']>0; rate0=np.ones(len(ev),bool); rate0[pos0]=np.isclose(r0['rate'][pos0],(sp[pos0]+dp[pos0]-1)/r0['dur'][pos0],rtol=1e-3); rate0[~pos0]=r0['rate'][~pos0]==0
        proto=raw_Xt.iloc[ev]['proto'].astype(str).to_numpy(); nontcp=proto!='tcp'
        timing_set=(np.abs(ra['tcprtt'])>1e-9)|(np.abs(ra['synack'])>1e-9)|(np.abs(ra['ackdat'])>1e-9)
        timing_before=(np.abs(r0['tcprtt'])>1e-9)|(np.abs(r0['synack'])>1e-9)|(np.abs(r0['ackdat'])>1e-9)
        nt=changed&nontcp
        rel={f:float(np.median(np.abs(ra[f]-r0[f])/np.maximum(np.abs(r0[f]),1e-12))) for f in F}
        res[name]={'flows':int(len(ev)),'flows_changed':int(changed.sum()),
          'tcprtt_relation_broken_share_of_changed':float(np.mean(~tcp_ok[changed])) if changed.any() else None,
          'rate_relation_broken_share_of_changed':float(np.mean(~rate_ok[changed])) if changed.any() else None,
          'either_broken_share_of_changed':float(np.mean(~(tcp_ok&rate_ok)[changed])) if changed.any() else None,
          'tcprtt_relation_held_before':float(np.mean(orig_tcp)),
          'nontcp_share_of_cohort':float(np.mean(nontcp)),'nontcp_timing_nonzero_before':float(np.mean(timing_before[nontcp])) if nontcp.any() else None,'nontcp_changed_timing_nonzero_after':float(np.mean(timing_set[nt])) if nt.any() else None,'nontcp_changed_n':int(nt.sum()),
          'rate_relation_held_before':float(np.mean(rate0)),'rate_relation_held_before_changed':float(np.mean(rate0[changed])) if changed.any() else None,
          'median_relative_change':rel}
    out['per_seed'][seed]=res; print(seed,'done',flush=True)
json.dump(out,open('/home/claude/matched/realism/realism_results.json','w'),indent=1)
