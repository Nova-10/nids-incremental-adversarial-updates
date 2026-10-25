"""Section 4 tables computed directly from the 15 per-run CSVs (five seeds x three attack settings).
Usage: python3 -I section4_tables.py <results_ext_dir> <out_dir>
Authority: per-seed CSVs. Intervals are 95% Student t (df=4), descriptive only."""
import sys, glob, json, numpy as np, pandas as pd
from scipy import stats
src, out = sys.argv[1], sys.argv[2]
df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{src}/unsw_nb15_ext_*_s*.csv"))], ignore_index=True)
assert len(df) == 450, len(df)
df = df[df.attack.isin(["FGSM-like","BIM-like","decision-only"])]
arms = ["frozen","static_adversarial","incremental_rehearsal","incremental_no_rehearsal","incremental_balanced_rehearsal","clean_continued"]
short = {"frozen":"A Frozen","static_adversarial":"B Static","incremental_rehearsal":"C Rehearsal","incremental_no_rehearsal":"D No rehearsal","incremental_balanced_rehearsal":"E Balanced","clean_continued":"F Control"}
attacks = ["FGSM-like","BIM-like","decision-only"]
T = stats.t.ppf(0.975, 4)
pp = ["clean_recall","clean_fpr","recalibrated_clean_recall","recalibrated_clean_fpr","attack_success_rate","attack_induced_asr",
      "asr_recalibrated","attack_induced_asr_recalibrated","pre_attack_detection_rate","pre_attack_detection_rate_recalibrated"]
for c in pp: df[c] = df[c]*100
def ms(x):
    x = np.asarray(x, float); m = x.mean(); h = T*x.std(ddof=1)/np.sqrt(len(x)); return m, h
# --- Table A: round-5 means with 95% half-width
r5 = df[df["round"]==5]
rows=[]
for a in attacks:
    for arm in arms:
        d = r5[(r5.attack==a)&(r5.arm==arm)].sort_values("seed")
        row={"attack":a,"arm":short[arm],"n":len(d)}
        for c in pp+["clean_auc","cumulative_new_evasion_labels","cumulative_train_and_attack_seconds"]:
            m,h = ms(d[c]); row[c]=m; row[c+"_hw"]=h
        rows.append(row)
A = pd.DataFrame(rows); A.to_csv(f"{out}/s4_round5_means.csv", index=False)
# --- Table B: paired contrasts (first minus second), mean, 95% t interval, seeds first lower
pairs = [("static_adversarial","frozen"),("static_adversarial","clean_continued"),("clean_continued","frozen"),
         ("incremental_rehearsal","frozen"),("incremental_rehearsal","static_adversarial"),
         ("incremental_no_rehearsal","frozen"),("incremental_balanced_rehearsal","frozen"),("incremental_balanced_rehearsal","static_adversarial")]
metrics = ["attack_induced_asr_recalibrated","asr_recalibrated","pre_attack_detection_rate_recalibrated","recalibrated_clean_recall","recalibrated_clean_fpr","clean_auc",
           "attack_success_rate","clean_fpr","clean_recall"]
rows=[]
for a in attacks:
    for x,y in pairs:
        dx = r5[(r5.attack==a)&(r5.arm==x)].sort_values("seed").reset_index(drop=True)
        dy = r5[(r5.attack==a)&(r5.arm==y)].sort_values("seed").reset_index(drop=True)
        assert (dx.seed.values==dy.seed.values).all()
        for m in metrics:
            diff = dx[m].values - dy[m].values
            mean,h = ms(diff)
            rows.append({"attack":a,"first":short[x],"second":short[y],"metric":m,"mean_diff":mean,"lo":mean-h,"hi":mean+h,"first_lower_in_seeds":int((diff<0).sum()),"n":5})
B = pd.DataFrame(rows); B.to_csv(f"{out}/s4_paired_contrasts.csv", index=False)
# --- per-round trajectories (means) for primary metric and clean metrics
rows=[]
for a in attacks:
    for arm in arms:
        for r in range(1,6):
            d = df[(df.attack==a)&(df.arm==arm)&(df["round"]==r)]
            rows.append({"attack":a,"arm":short[arm],"round":r,
                         "asr_attack_induced_cal":d.attack_induced_asr_recalibrated.mean(),
                         "fpr_cal":d.recalibrated_clean_fpr.mean(),"recall_cal":d.recalibrated_clean_recall.mean(),
                         "fpr_fixed":d.clean_fpr.mean(),"asr_fixed":d.attack_success_rate.mean()})
pd.DataFrame(rows).to_csv(f"{out}/s4_per_round.csv", index=False)
# --- resources
rows=[]
for a in attacks:
    for arm in arms:
        d = df[(df.attack==a)&(df.arm==arm)]
        perseed = d.groupby("seed").agg(adapt_queries=("decision_oracle_queries_this_round","sum")).reset_index()
        last = d[d["round"]==5].sort_values("seed")
        evalq = d.groupby("seed").agg(eval_q=("decision_oracle_queries","sum"), eval_q_cal=("decision_oracle_queries_recalibrated","sum")).reset_index()
        rows.append({"attack":a,"arm":short[arm],
            "labels_mean":last.cumulative_new_evasion_labels.mean(),"labels_min":last.cumulative_new_evasion_labels.min(),"labels_max":last.cumulative_new_evasion_labels.max(),
            "adapt_queries_mean":perseed.adapt_queries.mean(),"adapt_queries_min":perseed.adapt_queries.min(),"adapt_queries_max":perseed.adapt_queries.max(),
            "eval_queries_all_rounds_mean":evalq.eval_q.mean(),"eval_queries_cal_all_rounds_mean":evalq.eval_q_cal.mean(),
            "time_s_mean":last.cumulative_train_and_attack_seconds.mean(),"time_s_min":last.cumulative_train_and_attack_seconds.min(),"time_s_max":last.cumulative_train_and_attack_seconds.max()})
pd.DataFrame(rows).to_csv(f"{out}/s4_resources.csv", index=False)
# --- ranges for statements
sm={}
sm["test_fpr_cal_round5_range"]=(r5.recalibrated_clean_fpr.min(), r5.recalibrated_clean_fpr.max())
sm["val_fpr_range_all_rows"]=(float(df.recalibrated_validation_fpr.min()*100), float(df.recalibrated_validation_fpr.max()*100))
sm["initial_clean_fixed_fpr_round5_frozen"]=(r5[r5.arm=="frozen"].clean_fpr.min(), r5[r5.arm=="frozen"].clean_fpr.max())
json.dump(sm, open(f"{out}/s4_ranges.json","w"), indent=1)
print("done", sm)
