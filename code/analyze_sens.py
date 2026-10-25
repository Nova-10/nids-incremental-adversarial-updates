"""Pre-declared one-factor-at-a-time sensitivity (FGSM-like). Every configuration is reported; none is selected.
Usage: python3 analyze_sens.py <sens_dir> <main_dir> <out_dir>"""
import sys, glob, os, re, numpy as np, pandas as pd
from scipy import stats
sens, main, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
frames = []
for f in glob.glob(f'{sens}/*.csv'):
    d = pd.read_csv(f); d['config'] = re.search(r's_(\w+?)_fgsm', f).group(1); frames.append(d)
for f in glob.glob(f'{main}/unsw_nb15_m_fgsm_s*.csv'):
    d = pd.read_csv(f); d['config'] = 'default'; frames.append(d)
df = pd.concat(frames); df = df[df['round'] == 5]
ARMS = {'incremental_rehearsal':'C','matched_one_time':'M1','matched_one_time_e10':'M1-e10','matched_incremental':'M2','frozen':'A'}
df = df[df.arm.isin(ARMS)]; df['a'] = df.arm.map(ARMS)
for c in ['attack_induced_asr_recalibrated','recalibrated_clean_fpr','recalibrated_clean_recall','pre_attack_detection_rate_recalibrated']: df[c] *= 100
rows = []
for cfg, g in df.groupby('config'):
    for a, h in g.groupby('a'):
        x = h.attack_induced_asr_recalibrated.to_numpy(); n = len(x)
        rows.append({'config':cfg,'arm':a,'n':n,'asr':x.mean(),'asr_hw':stats.t.ppf(.975,n-1)*x.std(ddof=1)/np.sqrt(n),
                     'fpr':h.recalibrated_clean_fpr.mean(),'recall':h.recalibrated_clean_recall.mean(),'pre_det':h.pre_attack_detection_rate_recalibrated.mean()})
    p = g.pivot_table(index='seed', columns='a', values='attack_induced_asr_recalibrated')
    for x, y in [('M1','M2'),('M1-e10','M2'),('M2','A'),('C','A')]:
        d = (p[x]-p[y]).dropna(); n=len(d); hw=stats.t.ppf(.975,n-1)*d.std(ddof=1)/np.sqrt(n)
        rows.append({'config':cfg,'arm':f'{x} - {y}','n':n,'asr':d.mean(),'asr_hw':hw,'first_lower':int((d<0).sum()),'first_higher':int((d>0).sum())})
pd.DataFrame(rows).to_csv(f'{out}/sensitivity_round5.csv', index=False); print('ok')
