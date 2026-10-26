"""Figure 6: round-by-round calibrated attack-induced ASR over 20 seeds for the recipe-matched incremental arm and its comparators."""
import glob, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy import stats
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8})
S={'frozen':('A Frozen','#6B7785','o','-'),'static_adversarial':('B Static','#8A5A00','s','-'),'static_decision_trained':('B-dec Static (decision-only examples)','#C08A2E','s','--'),
   'matched_one_time_e10':('M1-e10 One-time, 1 × 10 epochs','#4A6B3A','^','--'),'matched_incremental':('M2 Incremental, memory only','#1F5A96','D','-'),
   'matched_incremental_full':('M2-full Incremental, static recipe','#7A2E8A','o','-')}
df=pd.concat([pd.read_csv(f) for f in glob.glob('/home/claude/matched/results_full/*.csv')]); df=df[df.arm.isin(S)]
df['v']=df.attack_induced_asr_recalibrated*100
fig,axs=plt.subplots(1,2,figsize=(7.4,3.0))
for ax,att in zip(axs,['FGSM-like','decision-only']):
    g=df[df.attack==att]
    for k,(lab,col,mk,ls) in S.items():
        h=g[g.arm==k]
        if h.empty: continue
        st=h.groupby('round').v.agg(['mean','std','count'])
        hw=stats.t.ppf(.975,st['count']-1)*st['std']/np.sqrt(st['count'])
        x=st.index.values+({'frozen':-.12,'static_adversarial':-.06,'static_decision_trained':-.03,'matched_one_time_e10':0.,'matched_incremental':.06,'matched_incremental_full':.12}[k])
        ax.errorbar(x,st['mean'],yerr=hw,color=col,marker=mk,ms=3.5,lw=1.3 if k=='matched_incremental_full' else .9,ls=ls,capsize=2,label=lab)
    ax.set_title(att+(' (BIM-like is nearly identical)' if att=='FGSM-like' else ''),fontsize=8.5); ax.set_xticks(range(1,6)); ax.set_xlabel('Round')
    ax.grid(color='#e5e5e5',lw=.5); ax.set_axisbelow(True)
axs[0].set_ylabel('Attack-induced ASR (%), calibrated')
h,l=[],[]
for ax in axs:
    for a,b in zip(*ax.get_legend_handles_labels()):
        if b not in l: h.append(a); l.append(b)
fig.legend(h,l,loc='lower center',ncol=3,fontsize=7,frameon=False)
plt.tight_layout(rect=(0,.13,1,1)); plt.savefig('/home/claude/matched/figures/fig6_recipe_matched_trajectories.png',dpi=220); print('ok')
