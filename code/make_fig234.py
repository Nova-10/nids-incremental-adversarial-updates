import glob, pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
import sys
R = sys.argv[1].rstrip("/") + "/"   # archive change: input folder (was hard-coded)
OUT = sys.argv[2].rstrip("/") + "/"  # archive change: output folder (was hard-coded)
names={"frozen":"A Frozen","static_adversarial":"B Static","incremental_rehearsal":"C Rehearsal","incremental_no_rehearsal":"D No rehearsal","incremental_balanced_rehearsal":"E Balanced","clean_continued":"F Control"}
att={"fgsm":"FGSM-like","bim5":"BIM-like","decision":"Decision-only"}
dfs=[]
for a in att:
    for f in sorted(glob.glob(R+f"unsw_nb15_ext_{a}_s*.csv")):
        d=pd.read_csv(f); d["atk"]=att[a]; d["arm"]=d["arm"].map(names); dfs.append(d)
D=pd.concat(dfs)
for c in ["attack_induced_asr_recalibrated","attack_induced_asr","recalibrated_clean_fpr","clean_fpr"]: D[c]=D[c]*100
arms=list(names.values())
col=dict(zip(arms,["#6B7785","#D98E1F","#3C9D5D","#C0392B","#2F6FB5","#7D5BA6"]))
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8})
from scipy import stats
def ci(x):
    x=np.asarray(x); h=stats.t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x)); return x.mean(),h
# Fig 2
fig,axs=plt.subplots(1,3,figsize=(7.4,3.1),sharey=True)
for ax,a in zip(axs,att.values()):
    for i,arm in enumerate(arms):
        v=D[(D.atk==a)&(D["round"]==5)&(D.arm==arm)].sort_values("seed")["attack_induced_asr_recalibrated"].values
        m,h=ci(v); y=len(arms)-1-i
        ax.scatter(v,np.full(len(v),y)+np.linspace(-.12,.12,len(v)),s=9,color=col[arm],alpha=.45,lw=0)
        ax.errorbar(m,y,xerr=h,fmt="o",color=col[arm],ms=5,capsize=2.5,lw=1.4)
    ax.axvline(D[(D.atk==a)&(D["round"]==5)&(D.arm=="A Frozen")]["attack_induced_asr_recalibrated"].mean(),color="#6B7785",ls=":",lw=.8)
    ax.set_title(a,fontsize=8.5); ax.set_xlabel("Attack-induced ASR (%)"); ax.set_xlim(0,13)
    ax.set_yticks(range(len(arms))); ax.set_yticklabels(arms[::-1]); ax.grid(axis="x",color="#e5e5e5",lw=.5); ax.set_axisbelow(True)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(OUT+"fig2_round5_asr.png",dpi=220); plt.close()
# Fig 3 arrows: validation-calibrated -> fixed
fig,axs=plt.subplots(1,2,figsize=(7.4,3.4),sharey=True)
for ax,a in zip(axs,["FGSM-like","Decision-only"]):
    for arm in arms:
        s=D[(D.atk==a)&(D["round"]==5)&(D.arm==arm)]
        x0,y0=s["recalibrated_clean_fpr"].mean(),s["attack_induced_asr_recalibrated"].mean()
        x1,y1=s["clean_fpr"].mean(),s["attack_induced_asr"].mean()
        ax.scatter(x0,y0,s=26,color=col[arm],zorder=3)
        ax.scatter(x1,y1,s=26,facecolor="white",edgecolor=col[arm],lw=1.3,zorder=3)
        if abs(x1-x0)+abs(y1-y0)>.3: ax.annotate("",xy=(x1,y1),xytext=(x0,y0),arrowprops=dict(arrowstyle="->",color=col[arm],lw=1,shrinkA=3,shrinkB=3))
        ax.text(x0+.5,y0+.35,arm[0],color=col[arm],fontsize=8,fontweight="bold")
    ax.set_title(a,fontsize=8.5); ax.set_xlabel("Clean-traffic FPR on test set (%)"); ax.set_xlim(2,46); ax.grid(color="#e5e5e5",lw=.5); ax.set_axisbelow(True)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
axs[0].set_ylabel("Attack-induced ASR (%)")
h=[plt.Line2D([],[],marker="o",ls="",color="#444",label="Validation-calibrated threshold"),plt.Line2D([],[],marker="o",ls="",mfc="white",color="#444",label="Common fixed threshold")]
axs[1].legend(handles=h,fontsize=7,frameon=False,loc="upper right")
plt.tight_layout(); plt.savefig(OUT+"fig3_threshold_shift.png",dpi=220); plt.close()
# Fig 4 trajectories
fig,axs=plt.subplots(1,3,figsize=(7.4,2.9),sharey=True)
for ax,a in zip(axs,att.values()):
    for arm in arms:
        g=D[(D.atk==a)&(D.arm==arm)].groupby("round")["attack_induced_asr_recalibrated"].mean()
        ax.plot(g.index,g.values,marker="o",ms=3,lw=1.3,color=col[arm],label=arm)
    ax.set_title(a,fontsize=8.5); ax.set_xlabel("Round"); ax.set_xticks(range(1,6)); ax.grid(color="#e5e5e5",lw=.5); ax.set_axisbelow(True)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
axs[0].set_ylabel("Attack-induced ASR (%)")
fig.legend(*axs[0].get_legend_handles_labels(),loc="lower center",ncol=6,fontsize=7,frameon=False)
plt.tight_layout(rect=(0,.08,1,1)); plt.savefig(OUT+"fig4_trajectories.png",dpi=220); plt.close()
print(D.columns.tolist()[:8], D.groupby("atk").size().to_dict())
