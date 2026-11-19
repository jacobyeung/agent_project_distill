"""Step-N rerun prompts from the step-200 prompts (lane swarm_an). usage: make_prompts_next.py --step 400 [--only id,id]
Writes B/events/swarm_an/prompts/m<step>_<id>.md = the m200 prompt with a rerun block placed before the assignment, and
work/queue_m<step>.txt for run_queue.sh. Add the step's roots to kit/roots.json first (direct, facing, vsti); the routed read
needs its return wired into san_kit.routed() before the three routed analysts and cot_cost run."""
import argparse, io, os
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=int, default=400); ap.add_argument('--only', default=''); a = ap.parse_args()
N = a.step
P = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_an/prompts/'
REC = '/data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md'
IDS = ['count', 'dir_easy', 'dir_med', 'dir_hard', 'rel_dist', 'app_order', 'route', 'size', 'facing', 'vsti_a', 'vsti_b', 'vsti_c',
       'routed_dist', 'routed_disp', 'routed_rot', 'cot_cost', 'rows_a', 'rows_b']
SKIP = {'rows_a', 'rows_b'}          # training-row audits do not depend on the checkpoint
SEC = {'count': '2, 10.2, 10.6', 'dir_easy': '2, 10.3, 10.8', 'dir_med': '2, 10.3, 10.8', 'dir_hard': '2, 10.3, 10.8', 'rel_dist': '2, 10.10',
       'app_order': '2, 10.4, 10.11', 'route': '2, 10.12', 'size': '2, 10.9', 'facing': '2, 10.3, 10.8', 'vsti_a': '2, 10.5, 10.13',
       'vsti_b': '2, 10.5, 10.13', 'vsti_c': '2, 10.5, 10.13', 'routed_dist': '3, 10.1, 10.7, 10.14', 'routed_disp': '3, 10.15',
       'routed_rot': '3, 10.15', 'cot_cost': '4'}
BLOCK = u'''## This run: the same analysis on step %(N)d (rerun)
The assignment below was written for step 200. You now analyse **step %(N)d** of the same leg (R1, run 673bc60f) as the new checkpoint:
- Wherever the text below loads or names step 200 as the new checkpoint, load step %(N)d instead: `K.direct('R1', %(N)d, ...)`, `K.facing('R1', %(N)d, ...)`, `K.vsti('R1', %(N)d)`, `K.routed(%(N)d, ...)`. Step 200 (`'R1', 200`) and step 544 (`'S1', 544`) stay available and are your two comparisons. If a loader raises for step %(N)d, say so in the report's first line and analyse what loads.
- The verified step-200 result for your type is in `%(REC)s`, sections %(SEC)s (read those sections once, by line range; the file is about 330 lines). Use its mode names and definitions so that counts compare; add a mode only when step %(N)d shows one that step 200 did not have.
- Counts quoted in the assignment text below are step-200 counts; recompute every one of them at step %(N)d.
- The report keeps its order, with these additions: in section 2 every mode has three columns (step 544, step 200, step %(N)d: wrong items and type points); section 4 becomes "Step 200 against step %(N)d" (right to wrong, wrong to right, wrong to wrong, and what changed in the trace for the flipped items) followed by one line on step 544 against step %(N)d; add a section "Gates" answering, with counts, each of these that applies to your type: force-closed items (B2048 `forced_close`) at the three steps; away traces that omit the half turn and their opening line; calls placed, by unit for distance; traces citing a frame above 32; overcounts at a truth of 2 on R0-dev multiple-category counting; items whose answer departs from the trace's conclusion.
- The training rows changed between the steps only by the removal of the first-seen list counting rows (qids in `/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json`); say for each change in the traces whether that removal can explain it.

'''
ids = [i for i in IDS if i not in SKIP and (not a.only or i in a.only.split(','))]
for i in ids:
    s = io.open(P + 'm200_%s.md' % i, encoding='utf-8').read()
    k = s.index('## Your assignment')
    t = s[:k] + BLOCK % dict(N=N, REC=REC, SEC=SEC[i]) + s[k:]
    t = t.replace('(m200)', '(m%d)' % N, 1)
    io.open(P + 'm%d_%s.md' % (N, i), 'w', encoding='utf-8').write(t)
q = '/scratch/jjyeung/orch_n30/swarm_an/work/queue_m%d.txt' % N
io.open(q, 'w').write(u'\n'.join('m%d_%s' % (N, i) for i in ids) + u'\n'); print(len(ids), 'prompts;', q)
