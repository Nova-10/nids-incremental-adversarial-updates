"""Figure 5: seed-paired round-5 differences in calibrated attack-induced ASR for the pre-declared matched contrasts."""
import glob, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy import stats
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8})
S={'frozen':'A','static_adversarial':'B','matched_one_time':'M1','matched_one_time_e10':'M1-e10','matched_incremental':'M2','static_decision_trained':'B-dec'}
df=pd.concat([pd.read_csv(f) for f in glob.glob('/home/claude/matched/results_main/*.csv')]); df=df[(df['round']==5)&df.arm.isin(S)]
df['a']=df.arm.map(S); df['v']=df.attack_induced_asr_recalibrated*100
C=[('M1','M2'),('M1-e10','M2'),('M2','A'),('M1','A'),('M1-e10','A'),('B','M1'),('B','B-dec')]
fig,axs=plt.subplots(1,3,figsize=(7.4,3.0),sharey=True)
for ax,att in zip(axs,['FGSM-like','BIM-like','decision-only']):
    p=df[df.attack==att].pivot_table(index='seed',columns='a',values='v')
    labs=[]
    for i,(x,y) in enumerate(C):
        yy=len(C)-1-i; labs.append(f'{x} − {y}')
        if x not in p or y not in p: continue
        d=(p[x]-p[y]).dropna(); m=d.mean(); h=stats.t.ppf(.975,len(d)-1)*d.std(ddof=1)/np.sqrt(len(d))
        col='#1F5A96' if x.startswith('M') and y.startswith('M') else ('#8A5A00' if x=='B' else '#4A6B3A')
        ax.scatter(d,np.full(len(d),yy)+np.linspace(-.18,.18,len(d)),s=7,color=col,alpha=.4,lw=0)
        ax.errorbar(m,yy,xerr=h,fmt='o',color=col,ms=4.5,capsize=2.5,lw=1.3)
    ax.axvline(0,color='#6B7785',lw=.8,ls=':'); ax.set_title(att,fontsize=8.5)
    ax.grid(axis='x',color='#e5e5e5',lw=.5); ax.set_axisbelow(True)
axs[0].set_yticks(range(len(C))); axs[0].set_yticklabels(labs[::-1])
fig.supxlabel('Seed-paired difference in round-5 attack-induced ASR (percentage points, first arm minus second)',fontsize=8)
plt.tight_layout(); plt.savefig('/home/claude/matched/figures/fig5_matched_contrasts.png',dpi=220); plt.close(); print('ok')
