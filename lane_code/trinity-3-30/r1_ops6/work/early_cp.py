"""r1_ops6 early-loss check for C' (resume at 201): STEP lines from ms_cp.sh on stdin.
Baseline = A's steps 186-200 four-rank means (median, MAD) from metrics_171377.jsonl 6934aafe (xfer/A_base.out).
ALARM: any non-finite stream; pose or pointing above median + max(0.5|m|, 6*1.4826*MAD) on two consecutive steps;
VQA above 2 x A's median on two consecutive steps (a lost restore would sit near the step-1 level 1.9). Routing reported only.
Exit 0 PASS (>=3 steps), 3 PENDING, 2 ALARM."""
import json,math,sys
BASE={"pose":[0.17362514999695122,0.005428779288195074],"vqa":[0.07336675647646018,0.0029393095265248803],"routing":[7.74195153141477e-05,3.5747777396011315e-06],"pointing":[0.431519818100071,0.04501032261242699]}
rows=[json.loads(l.split(' ',1)[1]) for l in sys.stdin if l.startswith('STEP ')]
rows=[r for r in rows if r['step']>=201]
prob=[];warn=[]
def thr(s):m,d=BASE[s];return m+max(0.5*abs(m),6*1.4826*d)
for i,r in enumerate(rows):
  for s in BASE:
    if not math.isfinite(r[s]):prob.append(f"step {r['step']} {s} non-finite")
  for s in ('pose','pointing'):
    if r[s]>thr(s):
      (prob if i>0 and rows[i-1][s]>thr(s) else warn).append(f"step {r['step']} {s} {r[s]:.4f} > {thr(s):.4f}")
  if r['vqa']>2*BASE['vqa'][0]:
    (prob if i>0 and rows[i-1]['vqa']>2*BASE['vqa'][0] else warn).append(f"step {r['step']} vqa {r['vqa']:.4f} > {2*BASE['vqa'][0]:.4f}")
v='ALARM' if prob else ('PASS' if len(rows)>=3 else 'PENDING')
print(json.dumps(dict(verdict=v,steps=[r['step'] for r in rows],problems=prob,warnings=warn,first=rows[:3],thresholds={s:thr(s) for s in ('pose','pointing')},vqa_limit=2*BASE['vqa'][0])))
sys.exit({'PASS':0,'PENDING':3,'ALARM':2}[v])
