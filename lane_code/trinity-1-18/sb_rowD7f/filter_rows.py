"""Apply the labelling pilot's builder rules R1-R3 to the rebuilt twins and, for counting, to their v7 sources.

R1 drops a row that names a placeholder or non-object label. R2 re-cites or drops a cited (object, frame)
fact under 1% of the frame. R3 drops a row whose named object is visible in no sampled frame. R2 and R3
use only local rasters authenticated in out/RASTER_INDEX.json whose 32 frame indices equal the row's;
other rows are listed by qid and left unchanged. A twin and its source share names, scene and frames,
so a failing source drops its twin and the pair leaves the teaching subset together.
"""
import collections as C, hashlib, json, re, sqlite3, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
D7 = HERE / 'd7'
sys.path.insert(0, str(D7))
sys.dont_write_bytecode = True
from survey import d  # noqa: E402

OUT = HERE / 'out'
DB = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
DB_SHA = '210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
VISIBLE = 0.002
CITE = 0.01
# ScanNet raw/NYU40 catch-alls, ScanNet++ annotation markers, ARKitScenes has none; matched on whole name.
PLACEHOLDERS = {
    'remove': 'ScanNet++ annotation marker for geometry to delete',
    'split': 'ScanNet++ annotation marker for an instance to split',
    'structure': 'ScanNet/ScanNet++ catch-all for unnamed architecture',
    'object': 'ScanNet raw-label catch-all', 'objects': 'ScanNet raw-label catch-all',
    'stuff': 'ScanNet raw-label catch-all', 'misc': 'ScanNet raw-label catch-all',
    'miscellaneous': 'ScanNet raw-label catch-all', 'unknown': 'ScanNet raw-label catch-all',
    'unlabeled': 'ScanNet/ScanNet++ unannotated', 'unlabelled': 'ScanNet/ScanNet++ unannotated',
    'void': 'ScanNet unannotated', 'other': 'catch-all',
    'otherprop': 'NYU40 class 40', 'otherfurniture': 'NYU40 class 39', 'otherstructure': 'NYU40 class 38',
    'other prop': 'NYU40 class 40', 'other furniture': 'NYU40 class 39', 'other structure': 'NYU40 class 38',
}
SURFACES = ('wall', 'floor', 'ceiling')
FRAME_CITE = re.compile(r'\bframes?\s+\d+', re.I)


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def coverage(z, name):
    labels = [str(x).strip().lower() for x in z['labels']]
    ids = [int(i) for i, l in zip(z['ids'], labels) if l == name.strip().lower()]
    if not ids:
        return None
    inst = z['inst']; valid = z['valid']
    cov = np.isin(inst, ids).reshape(inst.shape[0], -1).mean(axis=1)
    return dict(ids=ids, per_frame=[round(float(c), 6) for c in cov], valid=[bool(v) for v in valid])


def main():
    inputs = {}
    for p in (D7 / 'out/NEW_ROWS.jsonl', D7 / 'out/SOURCE_MAP.jsonl', D7 / 'out/TEACHING_SET.json',
              OUT / 'RASTER_INDEX.json', HERE / 'filter_rows.py', HERE / 'raster_index.py', D7 / 'build_rows.py'):
        inputs[str(p)] = fsha(p)
    inputs[str(DB)] = DB_SHA
    rindex = json.loads((OUT / 'RASTER_INDEX.json').read_text())['rasters']
    rooms, _ = d.room_authority()
    inputs[str(d.BASE / 'alias_inputs/out/TIERED_ALIAS_MAP.json')] = fsha(d.BASE / 'alias_inputs/out/TIERED_ALIAS_MAP.json')
    con = sqlite3.connect(DB.as_uri() + '?mode=ro&immutable=1', uri=True)
    rows = [json.loads(l) for l in open(D7 / 'out/NEW_ROWS.jsonl')]
    maps = [json.loads(l) for l in open(D7 / 'out/SOURCE_MAP.jsonl')]
    assert [r['qid'] for r in rows] == [m['qid'] for m in maps]

    # Family-wide surface usage decides whether bare wall/floor/ceiling count as non-object labels.
    survey = json.loads((D7 / 'out/SURVEY.json').read_text())
    fam_names = C.Counter(n.strip().lower() for m in survey['rows'] for n in m['objects'])
    surface_bare = {s: fam_names.get(s, 0) for s in SURFACES}
    surface_compound = {n: c for n, c in sorted(fam_names.items()) if set(n.split()) & set(SURFACES) and n not in SURFACES}
    placeholders = dict(PLACEHOLDERS)
    if not any(surface_bare.values()):
        for s in SURFACES:
            placeholders[s] = 'bare surface; the direction family never names it as an object'
    family_placeholder_rows = sum(1 for m in survey['rows'] if any(n.strip().lower() in placeholders for n in m['objects']))

    stats = {k: C.Counter() for k in ('R1', 'R2', 'R3')}
    per_row, keep, no_raster = [], [], []
    cache = {}
    for r, m in zip(rows, maps):
        s_raw = con.execute('select row from rows where i=?', (m['source_i'],)).fetchone()[0]
        s = json.loads(s_raw)
        assert hashlib.sha256(s_raw.encode()).hexdigest() == m['source_row_sha256']
        names = list(m['objects'])
        rec = dict(qid=r['qid'], source_qid=s['qid'], objects=names)
        drop = []
        for who, row in (('twin', r), ('source', s)):
            stats['R1'][who + '_checked'] += 1
            hits = [n for n in names if n.strip().lower() in placeholders]
            if hits:
                stats['R1'][who + '_removed'] += 1; drop.append('R1:' + who + ':' + ','.join(hits))
        can, _ = rooms.canonical(s)
        assert can and rooms.canonical(r)[0] == can
        ras = rindex.get(can)
        aligned = False
        if ras:
            if can not in cache:
                cache[can] = dict(np.load(ras['path']))
            z = cache[can]
            aligned = z['frame_indices'].tolist() == s['student_input']['frame_indices'] == r['student_input']['frame_indices']
        rec.update(capture=can, raster=ras['path'] if ras else None, raster_sha256=ras['sha256'] if ras else None, frames_aligned=aligned)
        # R2: cited (object, frame) facts in either trace.
        cites = {who: [ln for ln in row['target'].split('\n') if FRAME_CITE.search(ln)] for who, row in (('twin', r), ('source', s))}
        for who in ('twin', 'source'):
            stats['R2'][who + '_checked'] += 1
            if cites[who]:
                stats['R2'][who + '_citing'] += 1
                stats['R2'][who + ('_with_raster' if aligned else '_listed_without_raster')] += 1
        rec['r2_cited_lines'] = cites
        # R3: every named object visible in at least one sampled frame.
        for who in ('twin', 'source'):
            stats['R3'][who + '_checked'] += 1
            stats['R3'][who + ('_with_raster' if aligned else '_listed_without_raster')] += 1
        if aligned:
            covs = {n: coverage(z, n) for n in names}
            rec['r3'] = {}
            unmatched = [n for n, c in covs.items() if c is None]
            for n, c in covs.items():
                if c is None:
                    rec['r3'][n] = 'NAME_NOT_IN_RASTER_LABELS'; continue
                vis = [f for f, (v, ok) in enumerate(zip(c['per_frame'], c['valid'])) if ok and v >= VISIBLE]
                rec['r3'][n] = dict(ids=c['ids'], max_coverage=max(c['per_frame']), visible_frames=len(vis),
                                    any_pixel=any(v > 0 for v in c['per_frame']), invalid_frames=c['valid'].count(False))
            absent = [n for n, v in rec['r3'].items() if isinstance(v, dict) and v['visible_frames'] == 0]
            undecidable = [n for n in absent if rec['r3'][n]['invalid_frames']]
            absent = [n for n in absent if n not in undecidable]
            if unmatched or undecidable:
                rec['r3_unverifiable'] = dict(unmatched=unmatched, invalid_frames=undecidable)
            if absent:
                for who in ('twin', 'source'):
                    stats['R3'][who + '_removed'] += 1
                    stats['R3'][who + '_removed_zero_pixels' if not any(rec['r3'][n]['any_pixel'] for n in absent) else who + '_removed_sliver_only'] += 1
                drop.append('R3:' + ','.join(absent))
            elif unmatched or undecidable:
                for who in ('twin', 'source'):
                    stats['R3'][who + '_raster_but_unverifiable'] += 1
        else:
            no_raster.append(dict(qid=r['qid'], source_qid=s['qid'], capture=can,
                                  reason='no local raster for capture' if not ras else 'raster frames differ from row frames'))
        rec['drop'] = drop
        per_row.append(rec)
        if not drop:
            keep.append((r, m))
    assert all(stats['R2'][k] == 0 for k in ('twin_citing', 'source_citing')), stats['R2']
    OUT.mkdir(exist_ok=True)
    (OUT / 'NEW_ROWS.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r, _ in keep))
    (OUT / 'SOURCE_MAP.jsonl').write_text(''.join(json.dumps(m, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for _, m in keep))
    teach = json.loads((D7 / 'out/TEACHING_SET.json').read_text())
    kept_src = {m['source_qid'] for _, m in keep}
    teach_f = dict(command='nice -n 10 python filter_rows.py', input_sha256=inputs, status='PASS', new_rows=len(keep),
                   existing_source_rows=len(keep), rows=2 * len(keep),
                   existing_sources=[x for x in teach['existing_sources'] if x['qid'] in kept_src],
                   new_rows_pin=dict(path=str(OUT / 'NEW_ROWS.jsonl'), sha256=fsha(OUT / 'NEW_ROWS.jsonl')),
                   instruction=teach['instruction'])
    assert len(teach_f['existing_sources']) == len(keep)
    (OUT / 'TEACHING_SET.json').write_text(json.dumps(teach_f, indent=1, sort_keys=True) + '\n')
    cells = C.Counter((m['family'], m['label']) for _, m in keep)
    value = dict(command='nice -n 10 python filter_rows.py', input_sha256=inputs,
                 thresholds=dict(r2_cited_frame_min_coverage=CITE, r3_visible_min_coverage=VISIBLE,
                                 raster='240x320 instance raster; coverage = pixels of every instance carrying the name / frame pixels'),
                 r1=dict(placeholder_labels=placeholders, matching='whole named object, case-folded',
                         surfaces_bare_uses_in_direction_family=surface_bare,
                         surfaces_compound_uses_in_direction_family=surface_compound,
                         direction_family_rows_with_placeholder=family_placeholder_rows,
                         direction_family_rows=len(survey['rows']), direction_family_names=len(fam_names)),
                 stats={k: dict(v) for k, v in stats.items()},
                 rows_in=len(rows), rows_out=len(keep), cells_out={f'{a}/{b}': n for (a, b), n in sorted(cells.items())},
                 dropped=[x for x in per_row if x['drop']],
                 raster_unverifiable=[dict(qid=x['qid'], **x['r3_unverifiable']) for x in per_row if x.get('r3_unverifiable') and not x['drop']],
                 listed_without_raster=dict(rows=len(no_raster), reason_counts=dict(C.Counter(x['reason'] for x in no_raster)),
                                            captures=len({x['capture'] for x in no_raster})),
                 outputs={str(OUT / n): fsha(OUT / n) for n in ('NEW_ROWS.jsonl', 'SOURCE_MAP.jsonl', 'TEACHING_SET.json')})
    (OUT / 'NO_RASTER_QIDS.jsonl').write_text(''.join(json.dumps(x, sort_keys=True) + '\n' for x in no_raster))
    value['outputs'][str(OUT / 'NO_RASTER_QIDS.jsonl')] = fsha(OUT / 'NO_RASTER_QIDS.jsonl')
    (OUT / 'FILTER_ROWS.json').write_text(json.dumps(dict(command=value['command'], input_sha256=inputs, rows=per_row), sort_keys=True) + '\n')
    value['outputs'][str(OUT / 'FILTER_ROWS.json')] = fsha(OUT / 'FILTER_ROWS.json')
    (OUT / 'FILTER.json').write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(stats=value['stats'], rows_out=len(keep), cells=value['cells_out'],
                          unverifiable=len(value['raster_unverifiable']), r1=dict(bare=surface_bare, fam_rows=family_placeholder_rows)), indent=1))


if __name__ == '__main__':
    main()
