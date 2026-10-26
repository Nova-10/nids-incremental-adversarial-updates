"""Analysis of the budget-matched experiment (design fixed in DESIGN.md before any run).
Usage: python3 analyze_matched.py <results_dir> <out_dir>"""
import sys, glob, json, numpy as np, pandas as pd
from scipy import stats
src, out = sys.argv[1], sys.argv[2]
import os; os.makedirs(out, exist_ok=True)
df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f'{src}/*.csv'))], ignore_index=True)
SHORT = {'frozen':'A Frozen','static_adversarial':'B Static','incremental_rehearsal':'C Rehearsal','incremental_no_rehearsal':'D No rehearsal',
         'incremental_balanced_rehearsal':'E Balanced','clean_continued':'F Control','matched_one_time':'M1 One-time matched',
         'matched_one_time_e10':'M1-e10 One-time matched (10 ep)','matched_incremental':'M2 Incremental matched','static_decision_trained':'B-dec Static (decision-trained)','matched_one_time_seq':'M1-seq One-time matched (5 sequential updates)','matched_incremental_full':'M2-full Incremental (B recipe)'}
df['arm_s'] = df.arm.map(SHORT)
PCT = ['attack_induced_asr_recalibrated','pre_attack_detection_rate_recalibrated','asr_recalibrated','recalibrated_clean_recall',
       'recalibrated_clean_fpr','recalibrated_clean_f1','attack_induced_asr','pre_attack_detection_rate','attack_success_rate','clean_recall','clean_fpr']
for c in PCT: df[c] = df[c] * 100
def ci(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    return x.mean(), (stats.t.ppf(.975, n-1) * x.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan), n
r5 = df[df['round'] == 5]
rows = []
for (att, arm), g in r5.groupby(['attack','arm_s']):
    row = {'attack':att,'arm':arm,'n_seeds':g.seed.nunique()}
    for c in PCT + ['clean_auc','adversarial_training_examples_cumulative']:
        m, h, n = ci(g[c]); row[c] = m; row[c+'_hw'] = h
    rows.append(row)
means = pd.DataFrame(rows); means.to_csv(f'{out}/round5_means.csv', index=False)
CONTRASTS = [('M1 One-time matched','M2 Incremental matched'),('M1-e10 One-time matched (10 ep)','M2 Incremental matched'),
             ('B Static','M1 One-time matched'),('B Static','B-dec Static (decision-trained)'),
             ('B Static','A Frozen'),('B Static','C Rehearsal'),('F Control','A Frozen'),('B Static','F Control'),
             ('M2 Incremental matched','A Frozen'),('M1 One-time matched','A Frozen'),('M1-e10 One-time matched (10 ep)','A Frozen'),
             ('M2 Incremental matched','C Rehearsal'),('M1-seq One-time matched (5 sequential updates)','M2 Incremental matched'),('M1 One-time matched','M1-seq One-time matched (5 sequential updates)'),('M1-seq One-time matched (5 sequential updates)','A Frozen'),('M2-full Incremental (B recipe)','B Static'),('M2-full Incremental (B recipe)','M2 Incremental matched'),('M2-full Incremental (B recipe)','M1-e10 One-time matched (10 ep)'),('M2-full Incremental (B recipe)','A Frozen'),('M2-full Incremental (B recipe)','B-dec Static (decision-trained)'),('M2-full Incremental (B recipe)','F Control')]
METRICS = ['attack_induced_asr_recalibrated','pre_attack_detection_rate_recalibrated','asr_recalibrated','recalibrated_clean_recall','recalibrated_clean_fpr','clean_auc']
crow = []
for att, g in r5.groupby('attack'):
    piv = {m: g.pivot_table(index='seed', columns='arm_s', values=m) for m in METRICS}
    for a, b in CONTRASTS:
        for m in METRICS:
            p = piv[m]
            if a not in p or b not in p: continue
            d = (p[a] - p[b]).dropna(); n = len(d)
            if n == 0: continue
            mean, hw, _ = ci(d)
            lower = int((d < 0).sum()); higher = int((d > 0).sum()); ties = n - lower - higher
            sign_p = stats.binomtest(lower, lower + higher, .5).pvalue if lower + higher > 0 else np.nan
            crow.append({'attack':att,'first':a,'second':b,'metric':m,'n':n,'mean_diff':mean,'lo':mean-hw,'hi':mean+hw,
                         'first_lower':lower,'first_higher':higher,'ties':ties,'sign_test_p_two_sided':sign_p})
pd.DataFrame(crow).to_csv(f'{out}/paired_contrasts.csv', index=False)
traj = df.groupby(['attack','arm_s','round'])[['attack_induced_asr_recalibrated','recalibrated_clean_fpr','recalibrated_clean_recall']].mean().reset_index()
traj.to_csv(f'{out}/per_round_means.csv', index=False)
json.dump({'seeds': sorted(df.seed.unique().tolist()), 'runs': int(df.groupby(['seed','attack']).ngroups), 'rows': int(len(df))}, open(f'{out}/coverage.json','w'), indent=1)
print('ok', len(means), len(crow))
