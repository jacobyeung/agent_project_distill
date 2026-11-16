"""K1-refit logistic (unchanged setsel fit.fit_predict, portable_np, train rooms only) and the deployed MODELS.json
selector on the held-out candidates. Run with /scratch/jjyeung/envs/planner_local_v1/bin/python (sklearn 1.5.2)."""
import json, sys
import numpy as np
import sklearn
from sklearn.metrics import roc_auc_score, average_precision_score
sys.path.insert(0, '/scratch/jjyeung/orch_n30/b04_e2ehook/heads/selector')
import common as C
SETSEL = C.HERE / 'src118/scratch/jjyeung/orch_cd/grd_selector/work/setsel'
CURRENT = C.HERE / 'src118/scratch/jjyeung/orch_cd/devs1_masks/out/kit/work/vendor/MODELS.json'
sys.path.insert(0, str(SETSEL))
import fit, setlib as L


def probability(m, rows, key='features'):
    X = np.array([[r[key][f] for f in m['features']] for r in rows])
    z = ((X - np.array(m['mean'])) / m['scale']) @ np.array(m['coef']) + m['intercept']
    return 1 / (1 + np.exp(-np.clip(z, -700, 700)))


rows = C.load()
tr = [r for r in rows if r['split'] == 'train']
ho = [r for r in rows if r['split'] == 'heldout']
assert not {r['room'] for r in tr} & {r['room'] for r in ho}
p_refit, model, _ = fit.fit_predict(tr, ho, L.FEATS['portable_np'], 'logistic')
current = json.loads(CURRENT.read_text())['accept']
p_cur = probability(current, ho)
y = np.array([r['y'] for r in ho])
out = dict(versions=dict(sklearn=sklearn.__version__, numpy=np.__version__, python=sys.version),
           upstream={n: C.sha(SETSEL / n) for n in ('fit.py', 'setlib.py')}, current_models_sha256=C.sha(CURRENT),
           n_train=len(tr), n_heldout=len(ho),
           check_sklearn=dict(refit_auc=float(roc_auc_score(y, p_refit)), refit_ap=float(average_precision_score(y, p_refit))),
           heldout={C.key(r): dict(refit=float(a), current=float(b)) for r, a, b in zip(ho, p_refit, p_cur)})
for tag, p in (('refit', p_refit), ('current', p_cur)):
    out[tag] = dict(auc=C.auc(y, p), ap=C.ap(y, p), top1=C.top1(ho, p))
json.dump(out, open(C.HERE / f'work/logistic_heldout{C.TAG}.json', 'w'))
print(json.dumps({k: v for k, v in out.items() if k != 'heldout'}, indent=1))
