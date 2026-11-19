"""CPU dry-run checks, each written into out/dry/DRYRUN.json (merged by check name).

  stub_seed    seed-alone stub: C_best1 on S_A0 equals A0_deployed on 1,037 of 1,037 predictions
  stub_seed_phr  the same stub on S_PHR equals the phrase kit's frozen arm (W1) on 1,037 of 1,037 predictions
  stub_raster  raster stub: C_best1 equals A2_gt_masks (73.97) and C_fused equals fused_cf (78.62) on every row
  frames       dense_frames[anchor_slots[i]] is anchor i's file (sha256) for every capture
  folds        room folds disjoint, every priced capture k1_split == train, 1,037 rows all train
  reuse        sb_kobj4 K1_TRACK.json reused only if its checkpoint and frames match
  seeds        dry-run item 1 from out/seeds (5 captures, then all)
  sam3_cpu     SAM 3 loads from the pinned checkpoint on CPU; 8-frame probe
  cpu_pass8    one capture through mc_track_pass on CPU (real tracker), 8 dense frames, then priced
  cpu_pass64   the same capture on all 64 dense frames, every seeded object, then priced
Usage: python mc_dry.py <check> [...]   (p1cpu interpreter)
"""
import json, sys, time
from pathlib import Path
import mc_common as C
import mc_ladder as L

DRY = C.OUT/'dry'


def priced(price_dir):
    items = []
    for p in sorted(Path(price_dir).glob('*.json.gz')):
        items += C.read_json(p)['items']
    return items


def summarize_train():
    L.T()
    import summarize_train as ST
    return ST


def compare(mine, published, arm_pub):
    mine = {r['row_id']: r for r in mine}
    pub = {k[1]: v for k, v in published.items() if k[0] == arm_pub}
    ids = sorted(pub)
    same_pred = sum(mine.get(i, {}).get('prediction', 'missing') == pub[i]['prediction'] for i in ids)
    same_all = sum(i in mine and mine[i]['prediction'] == pub[i]['prediction'] and mine[i]['refusal_code'] == pub[i]['refusal_code']
                   and mine[i]['box'] == pub[i]['box'] for i in ids)
    ST = summarize_train()
    diff = [dict(row_id=i, mine=mine.get(i, {}).get('prediction'), published=pub[i]['prediction']) for i in ids
            if mine.get(i, {}).get('prediction', 'missing') != pub[i]['prediction']][:10]
    return dict(rows=len(ids), missing=sum(i not in mine for i in ids), equal_predictions=same_pred, equal_prediction_refusal_box=same_all,
                mra_mine=ST.mean([mine[i] for i in ids if i in mine]) if len(mine) >= len(ids) else None,
                mra_published=ST.mean([pub[i] for i in ids]), refusals_mine=sum(mine.get(i, {}).get('prediction') is None for i in ids),
                refusals_published=sum(pub[i]['prediction'] is None for i in ids), first_differences=diff)


def stub_seed():
    items = priced(C.OUT/'dry/price/S_A0_STUBSEED')
    pub = L.published(('A0_deployed',))
    r = compare([x for x in items if x['arm'] == 'C_best1/S_A0/STUBSEED'], pub, 'A0_deployed')
    return dict(r, passed=r['equal_predictions'] == r['rows'] == 1037,
                bar='C_best1 on S_A0 with the seed-alone stub equals A0_deployed on 1,037 of 1,037 predictions')


def stub_seed_phr():
    """Seed-alone stub on S_PHR against the phrase kit's own W1 rows (W1 chose heater -> q:radiator in every fold)."""
    path = C.PHRASE_SET.parent/'PER_ITEM.jsonl'
    arm = C.read_json(C.PHRASE_SET)['arm']
    C.pin(path)
    pub = {}
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            if r['arm'] == arm:
                pub[(arm, r['row_id'])] = r
    items = priced(C.OUT/'dry/price/S_PHR_STUBSEED')
    r = compare([x for x in items if x['arm'] == 'C_best1/S_PHR/STUBSEED'], pub, arm)
    return dict(r, arm=arm, passed=r['equal_predictions'] == r['rows'] == 1037,
                bar=f'C_best1 on S_PHR with the seed-alone stub equals the phrase kit arm {arm} on 1,037 of 1,037 predictions')


def stub_raster():
    items = priced(C.OUT/'dry/price/S_GT_STUBRASTER')
    pub = L.published(('A2_gt_masks', 'fused_cf'))
    best1 = compare([x for x in items if x['arm'] == 'C_best1/S_GT/STUBRASTER'], pub, 'A2_gt_masks')
    fused = compare([x for x in items if x['arm'] == 'C_fused/S_GT/STUBRASTER'], pub, 'fused_cf')
    return dict(C_best1_vs_A2_gt_masks=best1, C_fused_vs_fused_cf=fused,
                passed=best1['equal_predictions'] == best1['rows'] == 1037 and fused['equal_predictions'] == fused['rows'] == 1037,
                bar='raster stub: C_best1 == A2_gt_masks (73.97) and C_fused == fused_cf (78.62) on every row')


def frames():
    fs = C.frame_sets()
    caps = fs['captures']
    keys = sorted({k for c in caps.values() for k in c['checks']})
    counts = {k: sum(bool(c['checks'][k]) for c in caps.values()) for k in keys}
    return dict(captures=len(caps), checks=counts, unique_frames=fs['unique_frames'], frame_bytes=fs['frame_bytes'],
                failures=fs['failures'], passed=all(v == len(caps) for v in counts.values()) and not fs['failures'],
                bar='dense_frames[anchor_slots[i]] is anchor i file, sha256 equal to the anchor list, every capture')


def folds():
    caps, labels, rowids, tableids, folds_, truth, head = L.setup()
    rooms = {}
    for c in caps:
        rooms.setdefault(c['room'], set()).add(folds_[c['room']])
    by_fold = {}
    for room, f in folds_.items():
        by_fold.setdefault(f, set()).add(room)
    overlap = sum(len(a & b) for i, a in by_fold.items() for j, b in by_fold.items() if i < j)
    splits = sorted({c['k1_split'] for c in caps})
    rows = [r for c in caps for r in c['rows'] if r['id'] in rowids]
    items = priced(C.OUT/'dry/price/S_A0_STUBSEED')
    item_splits = sorted({x['split'] for x in items})
    out = dict(captures=len(caps), rooms=len(rooms), folds={str(k): len(v) for k, v in sorted(by_fold.items())},
               room_fold_overlap=overlap, rooms_in_one_fold=sum(len(v) == 1 for v in rooms.values()), k1_splits=splits,
               rows=len(rows), priced_item_splits=item_splits, rowset_size=len(rowids))
    out['passed'] = overlap == 0 and out['rooms_in_one_fold'] == len(rooms) and splits == ['train'] and len(rows) == 1037 and item_splits == ['train']
    return out


def reuse():
    p = C.REUSE
    if not p.exists():
        return dict(path=str(p), status='ABSENT', reused=False, passed=True,
                    note='no K1_TRACK.json from sb_kobj4: every seed set and frame set is tracked fresh')
    d = C.read_json(p)
    fs = C.frame_sets()
    ck = d.get('checkpoint_sha256') or d.get('contract', {}).get('checkpoint')
    frames_ok = all(d.get('frames', {}).get(k) == [x['sha256'] for x in v['dense']] for k, v in fs['captures'].items()) if 'frames' in d else False
    ok = ck == C.CHECKPOINT_SHA256 and frames_ok
    return dict(path=str(p), status='PRESENT', checkpoint=ck, checkpoint_match=ck == C.CHECKPOINT_SHA256, frames_match=frames_ok,
                reused=ok, passed=True)


def seeds():
    out = {}
    for name in ('SEEDS_first5.json', 'SEEDS.json'):
        p = C.OUT/'seeds'/name
        if p.exists():
            d = C.read_json(p)
            out[name] = dict(check1=d['check1'], summary=d['summary'], scope=d['scope'])
    ok = all(v['check1']['passed'] == v['check1']['objects'] and v['check1']['captures_passed'] == v['check1']['captures'] for v in out.values())
    return dict(out, passed=ok and 'SEEDS.json' in out,
                bar='rebuilt A0 served masks equal sb_maskfail records on all 32 anchors, A0 frames equal published, seed = served mask on obj["best"]')


def sam3_cpu():
    d = C.read_json(DRY/'SAM3_CPU_PROBE.json')
    return {k: d.get(k) for k in ('status', 'capture', 'name', 'load_seconds', 'embed_seconds', 'track_seconds', 'seconds',
                                  'peak_rss_mib', 'shims', 'modules_outside_scratch', 'parameters', 'dtype', 'scores', 'anchors', 'error')} | \
        dict(passed=d['status'] == 'PASS')


def cpu_pass(tag):
    root = C.OUT/f'dry/track_{tag}'
    index = C.read_json(root/'TRACK_INDEX.json')
    events = [json.loads(x) for x in (root/'EVENTS.jsonl').read_text().splitlines()]
    caps = [e for e in events if e['event'] == 'CAPTURE']
    out = dict(index={k: index[k] for k in ('sets_run', 'done', 'spent_seconds', 'embed_mean', 'set_means', 'stopped')}, captures=caps)
    for e in caps:
        for s in e['sets']:
            seed_set, fs = s.split('/')
            track = C.read_json(root/f'{seed_set}_{fs}'/(C.stub(e['capture'])+'.json.gz'))
            res = dict(dense_slots=track['dense_slots'], skipped_objects=track['skipped_objects'],
                       objects=[dict(name=o['name'], seed_slot=o['seed_slot'], seconds=o['seconds'],
                                     carried=[a['slot'] for a in o['anchors'] if a['carried']]) for o in track['objects']])
            price = C.OUT/f'dry/price_{tag}'/f'{seed_set}_{fs}'/(C.stub(e['capture'])+'.json.gz')
            if price.exists():
                items = C.read_json(price)['items']
                res['priced'] = [dict(arm=x['arm'], row_id=x['row_id'], prediction=x['prediction'], label=x['label'],
                                      refusal_code=x['refusal_code']) for x in items]
            out[s] = res
    out['passed'] = index['stopped'] is None and bool(caps)
    return out


CHECKS = dict(stub_seed=stub_seed, stub_seed_phr=stub_seed_phr, stub_raster=stub_raster, frames=frames, folds=folds, reuse=reuse, seeds=seeds,
              sam3_cpu=sam3_cpu, cpu_pass8=lambda: cpu_pass('cpu8'), cpu_pass64=lambda: cpu_pass('cpu64'))


def main():
    path = DRY/'DRYRUN.json'
    have = C.read_json(path) if path.exists() else dict(checks={})
    C.PINS.clear()
    for name in sys.argv[1:]:
        t0 = time.monotonic()
        try:
            res = CHECKS[name]()
        except Exception as exc:
            import traceback
            res = dict(passed=False, error=f'{type(exc).__name__}: {exc}', traceback=traceback.format_exc()[-1500:])
        res['seconds'] = time.monotonic()-t0
        res['command'] = f'bash kit/run_cpu.sh p1cpu mc_dry.py {name}'
        have['checks'][name] = res
        print(json.dumps({name: {k: v for k, v in res.items() if k in ('passed', 'error', 'equal_predictions', 'rows', 'status')}}), flush=True)
    C.code_pins()
    have.pop('input_sha256', None)
    C.write_json(path, have)


if __name__ == '__main__':
    main()
