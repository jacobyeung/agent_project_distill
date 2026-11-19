"""Recheck BINDING.jsonl from raw inputs without bind.py's code paths (except N's digest for the row hash)."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1')
from student_pilot.p3_provenance import digest  # noqa: E402

D7F = Path('/scratch/jjyeung/orch_n30/sb_rowD7f/out')
DB = '/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
LISTS = {'u_union': '/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json',
         'u.json': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/inputs/u.json',
         'n.json': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json',
         'z.json': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/z.json'}
FIELDS = {'twin_key', 'source_key', 'source_room', 'twin_sha256', 'room_authority'}

raw = (HERE / 'BINDING.jsonl').read_bytes()
lines = [json.loads(x) for x in raw.decode().splitlines()]
keys = [x['twin_key'] for x in lines]
twins = {r['qid']: r for r in map(json.loads, (D7F / 'NEW_ROWS.jsonl').read_text().splitlines())}
maps = {m['qid']: m for m in map(json.loads, (D7F / 'SOURCE_MAP.jsonl').read_text().splitlines())}
listed = {n: {json.loads(x)['row_key'] for x in Path(p).read_text().splitlines() if x.strip()} for n, p in LISTS.items()}
v7 = {}
con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
for i, row in con.execute('SELECT i, row FROM rows'):
    qid = json.loads(row)['qid']
    v7.setdefault(qid, []).append(i)
checks = dict(
    lines=len(lines), sorted=keys == sorted(keys), unique=len(set(keys)) == len(keys),
    fields_exact=all(set(x) == FIELDS for x in lines), covers_all_twins=set(keys) == set(twins),
    twin_sha256_is_N_digest=sum(digest(twins[x['twin_key']]) == x['twin_sha256'] for x in lines),
    source_key_is_label_row_key=sum(twins[x['twin_key']]['label_row_keys'] == [x['source_key']] for x in lines),
    source_once_in_v7_at_source_i=sum(v7.get(x['source_key']) == [maps[x['twin_key']]['source_i']] for x in lines),
    source_room_equals_D7f_map_room=sum(maps[x['twin_key']]['room'] == x['source_room'] for x in lines),
    list_hits={n: sum(x['source_key'] in s or x['twin_key'] in s for x in lines) for n, s in listed.items()},
    list_sizes={n: len(s) for n, s in listed.items()},
    authority_tags=sorted({x['room_authority'] for x in lines}),
    binding_sha256=hashlib.sha256(raw).hexdigest())
n = len(twins)
ok = (checks['lines'] == n == 7971 and checks['sorted'] and checks['unique'] and checks['fields_exact']
      and checks['covers_all_twins'] and all(checks[k] == n for k in (
          'twin_sha256_is_N_digest', 'source_key_is_label_row_key', 'source_once_in_v7_at_source_i',
          'source_room_equals_D7f_map_room')) and not any(checks['list_hits'].values()))
checks['status'] = 'PASS' if ok else 'FAIL'
(HERE / 'work/VERIFY_BINDING.json').write_text(json.dumps(checks, indent=1, sort_keys=True) + '\n')
print(json.dumps(checks, indent=1, sort_keys=True))
sys.exit(0 if ok else 1)
