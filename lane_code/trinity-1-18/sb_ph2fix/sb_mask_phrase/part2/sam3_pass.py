"""Mask phrase kit part 2, GPU pass. Written by the part 1 build and never executed by it (no GPU, no SAM 3 load there).

One SAM 3 pass over the 32 anchor frames of each of the 209 K1 training captures with priced rows. Per operand name it
calls, each phrase alone: the raw name (control, and the base of R_cond), the phrases the part 1 cross-fit chose in any
fold (W_exact: the alias called alone replaces the stored pool, which lost instances the stage-1 cache merged into the
raw name's above IoU 0.95) and the name's NEW_PHRASES.json phrases (W_new). `--all-aliases` adds every dictionary alias.
Each frame keeps the reader's K1 retention (stage1.sam3_detect: joint >= 0.05, cap 30, mask logit > 0;
retention='k1') and, when that set is empty, up to five queries with conditional score >= 0.5 (retention='cond', R_cond).

Output per capture: out/pool_part2/<digest(canonical)[:16]>/candidates.json in the stage-1 cache's format
(frames[slot].phrases[name] = presence of the raw call, all_instance_scores, instances[score, source_prompt,
source_presence, query, retention, mask RLE 480 x 640 column-major]) and PART2_RECEIPT.json beside it.

    bash part2/launch_gpu.sh --node-local 0 --mode step5
    bash part2/launch_gpu.sh --node-local 0 [--all-aliases]

step5 is the spec's dry-run step 5 and must PASS (out/pool_part2/STEP5.json) before `pass` runs. After the first 10
captures `pass` writes out/pool_part2/TIMING_RECEIPT.json with the projection of the whole pass; above 1.2 GPU-h it drops the new
phrases for the remaining captures (new_worth is then MISSING), and if the pass still projects above 1.2 GPU-h, or the
elapsed time reaches 1.2 GPU-h, it stops. A stop is reported in out/pool_part2/STOP.json and is not rerun.
"""
import sys
sys.dont_write_bytecode = True
from gate import check
if __name__ == '__main__':
    check(sys.argv[1])

import ast, hashlib, json, os, re, sys, time
from pathlib import Path
from staged_paths import local
from watchdog import bounded, call_watchdog
import numpy as np

HERE = Path(__file__).resolve().parents[1]
OUT = HERE/'out'/'pool_part2'
BOX = local('/scratch/jjyeung/orch_n30/sb_kbox4')
VENDOR = local('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam')
TREE = local('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449')
SOURCE_ROOT = local('/scratch/jjyeung/b01ec87a6f29b/d/s')
CHECKPOINT = local('/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt')
RECEIPT = VENDOR/'vendor/SAM3_RECEIPT.json'
CHECKPOINT_SHA = '9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e'
IDS = local('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
K1 = local('/scratch/jjyeung/k1/run_convert_2')
NEW = HERE/'part2/NEW_PHRASES.json'; NEW_SHA = HERE/'part2/NEW_PHRASES.sha256'
DECISION = HERE/'out/DECISION.json'
FLOOR, CAP, COND, COND_CAP = .05, 30, .5, 5
HARD_GPU_H, TIMED = 1.2, 10
CONTRACT = dict(joint_floor=FLOOR, cap=CAP, cond_floor=COND, cond_cap=COND_CAP, mask='bilinear logits > 0', resolution=1008,
                dtype='bf16', prompts='each phrase alone')
STEP5_CAPTURE = 'arkitscenes/41048124'
SCORE_TOL, IOU_MIN = .02, .99


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def evidence_json(value, **kwargs):
    inputs = [Path(__file__), HERE/'part2/gate.py', HERE/'part2/watchdog.py',
              HERE/'part2/BARS_PART2.json', NEW, NEW_SHA, DECISION, IDS,
              BOX/'pinned_train.json', RECEIPT]
    if os.environ.get('PART2_STAGED') == '1':
        inputs.append(HERE.parent/'out/STAGING_PART2.json')
    value['input_sha256'] = {str(p): sha(p) for p in inputs}
    value['input_sha256'][str(CHECKPOINT)] = CHECKPOINT_SHA
    return json.dumps(value, **kwargs)


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()


def rle_encode(m):
    """The stage-1 cache's RLE: column-major runs, first run counts zeros."""
    flat = np.asarray(m, bool).ravel(order='F')
    change = np.flatnonzero(flat[1:] != flat[:-1])+1
    runs = np.diff(np.concatenate([[0], change, [flat.size]])).tolist()
    if flat.size and flat[0]:
        runs = [0]+runs
    return dict(size=list(m.shape), counts=[int(r) for r in runs])


def rle_decode(rle):
    h, w = rle['size']
    return np.repeat(np.arange(len(rle['counts'])) % 2 == 1, rle['counts']).reshape((h, w), order='F')


def alias_table():
    src = (VENDOR/'variantlib.py').read_text()
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.Assign)
                and any(getattr(t, 'id', None) == 'ALIASES' for t in n.targets))
    return ast.literal_eval(node.value)


def chosen_phrases():
    """Non-raw phrases the part 1 cross-fit chose for any arm in any fold (W_exact reruns them alone)."""
    d = json.loads(DECISION.read_text())
    out = {}
    for arm in ('W1', 'W2', 'W2c'):
        for fold, names in d['fold_choices'][arm].items():
            for n, v in names.items():
                out.setdefault(n, set()).add(v.split(':', 1)[1])
    return {n: sorted(v) for n, v in out.items()}


def plan(all_aliases=False):
    check('plan')
    """Captures with priced rows and, per capture, {name: [phrases]} with the raw name first."""
    assert sha(NEW) == NEW_SHA.read_text().split()[0], 'NEW_PHRASES.json changed after it was frozen'
    new = json.loads(NEW.read_text())['phrases']; table = alias_table(); chosen = chosen_phrases()
    ids = set(IDS.read_text().split())
    manifest = json.loads((BOX/'pinned_train.json').read_text())
    caps = [c for c in manifest['captures'] if any(r['id'] in ids for r in c['rows'])]
    assert len(caps) == 209 and all(c['k1_split'] == 'train' for c in caps)
    out = []
    for c in sorted(caps, key=lambda c: c['canonical']):
        names = sorted({n for r in c['rows'] if r['id'] in ids for n in r['operands']})
        calls = {}
        for n in names:
            extra = (sorted(set(table.get(n, [])) - {n}) if all_aliases else chosen.get(n, [])) + new.get(n, [])
            calls[n] = [n]+[w for w in dict.fromkeys(extra) if w != n]
        out.append((c, calls))
    return out


def frames_of(c):
    from PIL import Image
    images = []
    for slot in c['anchor_slots']:
        rec = c['dense_frames'][slot]
        if sha(local(rec['path'])) != rec['sha256']:
            raise ValueError('frame content differs from pinned_train.json: '+rec['path'])
        images.append(Image.open(local(rec['path'])).convert('RGB'))
    assert len(images) == 32
    return images


def require_go():
    if os.environ.get('PART2_GO') != '1':
        sys.exit('PART2_GO=1 is required: part 2 runs only on a GPU placed by swarm_build3')


@bounded
def tower():
    require_go()
    import torch
    if not torch.cuda.is_available():
        sys.exit('part 2 needs CUDA; it never runs on CPU')
    if not (OUT/'RUNNING').is_file() or 'PART2_DEADLINE_MONOTONIC' not in os.environ or os.environ.get('PART2_STAGED') != '1':
        sys.exit('REFUSED: use part2/launch_gpu.sh for GPU execution')
    sys.path[:0] = [str(SOURCE_ROOT), str(VENDOR/'vendor'), str(BOX/'reader_src'), str(TREE)]
    from sam3_tower import Sam3Tower
    if sha(CHECKPOINT) != CHECKPOINT_SHA:
        raise ValueError('checkpoint sha256 differs')
    t = Sam3Tower(dict(checkpoint_path=str(CHECKPOINT), receipt_path=str(RECEIPT), source_root=str(SOURCE_ROOT),
                       device='cuda', precision='bf16'))
    torch.set_num_threads(8)
    t._load()
    return t


@bounded
def detect(t, features, phrase):
    """stage1.sam3_detect's forward and K1 retention, plus R_cond's conditional-score queries in empty frames."""
    import torch
    import torch.nn.functional as TF
    from e2e_reader.stage1 import name_key, K1_CONTRACT
    assert (K1_CONTRACT['joint_floor'], K1_CONTRACT['cap']) == (FLOOR, CAP)
    with torch.inference_mode(), t._autocast():
        text = t._backend.model.backbone.forward_text([name_key(phrase)], device=str(t.device))
    out = []
    for stored, (h, w) in zip(features.frames, features.sizes):
        backbone = {k: (v.to(t.device) if hasattr(v, 'to') else [x.to(t.device) for x in v]) for k, v in stored.items()}
        backbone['vision_features'] = backbone['backbone_fpn'][-1]
        backbone.update(text)
        with torch.inference_mode(), t._autocast():
            raw = t._backend.model.forward_grounding(backbone_out=backbone, find_input=t._backend.find_stage,
                                                     geometric_prompt=t._backend.model._get_dummy_prompt(), find_target=None)
        scores = raw['pred_logits'].sigmoid().reshape(-1).float()
        presence = float(raw['presence_logit_dec'].sigmoid().item())
        joint = scores*presence
        order = torch.argsort(scores, descending=True, stable=True)
        keep = order[joint[order] >= FLOOR][:CAP].tolist()
        cond = [] if keep else order[scores[order] >= COND][:COND_CAP].tolist()
        native = raw['pred_masks'].reshape(-1, *raw['pred_masks'].shape[-2:])
        inst = []
        for i, kind in [(i, 'k1') for i in keep]+[(i, 'cond') for i in cond]:
            m = (TF.interpolate(native[i][None, None].float(), (h, w), mode='bilinear', align_corners=False)[0, 0] > 0).cpu().numpy()
            inst.append(dict(score=float(scores[i]), joint_score=float(joint[i]), query=int(i), retention=kind, source_prompt=phrase,
                             source_presence=presence, mask=rle_encode(m)))
        out.append(dict(presence=presence, all_instance_scores=[float(s) for s in scores.cpu().tolist()], instances=inst))
        del raw, backbone
    return out


def capture(t, c, calls):
    """One encode of the 32 anchors, then one call per distinct phrase. Returns the record and its timings."""
    start = time.monotonic()
    with call_watchdog():
        feats = t.encode(frames_of(c))
    encoded = time.monotonic()
    runs, frames = {}, {str(s): dict(size=list(feats.sizes[s][::-1]), phrases={}) for s in range(32)}
    for n, phrases in calls.items():
        for w in phrases:
            if w not in runs:
                runs[w] = detect(t, feats, w)
        for s in range(32):
            frames[str(s)]['phrases'][n] = dict(presence=runs[n][s]['presence'], all_instance_scores=runs[n][s]['all_instance_scores'],
                                                instances=[i for w in phrases for i in runs[w][s]['instances']],
                                                phrase_presence={w: runs[w][s]['presence'] for w in phrases})
    done = time.monotonic()
    rec = dict(capture=c['canonical'], contract=CONTRACT, phrases=sorted(calls), calls=calls, frame_indices=list(c['anchor_indices']),
               frames=frames)
    return rec, dict(seconds=done-start, encode=encoded-start, detect=done-encoded, distinct_calls=len(runs))


def distinct(calls, new=None):
    return len({w for n, ws in calls.items() for w in ws if new is None or w not in new.get(n, [])})


def iou(a, b):
    u = np.count_nonzero(a | b)
    return np.count_nonzero(a & b)/u if u else 1.


def step5(name=STEP5_CAPTURE):
    """Rerun each operand's raw name on one capture; the K1 part must equal the reader's own sam3_detect and reproduce
    the stored raw instances (score within bf16 tolerance, mask IoU >= 0.99)."""
    check('step5')
    t = tower()
    from e2e_reader.stage1 import sam3_detect
    c, calls = next((c, k) for c, k in plan() if c['canonical'] == name)
    with call_watchdog():
        feats = t.encode(frames_of(c))
    cache = json.loads((K1/digest(c['canonical'])[:16]/'candidates.json').read_text())
    report, ok = [], True
    for n in calls:
        mine = detect(t, feats, n)
        with call_watchdog():
            reader = sam3_detect(t, feats, n)
        for s in range(32):
            k1 = [i for i in mine[s]['instances'] if i['retention'] == 'k1']
            same_reader = len(k1) == len(reader[s]) and all(abs(a['score']-b['score']) <= 1e-6 for a, b in zip(k1, reader[s]))
            rec = cache['frames'][str(s)]['phrases'].get(n) or dict(instances=[], presence=0.)
            stored = [p for p in rec['instances'] if p.get('source_prompt', n) == n]
            pres = float(stored[0].get('source_presence', rec['presence'])) if stored else float(rec['presence'])
            stored = [p for p in sorted(stored, key=lambda p: -float(p['score'])) if float(p['score'])*pres >= FLOOR][:CAP]
            matched = 0; boundary = 0
            for rank, p in enumerate(stored):
                m = rle_decode(p['mask'])
                best = max((iou(m, rle_decode(i['mask'])) for i in k1 if abs(i['score']-float(p['score'])) <= SCORE_TOL), default=0.)
                if best >= IOU_MIN:
                    matched += 1
                elif abs(float(p['score'])*pres-FLOOR) <= SCORE_TOL*pres or (len(stored) == CAP and rank >= CAP-3):
                    boundary += 1
            passed = same_reader and matched+boundary == len(stored) and abs(mine[s]['presence']-pres) <= SCORE_TOL
            ok &= passed
            report.append(dict(name=n, slot=s, stored=len(stored), rerun=len(k1), matched=matched, boundary=boundary,
                               presence=(pres, mine[s]['presence']), same_as_reader=same_reader, passed=passed))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'STEP5.json').write_text(evidence_json(dict(status='PASS' if ok else 'FAIL', capture=name, tolerance=dict(score=SCORE_TOL, iou=IOU_MIN),
                                                  frames=report, tower_receipt=t.receipt), indent=1))
    print('step5', 'PASS' if ok else 'FAIL')
    return ok


def projection(timed, remaining, new, elapsed_s):
    """GPU-h for the whole pass: elapsed plus, per remaining capture, the mean encode time and the mean time per call
    times its distinct calls; with and without the new phrases."""
    enc = float(np.mean([x['encode'] for x in timed]))
    per_call = sum(x['detect'] for x in timed)/max(1, sum(x['distinct_calls'] for x in timed))
    full = (elapsed_s+sum(enc+per_call*distinct(k) for k in remaining))/3600
    without = (elapsed_s+sum(enc+per_call*distinct(k, new) for k in remaining))/3600
    return dict(encode_s_per_capture=enc, s_per_call=per_call, s_per_prompt_frame=per_call/32, projected_gpu_h=full,
                projected_gpu_h_without_new=without, drop_new=full > HARD_GPU_H, stop=without > HARD_GPU_H)


def stop(reason, **kw):
    (OUT/'STOP.json').write_text(evidence_json(dict(reason=reason, hard_stop_gpu_h=HARD_GPU_H, **kw), indent=1))
    sys.exit(f'stopped ({reason}); reported in out/pool_part2/STOP.json, not rerun')


def run(all_aliases=False):
    check('pass')
    require_go()
    gate = json.loads((OUT/'STEP5.json').read_text())
    assert gate['status'] == 'PASS', 'dry-run step 5 has not passed'
    t = tower(); todo = plan(all_aliases); new = json.loads(NEW.read_text())['phrases']
    started = float(os.environ['PART2_DEADLINE_MONOTONIC']) - HARD_GPU_H*3600
    timed = []; drop_new = False
    for i, (c, calls) in enumerate(todo):
        dest = OUT/digest(c['canonical'])[:16]
        if (dest/'PART2_RECEIPT.json').exists():
            continue
        if drop_new:
            calls = {n: [w for w in ws if w not in new.get(n, [])] for n, ws in calls.items()}
        rec, tm = capture(t, c, calls); timed.append(dict(tm, capture=c['canonical']))
        dest.mkdir(parents=True, exist_ok=True)
        (dest/'candidates.json').write_text(evidence_json(rec, separators=(',', ':')))
        (dest/'PART2_RECEIPT.json').write_text(evidence_json(dict(capture=c['canonical'], timing=tm, calls=calls, new_phrases_dropped=drop_new,
                                                               candidates_sha256=sha(dest/'candidates.json'), new_phrases_sha256=sha(NEW),
                                                               bars_part2_sha256=sha(HERE/'part2/BARS_PART2.json'), tower_receipt=t.receipt), indent=1))
        elapsed = time.monotonic()-started
        if elapsed/3600 >= HARD_GPU_H:
            stop('elapsed', elapsed_gpu_h=elapsed/3600, done=len(timed), captures=len(todo))
        if len(timed) == TIMED:
            p = projection(timed, [k for _, k in todo[i+1:]], new, elapsed)
            (OUT/'TIMING_RECEIPT.json').write_text(evidence_json(dict(p, captures_timed=timed, captures=len(todo), hard_stop_gpu_h=HARD_GPU_H,
                                                                        all_aliases=all_aliases, new_phrases_sha256=sha(NEW)), indent=1))
            drop_new = p['drop_new']
            if p['stop']:
                stop('projection', **p)
    (OUT/'PASS_COMPLETE.json').write_text(evidence_json(dict(captures=len(todo), seconds=sum(x['seconds'] for x in timed), new_phrases_dropped=drop_new,
                                                          all_aliases=all_aliases), indent=1))


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'step5':
        sys.exit(0 if step5(*(sys.argv[2:3] or [STEP5_CAPTURE])) else 1)
    elif mode == 'pass':
        run('--all-aliases' in sys.argv)
    elif mode == 'plan':
        p = plan('--all-aliases' in sys.argv)
        print(json.dumps(dict(captures=len(p), calls=sum(len({w for ws in k.values() for w in ws}) for _, k in p))))
    else:
        sys.exit('mode: step5 | pass | plan')
