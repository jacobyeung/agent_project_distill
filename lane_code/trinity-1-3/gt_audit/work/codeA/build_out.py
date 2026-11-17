"""Assemble gt_audit deliverables under out/ (copies of evidence, drop lists, dev-S1 label check, summary table, SHA256SUMS)."""
import collections, hashlib, json, pathlib, shutil

LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
W, O = LANE / 'work', LANE / 'out/audit'
O.mkdir(parents=True, exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


copies = {
    'k1/K1_ROW_AUDIT.jsonl': W / 'k1audit/K1_ROW_AUDIT.jsonl', 'k1/K1_BOX_AUDIT.json': W / 'k1audit/K1_BOX_AUDIT.json',
    'k1/K1_LABELS_CORRECTED.jsonl': W / 'k1audit/K1_LABELS_CORRECTED.jsonl', 'k1/K1_RESCORE.json': W / 'k1audit/K1_RESCORE.json',
    'k1/K1_KILL_RESCORE.json': W / 'k1audit/K1_KILL_RESCORE.json', 'k1/RASTER_SHA_CHECK.json': W / 'k1audit/RASTER_SHA_CHECK.json',
    'k1/GEO_decide_stored.json': W / 'geo/decide_stored.json', 'k1/GEO_decide_corrected.json': W / 'geo/decide_corrected.json',
    'k1/GEO_decide_drop.json': W / 'geo/decide_drop.json', 'k1/LIFT_AGG_HELDOUT_stored.txt': W / 'lift/AGG_HELDOUT_stored.txt',
    'k1/LIFT_AGG_HELDOUT_corrected.txt': W / 'lift/AGG_HELDOUT_corrected.txt', 'k1/LIFT_AGG_HELDOUT_drop.txt': W / 'lift/AGG_HELDOUT_drop.txt',
    'k1/SCALEHEAD_AGG_HELDOUT_stored.txt': W / 'scalehead/AGG_HELDOUT_stored.txt', 'k1/SCALEHEAD_AGG_HELDOUT_corrected.txt': W / 'scalehead/AGG_HELDOUT_corrected.txt',
    'k1/SCALEHEAD_AGG_HELDOUT_drop.txt': W / 'scalehead/AGG_HELDOUT_drop.txt',
    'r0dev/R0_CONVENTION_ROWS.jsonl': W / 'r0conv/R0_CONVENTION_ROWS.jsonl', 'r0dev/R0_CONVENTION_SUMMARY.json': W / 'r0conv/R0_CONVENTION_SUMMARY.json',
    'vsti/VSTI_BOX_CHECK.json': W / 'vsti_check/VSTI_BOX_CHECK.json',
}
for dst, src in copies.items():
    (O / dst).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, O / dst)

# K1 drop list (rows whose label is inflated or unverifiable here), per split.
L = [json.loads(l) for l in open(W / 'k1audit/K1_LABELS_CORRECTED.jsonl')]
with open(O / 'k1/K1_DROP_AFFECTED.tsv', 'w') as f:
    f.write('row_id\tcapture\tsplit\tdataset\tconvention\tstored_m\tcorrected_m\n')
    for r in sorted(L, key=lambda r: (r['split'], r['capture'], r['id'])):
        if r['affected']:
            f.write('%s\t%s\t%s\t%s\t%s\t%.6f\t%s\n' % (r['id'], r['capture'], r['split'], r['dataset'], r['convention'], r['stored'],
                                                    '' if r['corrected'] is None else '%.6f' % r['corrected']))

# dev-S1 label check: routed 636 (H1 evaluator scores 'answer'), direct list (scores ground_truth).
I = json.load(open('/scratch/jjyeung/orch_n30/notseen_diag/work/f3/p446/items/devs1_routed.json'))['items']
E = [json.loads(l) for l in open('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/0/budget_2048.jsonl')]
census = json.load(open(W / 'SCENE_CENSUS_materialization_v2.json'))
mv2 = {x['scene'] for x in census['scenes'] if x['dataset'] == 'scannet'}
known_half = sorted({b['canonical'].split('/')[1] for b in json.load(open(W / 'k1audit/K1_BOX_AUDIT.json')).values()
                     if b['status'] == 'half' and b['canonical'].startswith('scannet/')} |
                    {b['canonical'].split('/')[1] for b in json.load(open('/scratch/jjyeung/orch_n30/rows_r1/out/extent_audit/BOX_AUDIT.json')).values()
                     if b['status'] == 'half' and b['canonical'].startswith('scannet/')})
with open(O / 'devs1/DEVS1_LABEL_CHECK.jsonl', 'w') as f:
    for i in I:
        if i['question_type'] in ('object_abs_distance', 'room_size_estimation'):
            ratio = float(i['answer']) / float(i['released_answer'])
            f.write(json.dumps(dict(set='devs1_routed_636', id=i['id'], type=i['question_type'], dataset=i['dataset'], scene=i['scene'],
                                    canonical_answer=i['answer'], released_answer=i['released_answer'], ratio=ratio,
                                    scene_has_materialization_v2_asset=i['scene_name'] in mv2, scene_known_half=i['scene_name'] in known_half), sort_keys=True) + '\n')
    for r in E:
        f.write(json.dumps(dict(set='devs1_direct_1525', id=r['id'], type=r['question_type'], dataset=r['dataset'], scene=r['scene'], stratum=r['stratum'],
                                scored_label=r['ground_truth'], scored_is_released=r['ground_truth'] == r.get('released_answer_in_options'),
                                scene_known_half=r['scene_name'] in known_half), sort_keys=True) + '\n')

# R1 gate sets: no item needs a correction or a drop for this defect.
gates = {
    'devs1_direct_1525 (harm rule H1/H2, relative size, toward twins)': dict(drop=[], corrected=[], reason='scored label is the released VSI-590K label on 1,375 of 1,375 primary items; route planning 150 uses the generated route pack (builder lost with trinity-2-18, unread; turn-sequence answers; scannetppv2 85, arkitscenes 50, scannet 15); no scannetpp/ (v1) row; no ScanNet scene known half'),
    'devs1_routed_636 (tower-arm/claimed reads: distance 150, room 36, camera 450; units, recovery, call-cap)': dict(drop=[], corrected=[], reason='canonical labels within 10% of released on 186/186 (ratio 0.917-1.089; H1-0 scored on released: 0.200 -> 0.197); camera labels are poses; datasets scannetppv2/scannet/arkitscenes only'),
    'vsti_rel_dev_r0 900': dict(drop=[], corrected=[], reason='rasters built from ScanNet++ meshes with full-length OBBs: audit tool 6,441 full / 1,961 unknown / 0 half boxes over 68 rooms'),
    'R0-dev f32 2,169 (printed reads, 98 room items)': dict(drop=[], corrected=[], reason='labels from instance mesh vertices (closest vertices, min-area z-up box of vertices, xy occupancy); no box enters any label'),
}
json.dump(gates, open(O / 'R1_GATE_DROP_LISTS.json', 'w'), indent=1)

with open(O / 'SHA256SUMS', 'w') as f:
    for p in sorted(O.rglob('*')):
        if p.is_file() and p.name != 'SHA256SUMS':
            f.write('%s  %s\n' % (sha(p), p.relative_to(O)))
print(open(O / 'SHA256SUMS').read())
print('k1 drop rows', sum(r['affected'] for r in L), collections.Counter((r['split'], r['dataset']) for r in L if r['affected']))
print('known half scannet scenes', len(known_half), known_half)
