"""Train SelectorHead on K1 train candidates; pick the config by room-grouped CV inside train (held-out never read).

Usage: python -I -B train_selector.py OUT_DIR [--configs quick|full]
Selection rule (fixed before training): maximise out-of-fold AUC + out-of-fold top-1 over 5 room-grouped folds.
"""
import argparse, collections, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
from safetensors.torch import load_file, save_file
import common as C
from selector_head import SelectorHead, name_key, file_sha256

EMB = C.HERE / 'data/emb/NAME_EMB_SAM3.safetensors'
EMB_META = C.HERE / 'data/emb/NAME_EMB_SAM3.json'
FOLDS = 5
CONFIGS = [dict(hidden=h, wd=w, epochs=e, name_mode=m, lr=3e-3)
           for m in ('sam3', 'trigram', 'none') for h in (32, 64) for w in (1e-3, 1e-2) for e in (15, 40)]


def names_table():
    E = load_file(str(EMB))['name_emb']
    names = json.load(open(EMB_META))['names']
    return {n: E[i] for i, n in enumerate(names)}


def groups(rows, emb):
    by = collections.defaultdict(list)
    for r in rows:
        by[r['object_id']].append(r)
    out = []
    for oid in sorted(by):
        g = by[oid]
        out.append(dict(object_id=oid, room=g[0]['room'], name=g[0]['name'], rows=g,
                        x=torch.tensor([r['x'] for r in g], dtype=torch.float64),
                        y=torch.tensor([float(r['y']) for r in g]),
                        e=emb.get(name_key(g[0]['name']), torch.zeros(256))))
    return out


def fit(train_groups, cfg, seed=C.SEED):
    torch.manual_seed(seed); random.seed(seed)
    head = SelectorHead(hidden=cfg['hidden'], name_mode=cfg['name_mode'])
    X = torch.cat([g['x'] for g in train_groups])
    std = X.std(0)
    head.feat_mean.copy_(X.mean(0)); head.feat_std.copy_(torch.where(std > 1e-12, std, torch.ones_like(std)))
    opt = torch.optim.AdamW(head.parameters(), lr=cfg['lr'], weight_decay=cfg['wd'])
    rng = random.Random(seed)
    order = list(range(len(train_groups)))
    for _ in range(cfg['epochs']):
        rng.shuffle(order)
        for i in range(0, len(order), 16):
            loss = 0.
            n = 0
            for j in order[i:i + 16]:
                g = train_groups[j]
                logit, null = head.both(g['x'], g['e'], g['name'])
                loss = loss + torch.nn.functional.binary_cross_entropy_with_logits(logit, g['y'], reduction='sum')
                none = torch.tensor([float(g['y'].sum() == 0)])
                loss = loss + torch.nn.functional.binary_cross_entropy_with_logits(null, none, reduction='sum')
                n += len(g['y']) + 1
            opt.zero_grad(); (loss / n).backward(); opt.step()
    return head.eval()


@torch.no_grad()
def predict(head, gs):
    return [torch.sigmoid(head(g['x'], g['e'], g['name'])).tolist() for g in gs]


@torch.no_grad()
def slot_accuracy(head, gs):
    """Argmax over [candidates, null]: right when it picks a positive candidate, or null when none is positive."""
    ok = []
    for g in gs:
        k = int(torch.argmax(head.with_null(g['x'], g['e'], g['name'])))
        ok.append(bool(g['y'].sum() == 0) if k == len(g['y']) else bool(g['y'][k] == 1))
    return float(sum(ok) / len(ok))


def evaluate(gs, probs):
    rows = [r for g in gs for r in g['rows']]
    p = [v for ps in probs for v in ps]
    y = [r['y'] for r in rows]
    return dict(auc=C.auc(y, p), ap=C.ap(y, p), top1=C.top1(rows, p))


def room_folds(gs):
    rooms = sorted({g['room'] for g in gs})
    rng = random.Random(C.SEED)
    rng.shuffle(rooms)
    fold = {r: i % FOLDS for i, r in enumerate(rooms)}
    return [[g for g in gs if fold[g['room']] == k] for k in range(FOLDS)], [[g for g in gs if fold[g['room']] != k] for k in range(FOLDS)]


_CV = None


def _cv_one(cfg):
    torch.set_num_threads(1)
    te, tr = _CV
    oof_g, oof_p, slots = [], [], []
    for k in range(FOLDS):
        h = fit(tr[k], cfg)
        oof_g += te[k]; oof_p += predict(h, te[k]); slots.append(slot_accuracy(h, te[k]) * len(te[k]))
    return dict(evaluate(oof_g, oof_p), slot_acc=sum(slots) / len(oof_g))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    a = ap.parse_args()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    rows = C.load(splits=('train',))
    emb = names_table()
    gs = groups(rows, emb)
    te, tr = room_folds(gs)
    import multiprocessing as mp
    global _CV
    _CV = (te, tr)
    with mp.get_context('fork').Pool(8) as pool:
        results = pool.map(_cv_one, CONFIGS)
    cv = {}
    for cfg, m in zip(CONFIGS, results):
        cv[json.dumps(cfg, sort_keys=True)] = m
        print(f"{json.dumps(cfg, sort_keys=True):90s} auc={m['auc']:.4f} top1={m['top1']:.4f} slot={m['slot_acc']:.4f}", flush=True)
    chosen = max(cv, key=lambda k: (cv[k]['auc'] + cv[k]['top1'], k))
    cfg = json.loads(chosen)
    head = fit(gs, cfg)
    out = C.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    sd = {k: v.contiguous() for k, v in head.state_dict().items()}
    save_file(sd, str(out / 'selector_head.safetensors'))
    w = file_sha256(out / 'selector_head.safetensors')
    meta = dict(config=dict(cfg, n_hash=4096), seed=C.SEED, folds=FOLDS,
                selection_rule='max OOF AUC + OOF top-1, 5 room-grouped folds inside train',
                cv=cv, chosen=chosen, n_parameters=sum(p.numel() for p in head.parameters()),
                train=dict(candidates=len(rows), objects=len(gs), rooms=len({g['room'] for g in gs}), caps=str(C.CAPS)),
                name_embedding=dict(path=str(EMB), sha256=file_sha256(EMB), meta_sha256=file_sha256(EMB_META)),
                weights_sha256=w,
                code_sha256={n: file_sha256(C.HERE / n) for n in ('selector_head.py', 'train_selector.py', 'common.py')})
    (out / 'selector_head.json').write_text(json.dumps(meta, indent=1) + '\n')
    (out / 'selector_head.safetensors.sha256').write_text(f'{w}  selector_head.safetensors\n')
    print('CHOSEN', chosen, w, flush=True)


if __name__ == '__main__':
    main()
