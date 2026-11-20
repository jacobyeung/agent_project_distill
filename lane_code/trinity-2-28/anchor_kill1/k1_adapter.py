"""Reconstruct frozen K1 raw-name pools on CPU; write diagnostic rows only.

All writes stay beside this file. Inputs are read only from node-local scratch.
Run with the staged Python environment, PYTHONDONTWRITEBYTECODE=1, and one BLAS thread.
"""
import argparse
import collections
import gzip
import hashlib
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage
import torch

W = Path(__file__).resolve().parent
N = W.parent
BOX = W/'k1_inputs/orch_n30/sb_kbox4'
PAY = N/'sb_ph2fix/payload/files'
TREE_ORIG = Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449')
TREE = PAY/str(TREE_ORIG).lstrip('/')
FALLBACK = N/'reads228/kit/A10b/src/tree'
SEL = N/'reads228/kit/A10b/src/b/heads/selector'
sys.path[:0] = [str(BOX), str(BOX/'reader_src'), str(TREE), str(FALLBACK), str(SEL), str(SEL/'sl118')]
from student_pilot import routed_features as F
from e2e_reader import geometry as GE, grounding as G
from selector_head import load_head
import pricing
import math_v2
from anchor_analysis import a3x, best_anchor, neighbor_anchor, digest

pricing.fusion_box = math_v2.fusion_box
torch.set_num_threads(1)
PINS = {}
AUDIT = {}
EXPECTED = json.loads((N/'sb_cachk/out/v2/seeds/SEEDS.json').read_text())['input_sha256']


def read(path, expected=None):
    p = Path(path)
    assert str(p.resolve()).startswith('/scratch/'), p
    data = p.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if expected is not None:
        assert actual == expected, ('hash mismatch', str(p), actual, expected)
    PINS[str(p)] = dict(sha256=actual, bytes=len(data))
    return data


def origin(path):
    """Map a named origin to the transferred tree, a staged payload, or its local path."""
    p = Path(path)
    for q in [W/'k1_inputs'/p.relative_to('/scratch/jjyeung'), PAY/str(p).lstrip('/'), p]:
        if q.is_file():
            return q
    raise FileNotFoundError(path)


def pinned(path):
    return read(origin(path), EXPECTED[str(path)])


def load_json(path, expected=None):
    b = read(path, expected)
    return json.loads(gzip.decompress(b) if str(path).endswith('.gz') else b)


def write(name, value):
    (W/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def decode(rle):
    counts = np.asarray(rle['counts'], np.int64)
    h, w = rle['size']
    assert np.all(counts >= 0) and counts.sum() == h*w
    return np.repeat(np.arange(len(counts)) % 2 == 1, counts).reshape((h, w), order='F')


def raw_name(cache, name):
    """The exact sb_kbox4.predicted.cache_detect retention and resize contract."""
    out = []
    for slot in range(32):
        record = cache['frames'][str(slot)]['phrases'].get(name)
        if record is None:
            out.append([])
            continue
        entries = [p for p in record.get('instances', []) if p.get('source_prompt', name) == name]
        presence = float(entries[0].get('source_presence', record['presence'])) if entries else float(record['presence'])
        assert all(float(p.get('source_presence', presence)) == presence for p in entries)
        entries = [p for p in sorted(entries, key=lambda p: -float(p['score']))
                   if float(p['score'])*presence >= .05][:30]
        out.append([dict(mask=F.resize(decode(p['mask']), F.SHAPE), score=float(p['score']), presence=presence)
                    for p in entries])
    return out


def iou(a, b):
    union = np.count_nonzero(a | b)
    return float(np.count_nonzero(a & b)/union) if union else None


def geometry(c, table):
    key = hashlib.sha256(json.dumps(c['canonical'], sort_keys=True, allow_nan=False).encode()).hexdigest()[:16]
    root = Path('/scratch/jjyeung/k1')
    gp = root/'run_convert_2'/key/'geometry.npz'
    if gp.exists():
        with np.load(io.BytesIO(pinned(gp)), allow_pickle=False) as z:
            arrays = {k:z[k] for k in ['K','canvas_to_source','camera_to_world','depth_grid','grid_uv','anchor_frame_indices']}
        geo = GE.from_arrays(**arrays, scale=table['geometry']['served_scale'])
    else:
        # Two audited captures were refused by the old up-axis guard; use the
        # same tower-to-reader construction used by serving_reference.geometry.
        tp = root/'run_tower_sam_2'/key
        with np.load(io.BytesIO(pinned(tp/'tower.npz')), allow_pickle=False) as z:
            tower = {k:z[k] for k in ['raw_pose','anchor_slots','frame_indices','depth_grid','grid_uv']}
        receipt = json.loads(pinned(tp/'PHASE_COMPLETE.json'))
        with np.load(io.BytesIO(pinned(root/'own_170235/native/probe'/key/'own.npz')), allow_pickle=False) as z:
            gravity = z['gravity']
        geo = GE.from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],
                            tower['depth_grid'],tower['grid_uv'],gravity,
                            table['geometry']['served_scale'],receipt['source_hw'])
    assert list(geo.frame_map.source_indices) == c['anchor_indices']
    return geo, key


def object_from_candidate(name, candidate, masks, geo):
    if candidate is None:
        return dict(name=name, seen=False, frames=[], visible=[], areas={}, points={}, boxes={})
    batch = np.zeros((32, 240, 320), bool)
    for f, mask in masks[candidate['id']].items():
        batch[f-1] = mask
    obj = pricing.lift_frames(name, batch, geo, G)
    obj['boxes'] = {}
    return obj


def main(limit=None):
    start = time.monotonic()
    seeds = load_json(N/'sb_cachk/out/v2/seeds/SEEDS.json')
    population = load_json(N/'sb_cachk/out/v2/POPULATION.json')
    body = {k:population[k] for k in ('decision','beside','track_order')}
    pid = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert pid == population['population_id'] == 'f0ecd8ee39f1e668027d2fbdf16d4b6bff56d9568dfedd4a90698929f4171bf0'
    guard = load_json(N/'sb_cachk/out/v2/GUARD.json', population['input_sha256'][str(N/'sb_cachk/out/v2/GUARD.json')])
    decision = population['decision']
    ids = set(decision['rows'])
    assert len(ids) == 1012 and len(decision['captures']) == 204
    for rec in guard['lists'].values():
        assert not (set(rec['hit_captures']) & set(decision['captures']))
    assert guard['k1_split']['passed']
    assert not set(guard['k1_split']['teacher_k1_refused']) & set(decision['captures'])
    manifest = json.loads(pinned('/scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json'))
    captures = {c['canonical']:c for c in manifest['captures']}
    caps = [captures[k] for k in decision['captures']]
    assert all(c['k1_split'] == c['split'] == 'train' for c in caps)
    assert not set(c['room'] for c in caps) & set(population['excluded_from_decision']['rooms'])
    assert {r['id'] for c in caps for r in c['rows'] if r['id'] in ids} == ids
    labels = {r['id']:r for r in json.loads(pinned('/scratch/jjyeung/orch_n30/sb_kbox4/train_labels.json'))['rows']}
    published = {}
    p = BOX/'out/box_ladder/PER_ITEM.jsonl'
    assert digest(p) == population['input_sha256']['/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl']
    PINS[str(p)] = dict(sha256=digest(p), bytes=p.stat().st_size)
    with p.open() as f:
        for line in f:
            if '"arm": "A0_deployed"' in line[:100]:
                row = json.loads(line)
                if row['row_id'] in ids:
                    assert row['row_id'] not in published
                    published[row['row_id']] = row
    assert set(published) == ids
    seeds_by_cap = {c['capture']:{o['name']:o for o in c['objects']} for c in seeds['captures']}
    for name in ['selector_head.py','sl118/selector_inputs.py']:
        p = SEL/name
        read(p, EXPECTED['/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/'+name])
    for name in ['student_pilot/routed_features.py','student_pilot/routed_candidates.py']:
        read(TREE/name, EXPECTED[str(TREE_ORIG/name)])
    hp = N/'b04host3/b04_e2ehook/heads/selector/work/run_iso'
    for ext in ['json','safetensors']:
        pinned(hp/('selector_head.'+ext))
    head, _ = load_head(hp)
    all_calls, all_rows, checks = [], [], []
    for ci, c in enumerate(caps[:limit] if limit else caps):
        cap = c['canonical']
        table_path = '/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/serving_tables/'+cap.replace('/','__')+'.json.gz'
        table = json.loads(gzip.decompress(pinned(table_path)))
        assert table['capture'] == cap and table['room'] == c['room'] and table['split'] == 'train'
        geo, key = geometry(c, table)
        cache = json.loads(pinned('/scratch/jjyeung/k1/run_convert_2/'+key+'/candidates.json'))
        assert cache['frame_indices'] == c['anchor_indices']
        with np.load(io.BytesIO(pinned(c['gt']['path'])), allow_pickle=False) as z:
            raster = z['inst'] if 'inst' in z else z['instances']
            valid = z['valid'].astype(bool)
            assert np.array_equal(z['frame_indices'], c['anchor_indices'])
        gt240 = np.stack([ndimage.zoom(f,(240/f.shape[0],320/f.shape[1]),order=0,prefilter=False) for f in raster])
        rows = [r for r in c['rows'] if r['id'] in ids]
        grids = F.candidates.lift_grid(geo)
        data = {}
        for name in sorted({n for r in rows for n in r['operands']}):
            assert len(c['gt_name_ids'][name]) == 1
            iid = c['gt_name_ids'][name][0]
            visibility = {str(f+1):float(np.mean(raster[f] == iid)) if valid[f] else 0. for f in range(32)}
            raw = raw_name(cache, name)
            proposals, _ = F.candidates.lift(F.cache_for(name,raw),name,geo,floor=.3,grids=grids,phrase=name)
            tracks = {t.id:t for t in F.candidates.link(proposals,name)}
            refs = [r for r in table['rows'] if r['name'] == name]
            inputs = [r for r in table['inputs'] if r['name'] == name]
            assert [r['candidate_id'] for r in refs] == [r['candidate_id'] for r in inputs]
            assert set(tracks) == {r['candidate_id'] for r in refs}
            candidates, masks = [], {}
            for ref in refs:
                cid = ref['candidate_id']
                track = tracks[cid]
                assert {p.frame-1 for p in track.proposals} == {m['slot'] for m in ref['members']}
                mm = {p.frame:raw[p.frame-1][p.index]['mask'][::2,::2] for p in track.proposals}
                assert len(mm) == len(track.proposals)
                masks[cid] = mm
                ious = {str(f):iou(mask,gt240[f-1] == iid) for f,mask in mm.items()}
                for m in ref['members']:
                    # Table labels compare the exact same per-frame 240x320 mask.
                    value = ious[str(m['slot']+1)]
                    if m['gid'] == iid:
                        assert value is not None and abs(value-m['iou']) < 1e-12, (cap,name,cid,m,value)
                best = min(mm, key=lambda f:(-int(mm[f].sum()),f))
                area = {str(f):int(mask.sum()) for f,mask in mm.items()}
                assert all(a > 0 for a in area.values())
                candidates.append(dict(id=cid,members=area,on_target=bool(ious[str(best)] is not None and ious[str(best)]>=.5),
                                       best_frame=best, best_iou=ious[str(best)], cited_ious=ious))
            with torch.no_grad():
                chosen = int(torch.argmax(head.with_null(torch.tensor([r['x'] for r in inputs],dtype=torch.float64),None,name)[:-1])) if inputs else -1
            baseline = candidates[chosen] if chosen >= 0 else None
            seed = seeds_by_cap[cap][name]['S_A0']
            assert (baseline['id'] if baseline else None) == seed.get('candidate_id'), (cap,name,'baseline_id')
            assert bool(baseline and baseline['on_target']) == seed.get('on_target',False), (cap,name,'on_target')
            if baseline:
                assert baseline['best_frame'] == seed['slot'], (cap,name,'best_frame')
                assert abs(baseline['best_iou']-seed['iou']) < 1e-12, (cap,name,'iou')
            best = best_anchor(visibility)
            neighbor = neighbor_anchor(visibility,best) if best is not None else None
            selections = dict(baseline=baseline, a3x=a3x(candidates,best) if best else None,
                              neighbor=a3x(candidates,neighbor) if neighbor else None)
            objects = {}
            object_cache = {}
            for arm, cand in selections.items():
                cid = cand['id'] if cand else None
                if cid not in object_cache:
                    object_cache[cid] = object_from_candidate(name,cand,masks,geo)
                objects[arm] = object_cache[cid]
            for row in rows:
                if name in row['operands']:
                    assert row['gt_instances'][name] == iid
                    assert objects['baseline']['frames'] == published[row['id']]['member_frames'][name], (cap,name,'frames')
            check = dict(capture=cap,name=name,candidates=len(candidates),baseline_id=seed.get('candidate_id'),
                         baseline_seed_parity=True,member_frames_parity=True,table_member_parity=True)
            checks.append(check)
            data[name] = dict(objects=objects,candidates=candidates,baseline=baseline,visibility=visibility,
                              best=best,neighbor=neighbor,instance=iid)
        for row in rows:
            rid = row['id']
            for n in row['operands']:
                d = data[n]
                all_calls.append(dict(row_id=rid,room=c['room'],capture=cap,dataset=cap.split('/')[0],operand=n,
                    instance=d['instance'],baseline_id=d['baseline']['id'] if d['baseline'] else None,
                    gt_visibility=d['visibility'],candidates=d['candidates']))
            results = {}
            for arm in ['baseline','a3x','neighbor']:
                objs = {n:data[n]['objects'][arm] for n in row['operands']}
                try:
                    pred, refusal, _, _ = pricing.session_distance(row,geo,objs,G,'best1')
                except (ValueError,KeyError,IndexError) as exc:
                    pred, refusal = None, type(exc).__name__+':'+str(exc)
                results[arm] = dict(prediction=pred,refusal=refusal,mra=math_v2.mra(pred,labels[rid]['corrected']))
            assert results['baseline']['prediction'] == published[rid]['prediction'], (rid,results['baseline'],published[rid]['prediction'])
            assert labels[rid]['corrected'] == published[rid]['label']
            all_rows.append(dict(row_id=rid,room=c['room'],capture=cap,dataset=cap.split('/')[0],
                neighbor_both_eligible=all(data[n]['neighbor'] is not None for n in row['operands']),
                label=labels[rid]['corrected'],**results))
        print(json.dumps(dict(capture=ci+1,total=len(caps),name=cap,rows=len(all_rows),objects=len(checks),seconds=round(time.monotonic()-start,1))),flush=True)
        write('K1_PROGRESS.json',dict(captures=ci+1,rows=len(all_rows),seconds=time.monotonic()-start))
    if not limit:
        assert len(all_calls) == 2024 and {r['row_id'] for r in all_calls} == ids
        assert len(all_rows) == 1012 and len({r['row_id'] for r in all_rows}) == 1012
    tag = 'pilot_' if limit else ''
    (W/(tag+'k1_calls.jsonl')).write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in all_calls))
    write(tag+'k1_distance_rows.json',all_rows)
    for module in list(sys.modules.values()):
        p = getattr(module, '__file__', None)
        if p and p.endswith('.py') and str(p).startswith((str(BOX),str(TREE),str(FALLBACK),str(SEL),str(W))):
            read(p)
    read(__file__)
    write(tag+'k1_adapter_validation.json',dict(status='PASS',population_id=pid,rows=len(all_rows),calls=len(all_calls),
        rooms=len({r['room'] for r in all_rows}),captures=len({r['capture'] for r in all_rows}),objects=len(checks),
        baseline_distances_equal_published=len(all_rows),checks=checks,
        exclusion_authority='Pinned POPULATION + GUARD, exact decision IDs; no new training-admission claim',
        input_sha256=PINS,seconds=time.monotonic()-start))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit',type=int)
    args = parser.parse_args()
    main(args.limit)
