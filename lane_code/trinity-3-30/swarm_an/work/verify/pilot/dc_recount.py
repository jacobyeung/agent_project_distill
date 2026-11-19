import sys, re, json, collections
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
import numpy as np
def auc(y, x):
    y = np.asarray(y, bool); x = np.asarray(x, float); p = x[y]; n = x[~y]
    return float(np.mean((p[:, None] > n[None, :]) + 0.5 * (p[:, None] == n[None, :])))
T = ['camera_displacement', 'camera_rotation', 'camera_movement_direction']
shown = 0
for step in (544, 200):
    rows = K.routed(step, types=T)
    for t in T:
        R = [r for r in rows if r['type'] == t]; sc = 100 * np.mean([r['score'] for r in R])
        if t == T[2]:
            print(step, t, len(R), 'score %.2f' % sc, 'wrong', sum(r['score'] < 1 for r in R), 'calls', sum(1 for r in R if r['calls'])); continue
        p0 = np.array([float(r['answer']) for r in R]); g0 = np.array([float(r['gt']) for r in R]); p, g = abs(p0), abs(g0); e_signed = None
        with np.errstate(divide='ignore', invalid='ignore'): e = np.where(g0 != 0, abs(p0 - g0) / abs(g0), np.where(p0 != 0, 9.0, 0.0))
        thr = 0.5 if t == T[0] else 20.0
        fl = p < thr
        # does the answer equal the printed response value?
        same = 0
        for r in R:
            resp = ' '.join(c['response'] or '' for c in r['calls'])
            same += (('%g' % float(r['answer'])) in resp) or (str(r['answer']) in resp)
        print(step, t, len(R), 'score %.2f' % sc, 'wrong>.25', int((e > .25).sum()), 'wrong>.5', int((e > .5).sum()), 'AUC(-magnitude) %.3f / %.3f' % (auc(e > .25, -p), auc(e > .5, -p)),
              '| printed<%g: %d flagged, %d wrong>.25, %d wrong>.5' % (thr, fl.sum(), (fl & (e > .25)).sum(), (fl & (e > .5)).sum()), '| truth<%g: %d' % (thr, (g < thr).sum()), '| answer found in response', same, 'calls', sum(1 for r in R if r['calls']))
        if step == 200 and shown < 3:
            r = sorted(R, key=lambda r: r['score'])[0]; shown += 1
            print('   example', r['id'], '| q:', r['question'][:160], '| gt', r['gt'], '| answer', r['answer'], '| response:', (r['calls'][0]['response'] or '')[:200])
