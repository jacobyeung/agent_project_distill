"""Resolve which K1 training rows sit in the 80 withheld rooms with the fixed sb_auditfix2 checker, plant test rows,
and write the 1,012-row rowsets (bash run.sh legality.py)."""
import gzip, importlib.util, json
from common import B, ROWSETS, OUT, PINS, read, jread, pin, sha, write

CHECKER = B/'sb_auditfix2/store_room_audit.py'
TREE, LISTS = B/'sb_auditfix2/inputs/tree_r1', B/'sb_auditfix2/inputs/lists'
PINNED = B/'sb_kbox4/pinned_train.json'
RULING = ['scannet/scene0201_02', 'scannet/scene0255_01', 'scannet/scene0478_00', 'scannet/scene0478_01',
          'scannet/scene0614_02', 'scannet/scene0692_03']
SELECTOR = B/'b04host3/b04_e2ehook/heads/selector'


def checker():
    read(CHECKER)
    spec = importlib.util.spec_from_file_location('fixed_audit', CHECKER)
    audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    ledger = audit.Inputs()
    rooms, mint, sets, checks, aliases, quarantine = audit.prepare(TREE, LISTS, ledger)
    PINS.update({k: v['sha256'] for k, v in ledger.pins.items()})
    def resolve(row):
        _, canonical, room, tier, error = audit.resolve(row, rooms, mint, aliases, quarantine)
        return dict(canonical=canonical, room=room, tier=tier, error=error, hits={n: int(room in s) for n, s in sets.items()})
    return resolve, sets, checks


def withheld_rows(captures, ids, resolve):
    """The one filter every report uses: a priced row is withheld when the checker puts its capture in a withheld room."""
    flagged, mismatches = [], []
    for c in captures:
        ds, scene = c['canonical'].split('/', 1)
        r = resolve(dict(dataset=ds, scene=scene, canonical=c['canonical']))
        if r['error'] or (c.get('room') and r['room'] != c['room']):
            mismatches.append([c['canonical'], r['room'], c.get('room'), r['error']])
        if r['hits']['withheld-80']:
            flagged.append(dict(capture=c['canonical'], room=r['room'], tier=r['tier'], hits=r['hits'],
                                priced_row_ids=[x['id'] for x in c['rows'] if x['id'] in ids]))
    excluded = {i for f in flagged for i in f['priced_row_ids']}
    return flagged, excluded, mismatches


def main():
    resolve, sets, checks = checker()
    manifest = jread(PINNED); caps = manifest['captures']
    order = read(ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines(); ids = set(order)
    tables = read(ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines()
    assert len(order) == len(ids) == 1037 and len(tables) == 883 and set(tables) <= ids
    assert PINS[str(ROWSETS/'K1_TRAIN_1037.txt')].startswith('e7646798')
    flagged, excluded, mismatches = withheld_rows(caps, ids, resolve)
    hits = {n: sorted(c['canonical'] for c in caps if resolve(dict(zip(('dataset', 'scene'), c['canonical'].split('/', 1)),
                                                                     canonical=c['canonical']))['hits'][n]) for n in sets}
    assert not mismatches, mismatches
    assert sorted(f['capture'] for f in flagged) == RULING, flagged
    keep = [i for i in order if i not in excluded]; keep_tables = [i for i in tables if i not in excluded]

    # Planted rows. Each goes through the same checker call and the same row filter that produced the 1,012.
    withheld_rooms = sorted(sets['withheld-80']); flagged_rooms = {f['room'] for f in flagged}
    fresh = next(r for r in withheld_rooms if r.startswith('scannet/') and r not in flagged_rooms)
    r0 = next(r for r in sorted(sets['R0']) if r.startswith('scannet/'))
    clean_cap = next(c for c in caps if c['canonical'].startswith('scannet/') and c['canonical'] not in RULING
                     and any(x['id'] in ids for x in c['rows']))
    probes = {
        'withheld_rescan_of_flagged_room': dict(dataset='scannet', scene='scene0201_07'),
        'withheld_room_not_in_K1_train': dict(dataset='scannet', scene=fresh.split('/')[1]+'_99'),
        'R0_room_review_v2_probe': dict(dataset='scannet', scene=r0.split('/')[1]+'_99'),
        'clean_K1_train_capture': dict(dict(zip(('dataset', 'scene'), clean_cap['canonical'].split('/', 1))), canonical=clean_cap['canonical']),
    }
    expect = {'withheld_rescan_of_flagged_room': 'withheld-80', 'withheld_room_not_in_K1_train': 'withheld-80',
              'R0_room_review_v2_probe': 'R0', 'clean_K1_train_capture': None}
    planted = {}
    for k, row in probes.items():
        r = resolve(row)
        want = {n: int(n == expect[k]) for n in sets}
        planted[k] = dict(row=row, resolved_room=r['room'], error=r['error'], hits=r['hits'], expected_hits=want, passed=r['hits'] == want and not r['error'])
    # End to end: plant one priced row in a withheld-room capture and one in a clean capture, then rerun the filter.
    synthetic = caps + [dict(canonical='scannet/scene0201_07', room='scannet/scene0201', rows=[dict(id='planted-withheld-row')])]
    synthetic = [dict(c, rows=c['rows']+[dict(id='planted-clean-row')]) if c['canonical'] == clean_cap['canonical'] else c for c in synthetic]
    ids_p = ids | {'planted-withheld-row', 'planted-clean-row'}
    f2, ex2, mm2 = withheld_rows(synthetic, ids_p, resolve)
    pipeline = dict(planted=['planted-withheld-row in scannet/scene0201_07', 'planted-clean-row in '+clean_cap['canonical']],
                    excluded=len(ex2), withheld_row_excluded='planted-withheld-row' in ex2, clean_row_kept='planted-clean-row' not in ex2,
                    real_excluded_unchanged=ex2 - {'planted-withheld-row'} == excluded, mismatches=mm2)
    pipeline['passed'] = pipeline['withheld_row_excluded'] and pipeline['clean_row_kept'] and pipeline['real_excluded_unchanged'] and not mm2
    assert all(p['passed'] for p in planted.values()) and pipeline['passed'], (planted, pipeline)

    # Independent cross-check: raw 634820b4 room strings against the pinned capture rooms, no checker code.
    raw = json.loads(read(LISTS/'634820b4.raw'))['rooms']
    raw_set = set(raw); independent = sorted(c['canonical'] for c in caps if c['room'] in raw_set)

    # Exposure of the deployed run_iso selector (A0's selector, not retrained here) to the withheld captures.
    scales = jread(SELECTOR/'sl118/SCALES_S4.json')['captures']; exposure = []
    for cap in RULING:
        p = SELECTOR/'data/caps_iso'/(cap.replace('/', '__')+'.json.gz')
        rec = dict(capture=cap, in_caps_iso=p.exists(), split=scales.get(cap, {}).get('split'))
        if p.exists():
            d = json.loads(gzip.decompress(read(p))); rec.update(candidates=len(d['rows']), objects=len({r['object_id'] for r in d['rows']}))
        exposure.append(rec)

    (OUT/'K1_TRAIN_1012.txt').write_text('\n'.join(keep)+'\n')
    (OUT/'K1_WITHHELD_25.txt').write_text('\n'.join(i for i in order if i in excluded)+'\n')
    (OUT/f'K1_TRAIN_TABLES_{len(keep_tables)}.txt').write_text('\n'.join(keep_tables)+'\n')
    lists = {n: dict(path=str(OUT/n), sha256=sha(OUT/n), rows=len(open(OUT/n).read().splitlines()))
             for n in ['K1_TRAIN_1012.txt', 'K1_WITHHELD_25.txt', f'K1_TRAIN_TABLES_{len(keep_tables)}.txt']}
    rooms_all = {c['room'] for c in caps if any(x['id'] in ids for x in c['rows'])}
    rooms_keep = {c['room'] for c in caps if any(x['id'] in set(keep) for x in c['rows'])}
    result = dict(
        ruling='RULING 1056Z item 1: the 80 withheld rooms (pin 634820b4) are held out; nothing is selected or trained on them.',
        checker=str(CHECKER), captures=len(caps), list_checks=checks, real_hits=hits,
        withheld_captures=flagged, withheld_captures_match_ruling=True, withheld_rooms=sorted(flagged_rooms),
        withheld_priced_captures=sum(bool(f['priced_row_ids']) for f in flagged), withheld_priced_rows=len(excluded),
        excluded_from_tables_883=len(set(tables) & excluded),
        rowsets=lists, rows_kept=len(keep), table_rows_kept=len(keep_tables),
        priced_rooms_1037=len(rooms_all), priced_rooms_1012=len(rooms_keep),
        planted_row_tests=planted, planted_pipeline_test=pipeline,
        independent_raw_list_check=dict(captures=independent, agrees=independent == RULING),
        deployed_selector_exposure=dict(selector=str(SELECTOR/'work/run_iso/selector_head.json'), captures=exposure,
            note='A0 and every arm that uses the run_iso selector were trained on caps_iso train-split captures; withheld captures listed here as in_caps_iso with split train were in that fit. Not retrained here.'))
    pin(SELECTOR/'work/run_iso/selector_head.json')
    write('LEGALITY.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('real_hits', 'input_sha256')}, indent=1)[:6000])


if __name__ == '__main__':
    main()
