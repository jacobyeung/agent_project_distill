"""Reviewer checks on a spread of train captures, kit code read-only; writes only into this workspace.
(a) A2 (GT masks) at C64 vs kbox4 A2_gt_masks rows; (b) kit pose path vs deployed convert geometry c2w;
(c) CPU smoke of the V64 path on a synthetic 64-frame tower/cache (non-anchor depth and proposals copied from the
nearest anchor; crash and numbering check only, no value meaning)."""
import os, sys, json, time, collections, copy
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_ktow3/code')
from common import *
import numpy as np
import metrics
from replay import price, load_selector, selector_diagnostics, flagged_row, printed_frames
from evaluate import geometry, stored_tower, scored
from policy import captures
W = Path('/scratch/jjyeung/orch_n30/sb_ktrev/work')
ref = collections.defaultdict(dict)
with open('/scratch/jjyeung/orch_n30/sb_ktow3/inputs/kbox4/PER_ITEM.jsonl') as f:
    for s in f:
        r = json.loads(s)
        if r['arm'] == 'A2_gt_masks':
            ref[r['capture']][r['row_id']] = r
head = load_selector()
train = [c for c in captures('train') if c['canonical'] in ref]
pick = train[::10]
out = dict(a2=[], pose=[], v64=[])
for c in pick:
    own = npz(capdir(c, '/scratch/jjyeung/k1/own_170235/native/probe') / 'own.npz')
    tw = stored_tower(c); g, scale = geometry(tw, own); gt = npz(c['gt']['path'])
    # (a)
    got = price(c, g, gt=gt)
    for r in got:
        a = ref[c['canonical']][r['row_id']]
        boxes = {n: r['box_records'][ids[0]]['value'] for n, ids in r['box_bindings'].items() if len(ids) == 1}
        out['a2'].append(dict(capture=c['canonical'], row_id=r['row_id'], equal_pred=r['prediction'] == a['prediction'],
                              pred=r['prediction'], ref=a['prediction'],
                              members_equal={n: v for n, v in zip(r['names'], r['member_frames'])} == a['member_frames'],
                              boxes_equal=clean(boxes) == a['box']))
    # (b)
    geo = npz(capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'geometry.npz')
    kit = metrics.poses(metrics.c2w_pose(tw['raw_pose'][tw['anchor_slots']]), gt['c2w'], scale, gt['valid'])
    dep = metrics.poses(np.asarray(geo['camera_to_world'], float), gt['c2w'], float(geo['scale']), gt['valid'])
    keys = [k for k in kit if isinstance(kit[k], (int, float)) and kit[k] is not None and k in dep and dep[k] is not None]
    out['pose'].append(dict(capture=c['canonical'], max_abs_diff={k: abs(float(kit[k]) - float(dep[k])) for k in keys},
                            kit={k: kit[k] for k in keys}, deployed={k: dep[k] for k in keys}))
    # (c)
    try:
        anchors = list(map(int, tw['anchor_slots'])); near = [min(range(32), key=lambda i: abs(anchors[i] - s)) for s in range(64)]
        dense = dict(tw); dense['depth_grid'] = tw['depth_grid'][near]; dense['depth_conf_grid'] = tw['depth_conf_grid'][near]
        dense['depth_slots'] = np.arange(64)
        g64, s64 = geometry(dense, own)
        cache = read_json(capdir(c, '/scratch/jjyeung/k1/run_convert_2') / 'candidates.json')
        c64 = dict(phrases=cache['phrases'], frames={str(s): copy.deepcopy(cache['frames'][str(near[s])]) for s in range(64)})
        rows64 = price(c, g64, c64, 64, head=head); rows32 = price(c, g, cache, 32, head=head)
        lab = {r['row_id']: 1.0 for r in rows32}
        fl = [flagged_row(b, d) for b, d in zip(rows32, rows64)]
        sel = selector_diagnostics(c, c64, g64, 64, gt, head)
        bad = [r['row_id'] for r in rows64 if any(f > 32 for pf in r['printed_frames'] for f in pf)]
        best_ok = all(all(int(m) <= 32 for m in __import__('re').findall(r'best (\d+)', t)) for r in rows64 for t in r['ground'])
        out['v64'].append(dict(capture=c['canonical'], status='OK', rows=len(rows64), scale_equal=s64 == scale,
                               printed_over_32=bad, best_le_32=best_ok,
                               dense_member_max=max([max(m) for r in rows64 for m in r['member_frames'] if m] or [0]),
                               not_seen_dense_only=sum(r['dense_only_not_seen_operands'] for r in rows64),
                               responses64=[r['response'] for r in rows64], responses32=[r['response'] for r in rows32],
                               flagged=[r['response'] for r in fl], selector_top1=sel['top1']))
    except Exception as e:
        import traceback; out['v64'].append(dict(capture=c['canonical'], status='ERROR', error=repr(e), tb=traceback.format_exc()[-1500:]))
    print(c['canonical'], flush=True)
summary = dict(captures=[c['canonical'] for c in pick],
               a2_rows=len(out['a2']), a2_pred_equal=sum(x['equal_pred'] for x in out['a2']),
               a2_all_equal=sum(x['equal_pred'] and x['members_equal'] and x['boxes_equal'] for x in out['a2']),
               pose_max_abs_diff=max((v for x in out['pose'] for v in x['max_abs_diff'].values()), default=None),
               v64_ok=sum(x['status'] == 'OK' for x in out['v64']), v64_errors=[x for x in out['v64'] if x['status'] != 'OK'],
               v64_printed_over_32=sum(len(x.get('printed_over_32', [])) for x in out['v64']),
               v64_best_le_32=all(x.get('best_le_32', False) for x in out['v64'] if x['status'] == 'OK'),
               v64_dense_member_max=max((x.get('dense_member_max', 0) for x in out['v64']), default=0))
(W / 'check2.json').write_text(json.dumps(clean(dict(summary=summary, **out)), indent=1))
print(json.dumps(clean(summary), indent=1))
