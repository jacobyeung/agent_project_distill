"""Bind each sb_rowD7f direction twin to its pinned v7 source key, source room and N row digest.

Run: nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 \
     /scratch/jjyeung/envs/p1cpu/bin/python bind.py [--out DIR]
Keys, row digests, rooms and removals use N's sealed functions (tree seal 780ca7b4) unchanged.
"""
import argparse
import collections
import hashlib
import json
import sqlite3
import sys
import tarfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
TREE = W / 'w20/work/tree_r1'
SEAL = W / 'w20/out/TREE_SEAL.json'
CONFIG = W / 'w20/work/build20/inputs/config.json'
D7F = Path('/scratch/jjyeung/orch_n30/sb_rowD7f/out')
STORE_DIR = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
U_UNION = Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json')
TIERED = Path('/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json')
EXPECT = {
    'seal': '780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278',
    'room_audit': 'dd60517b4f5c2fc16e91d10a4569389a7ba9e4f137b78996548a19dd2b76a326',
    'tiered': '7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b',
    'u_union': '1c7c930d1a533a3b18b08486bc2c2a9b49086b0809492963498b369ac8be45a2',
    'z': 'caba6a5695781491036de5b3acdb20db2d42ab581e5775fec3fe07fbd2114aad',
}
sys.path.insert(0, str(TREE))
from student_pilot import r1_rooms  # noqa: E402
from student_pilot.p3_provenance import digest, encoded, sha256  # noqa: E402
from student_pilot.row_removals import Removals, row_keys  # noqa: E402

PINS = {}


def pin(path, expected=None):
    path = str(Path(path).resolve())
    if path not in PINS:
        PINS[path] = sha256(path)
    if expected is not None and PINS[path] != expected:
        raise SystemExit(f'PIN MISMATCH {path}: {PINS[path]} != {expected}')
    return dict(path=path, sha256=PINS[path])


def load(path, expected=None):
    pin(path, expected)
    return json.loads(Path(path).read_text())


def same_pins(a, b):
    return {k: v['sha256'] for k, v in a.items()} == {k: v['sha256'] for k, v in b.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(HERE))
    out = Path(parser.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    pin(__file__)

    # N's sealed code and build-20 configuration.
    seal = load(SEAL)
    assert seal['tree_sha256'] == EXPECT['seal'], seal['tree_sha256']
    cfg = load(CONFIG)
    value = cfg['r1_training']
    audit = load(value['room_audit']['path'], EXPECT['room_audit'])
    assert value['room_audit']['sha256'] == EXPECT['room_audit']
    assert same_pins(audit['authority'], value['room_authority']), 'audit authority differs from build-20 config'
    receipt = load(cfg['streams']['vqa']['path'], cfg['streams']['vqa']['sha256'])
    assert receipt['database']['sha256'] == r1_rooms.STORE == audit['store']['database']['sha256']
    manifest = pin(STORE_DIR / 'BUILD_MANIFEST.json', receipt['source']['sha256'])
    db = pin(STORE_DIR / 'vqa/rows.sqlite', r1_rooms.STORE)
    for p in value['room_authority'].values():
        pin(p['path'], p['sha256'])

    # Removal lists: u.json (V7_K1_LIST), n.json (N_LIST), z.json from build-20 remove_files, plus u_union.
    remove_files = cfg['remove_files']
    by_name = {Path(p['path']).name: p for p in remove_files}
    u_pin, n_pin, z_pin = by_name['u.json'], by_name['n.json'], by_name['z.json']
    assert u_pin['sha256'] == r1_rooms.V7_K1_LIST == value['v7_k1_removal']['sha256']
    assert n_pin['sha256'] == r1_rooms.N_LIST and z_pin['sha256'] == EXPECT['z']
    union_pin = pin(U_UNION, EXPECT['u_union'])
    for p in remove_files:
        pin(p['path'], p['sha256'])
    lists = {'u_union': Removals([union_pin]), 'u.json': Removals([u_pin]),
             'n.json': Removals([n_pin]), 'z.json': Removals([z_pin])}
    list_keys = {name: r.keys[0] for name, r in lists.items()}
    assert len(list_keys['u_union']) == 4959 and len(list_keys['u.json']) == 2637

    # Room authorities: strict Rooms with the audit's pins; tiered map for strict-unresolved rows.
    strict = r1_rooms.Rooms(value['room_authority'])
    tiered_map = load(TIERED, EXPECT['tiered'])
    assert tiered_map['complete'] is True and not tiered_map['conflicts'] and not tiered_map['quarantined_tokens']
    assert tiered_map['inputs'][str(Path(db['path']))]['sha256'] == r1_rooms.STORE
    tiered = r1_rooms.Rooms(value['room_authority'])
    tiered.aliases = {k: v['canonical'] for k, v in tiered_map['aliases'].items()}
    tier_of = {k: v['tier'] for k, v in tiered_map['aliases'].items()}
    token = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}

    def room_status(room):
        return 'r0' if room in strict.r0 else 'k1_heldout' if room in strict.k1 else 'ok'

    def resolve(row):
        status, canonical, how = strict.status(row)
        if status != 'unresolved':
            return strict.room(canonical), 'strict_rooms_dd60517b_authority:' + how
        canonical, how = tiered.canonical(row)
        if not canonical:
            return None, 'unresolved'
        tier = tier_of[token.get(row.get('dataset', ''), row.get('dataset', '')) + '/' + row.get('scene', '')] \
            if how == 'alias' else how
        return tiered.room(canonical), f'tiered_alias_map_7f50287b_tier_{tier}:strict_unresolved_in_dd60517b'

    # D7f deliverables; the archive must carry the same row and map bytes.
    rows_path, map_path = D7F / 'NEW_ROWS.jsonl', D7F / 'SOURCE_MAP.jsonl'
    for name in ('NEW_ROWS.jsonl', 'SOURCE_MAP.jsonl', 'CHECKS.json', 'FILTER_REPORT.md', 'sb_rowD7f.tar.sha256'):
        pin(D7F / name)
    tar_sha = (D7F / 'sb_rowD7f.tar.sha256').read_text().split()[0]
    pin(D7F / 'sb_rowD7f.tar', tar_sha)
    tar_members = {}
    with tarfile.open(D7F / 'sb_rowD7f.tar') as tar:
        for member in tar.getmembers():
            if member.isfile() and Path(member.name).name in ('NEW_ROWS.jsonl', 'SOURCE_MAP.jsonl'):
                h = hashlib.sha256()
                with tar.extractfile(member) as f:
                    for block in iter(lambda: f.read(1 << 22), b''):
                        h.update(block)
                tar_members[member.name] = h.hexdigest()
    tar_ok = {n: any(Path(m).name == n and s == PINS[str((D7F / n).resolve())] for m, s in tar_members.items())
              for n in ('NEW_ROWS.jsonl', 'SOURCE_MAP.jsonl')}
    assert all(tar_ok.values()), tar_members
    twin_lines = rows_path.read_text().splitlines()
    maps = [json.loads(line) for line in map_path.read_text().splitlines()]
    twins = [json.loads(line) for line in twin_lines]
    assert len(twins) == len(maps) == 7971
    wanted = {m['source_qid'] for m in maps}
    twin_qids = {t['qid'] for t in twins}

    # One read-only pass over v7: source lookup, key census, and both room censuses.
    removals_cfg = Removals(remove_files)
    removals_aug = Removals([*remove_files, union_pin])
    strict_counts, strict_hows, tiered_counts = collections.Counter(), collections.Counter(), collections.Counter()
    qid_count, sources, twin_key_collisions = collections.Counter(), {}, collections.Counter()
    con = sqlite3.connect(Path(db['path']).as_uri() + '?mode=ro&immutable=1', uri=True)
    for i, raw in con.execute('SELECT i, row FROM rows ORDER BY i'):
        row = json.loads(raw)
        qid_count[row['qid']] += 1
        for key in row_keys(row) & twin_qids:
            twin_key_collisions[key] += 1
        if row['qid'] in wanted:
            sources[row['qid']] = (i, row, hashlib.sha256(raw.encode()).hexdigest())
        status, canonical, how = strict.status(row)
        strict_counts['rows'] += 1; strict_counts[status] += 1; strict_hows[how] += 1
        if status in ('k1_heldout', 'r0'):
            strict_counts['unremoved_hits'] += int(removals_cfg.keep(row))
        room, _ = resolve(row)
        tstatus = room_status(room) if room else 'unresolved'
        tiered_counts['rows'] += 1; tiered_counts[tstatus] += 1
        if tstatus in ('k1_heldout', 'r0'):
            tiered_counts['unremoved_hits'] += int(removals_aug.keep(row))
    con.close()
    keys = ('rows', 'ok', 'k1_heldout', 'r0', 'unresolved', 'unremoved_hits')
    store = audit['store']
    strict_repro = {k: strict_counts[k] for k in keys}
    assert strict_repro == {k: store[k] for k in keys}, (strict_repro, {k: store[k] for k in keys})
    assert dict(strict_hows) == store['canonical_from'], (dict(strict_hows), store['canonical_from'])

    # Per-twin binding and checks.
    counts, authorities, dropped, binding = collections.Counter(), collections.Counter(), [], []
    hits = {name: dict(source_key=0, twin_row_keys=0) for name in list_keys}
    cfg_hits = collections.Counter()
    for line, twin, m in zip(twin_lines, twins, maps, strict=True):
        reasons = []
        twin_key, source_key = twin['qid'], m['source_qid']
        assert m['qid'] == twin_key and twin['provenance']['sb_rowD7']['source_qid'] == source_key
        counts['label_row_keys_is_source'] += int(twin.get('label_row_keys') == [source_key])
        twin_keys = row_keys(twin)
        counts['twin_row_keys_eq_twin_and_source'] += int(twin_keys == {twin_key, source_key})
        found = sources.get(source_key)
        if not found or qid_count[source_key] != 1:
            reasons.append('source_absent_or_not_unique_in_v7')
        else:
            i, source, raw_sha = found
            counts['source_i_matches'] += int(i == m['source_i'] == twin['provenance']['sb_rowD7']['source_store_i'])
            counts['source_raw_sha_matches'] += int(raw_sha == m['source_row_sha256']
                                                    == twin['provenance']['sb_rowD7']['source_row_sha256'])
            counts['source_row_keys_eq_qid'] += int(row_keys(source) == {source_key})
            counts['dataset_scene_equal'] += int((source['dataset'], source['scene']) == (twin['dataset'], twin['scene']))
            source_room, authority = resolve(source)
            twin_room, twin_authority = resolve(twin)
            if source_room is None:
                reasons.append('source_room_unresolved')
            if twin_room != source_room or twin_authority != authority:
                reasons.append('twin_room_differs_from_source_room')
            counts['source_map_room_matches'] += int(source_room == m['room'])
            if authority.startswith('strict'):
                tc, _ = tiered.canonical(source)
                counts['strict_resolved_tiered_agrees'] += int(tiered.room(tc) == source_room)
            for name, keyset in list_keys.items():
                if row_keys(source) & keyset:
                    hits[name]['source_key'] += 1
                    reasons.append('source_key_in_' + name)
                if twin_keys & keyset:
                    hits[name]['twin_row_keys'] += 1
            for index in removals_cfg.match(twin):
                cfg_hits[Path(remove_files[index]['path']).name] += 1
            status = room_status(source_room) if source_room else 'unresolved'
            counts['room_status_' + status] += 1
            if status in ('k1_heldout', 'r0') and not (row_keys(source) & list_keys['u_union']):
                counts['twin_unremoved_hits'] += 1
            twin_sha = digest(twin)
            counts['twin_line_is_canonical_json'] += int(hashlib.sha256(line.encode()).hexdigest() == twin_sha)
            counts['twin_line_equals_encoded'] += int(line == encoded(twin))
        if reasons:
            dropped.append(dict(twin_key=twin_key, source_key=source_key, reasons=reasons))
            continue
        authorities[authority] += 1
        binding.append(dict(twin_key=twin_key, source_key=source_key, source_room=source_room,
                            twin_sha256=twin_sha, room_authority=authority))
    binding.sort(key=lambda r: r['twin_key'])
    assert len({r['twin_key'] for r in binding}) == len(binding)
    text = ''.join(encoded(r) + '\n' for r in binding)
    (out / 'BINDING.jsonl').write_text(text)
    binding_sha = hashlib.sha256(text.encode()).hexdigest()

    # Every module loaded from N's tree must match the seal.
    loaded = {}
    for module in list(sys.modules.values()):
        f = getattr(module, '__file__', None)
        if f and str(Path(f).resolve()).startswith(str(TREE) + '/'):
            rel = str(Path(f).resolve().relative_to(TREE))
            loaded[rel] = pin(f, seal['files'][rel])['sha256']

    n = len(twins)
    checks = dict(
        twins_in=n, bound=len(binding), dropped=len(dropped),
        source_in_v7_unique=n - sum('source_absent_or_not_unique_in_v7' in d['reasons'] for d in dropped),
        twin_room_equals_source_room=n - sum('twin_room_differs_from_source_room' in d['reasons'] for d in dropped),
        removal_hits=hits, build20_remove_files_hits_on_twin_row_keys=dict(cfg_hits),
        twin_key_collisions_with_v7_row_keys=sum(twin_key_collisions.values()),
        per_twin=dict(counts), room_authority=dict(authorities),
        unremoved=dict(twins=counts['twin_unremoved_hits'], v7_tiered_with_u_union=tiered_counts['unremoved_hits'],
                       augmented_total=counts['twin_unremoved_hits'] + tiered_counts['unremoved_hits']),
        v7_strict_census_reproduces_dd60517b=dict(counts=strict_repro, canonical_from=dict(strict_hows)),
        v7_tiered_census=dict(tiered_counts),
        tar_members=tar_members)
    expected = dict(
        bound=n, dropped=0, source_in_v7_unique=n, twin_room_equals_source_room=n,
        twin_key_collisions_with_v7_row_keys=0,
        **{'per_twin.' + k: n for k in ('label_row_keys_is_source', 'twin_row_keys_eq_twin_and_source', 'source_i_matches',
                                        'source_raw_sha_matches', 'source_row_keys_eq_qid', 'dataset_scene_equal',
                                        'source_map_room_matches')},
        unremoved_augmented_total=0, removal_source_key_hits=0)
    actual = dict(checks, **{'per_twin.' + k: v for k, v in counts.items()},
                  unremoved_augmented_total=checks['unremoved']['augmented_total'],
                  removal_source_key_hits=sum(h['source_key'] for h in hits.values()))
    verdict = {k: dict(expected=v, actual=actual.get(k, 0), status='PASS' if actual.get(k, 0) == v else 'FAIL')
               for k, v in expected.items()}
    record = dict(
        schema='twin-v7-source-binding-v1', binding=dict(path=str(out / 'BINDING.jsonl'), sha256=binding_sha, lines=len(binding)),
        status='PASS' if all(v['status'] == 'PASS' for v in verdict.values()) else 'FAIL', verdict=verdict,
        definitions=dict(
            twin_key="twin row['qid'] (r1_rooms.census row_key=row['qid']); row_removals.row_keys(twin) = {twin_key, source_key}",
            source_key="v7 source row['qid'] = row_removals.row_keys(source) (u_union row_key = store qid)",
            twin_sha256='student_pilot.p3_provenance.digest(twin row): sha256 of json.dumps(sort_keys=True, separators=(",",":"), allow_nan=False)',
            source_room='r1_rooms.Rooms.room(canonical); canonical from strict Rooms.status with the build-20/dd60517b room_authority pins; '
                        'if strict-unresolved, Rooms.canonical with aliases replaced by TIERED_ALIAS_MAP 7f50287b canonicals',
            unremoved='rows whose room is K1 held-out or R0 and that no removal list removes; v7 uses build-20 remove_files plus u_union'),
        checks=checks, dropped=dropped, tree_modules=loaded, inputs=PINS,
        command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 '
                '/scratch/jjyeung/envs/p1cpu/bin/python bind.py')
    (out / 'BINDING_CHECKS.json').write_text(json.dumps(record, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(status=record['status'], binding=record['binding'], verdict=verdict, room_authority=dict(authorities),
                          removal_hits=hits, unremoved=checks['unremoved'], v7_tiered=dict(tiered_counts)), indent=1))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
