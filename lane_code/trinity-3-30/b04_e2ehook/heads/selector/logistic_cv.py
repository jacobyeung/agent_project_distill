"""Train-only reference: the K1 logistic (unchanged fit.fit_predict, portable_np) out-of-fold on the same 5
room-grouped folds train_selector.py uses. Held-out rows are not read. planner_local_v1 python."""
import json, random, sys
sys.path.insert(0, '/scratch/jjyeung/orch_n30/b04_e2ehook/heads/selector')
import common as C
sys.path.insert(0, str(C.HERE / 'src118/scratch/jjyeung/orch_cd/grd_selector/work/setsel'))
import fit, setlib as L
rows = C.load(splits=('train',))
rooms = sorted({r['room'] for r in rows}); rng = random.Random(C.SEED); rng.shuffle(rooms)
fold = {r: i % 5 for i, r in enumerate(rooms)}
oof_r, oof_p = [], []
for k in range(5):
    tr = [r for r in rows if fold[r['room']] != k]; te = [r for r in rows if fold[r['room']] == k]
    p, _, _ = fit.fit_predict(tr, te, L.FEATS['portable_np'], 'logistic')
    oof_r += te; oof_p += list(p)
y = [r['y'] for r in oof_r]
res = dict(auc=C.auc(y, oof_p), ap=C.ap(y, oof_p), top1=C.top1(oof_r, oof_p))
json.dump(res, open(C.HERE / f'work/logistic_train_oof{C.TAG}.json', 'w')); print(res)
