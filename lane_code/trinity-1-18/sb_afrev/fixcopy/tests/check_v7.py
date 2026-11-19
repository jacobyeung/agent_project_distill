"""Verify the requested v7 regression and all persisted row/count relationships."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import store_room_audit as audit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--audit', type=Path, default=ROOT/'out/v7/audit.json')
parser.add_argument('--out', type=Path, default=ROOT/'out/V7_CHECK.json')
args = parser.parse_args()
ledger = audit.Inputs()
ledger.pin(Path(__file__))
ledger.pin(ROOT/'store_room_audit.py')
report = ledger.document(args.audit)
assert report['complete'] is True and report['status'] == 'PASS'
assert report['rows'] == report['resolved_rows'] == 204413
assert report['unresolved_rows'] == report['unresolved_token_count'] == 0
expected = {'R0': 0, 'withheld-80': 0, 'BENCH v2': 0, 'dev-S1': 0, 'K1': 4959}
assert report['hits'] == expected, report['hits']
assert report['hits_by_tier']['K1'] == {'A': 110, 'B': 4770, 'C': 79}
assert report['inputs'][report['store']]['sha256'] == '210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
rows_path = args.audit.parent/report['row_records']['path']
ledger.pin(rows_path, report['row_records']['sha256'])
rooms, _, _, _, _, _ = audit.prepare(Path(report['tree']), ROOT/'inputs/lists', ledger)
counts, tiers, streams, families, joint = Counter(), Counter(), Counter(), Counter(), Counter()
rows = 0
with sqlite3.connect(rows_path.resolve().as_uri()+'?mode=ro&immutable=1', uri=True) as conn:
    for scene, room, tier, stream, family, hits, reason in conn.execute('SELECT scene,room,tier,stream,family,hits,unresolved_reason FROM rows'):
        assert scene and room and reason is None
        assert rooms.room(scene) == room
        rows += 1
        for name in json.loads(hits):
            counts[name] += 1
            tiers[(name,tier)] += 1
            streams[(name,stream)] += 1
            families[(name,family)] += 1
            joint[(name,tier,stream,family)] += 1
    metadata = json.loads(conn.execute("SELECT value FROM metadata WHERE key='audit'").fetchone()[0])
    assert metadata['inputs'] == report['inputs']
assert rows == report['rows']
for name in audit.NAMES:
    assert counts[name] == report['hits'][name]
    for exported, actual in [(report['hits_by_tier'][name],tiers), (report['hits_by_stream'][name],streams), (report['hits_by_family'][name],families)]:
        assert exported == {key[1]: value for key,value in actual.items() if key[0] == name}
assert joint == Counter({(r['list'],r['tier'],r['stream'],r['family']):r['rows'] for r in report['hits_by_list_tier_stream_family']})
result = dict(schema='auditfix-v7-check-v1', command=' '.join([sys.executable, '-s', str(Path(__file__).resolve()), *sys.argv[1:]]),
              inputs=ledger.pins, status='PASS', rows_checked=rows, hits=expected, k1_by_tier=report['hits_by_tier']['K1'],
              assertions='All row scenes reproduce persisted rooms; all list/tier/stream/family marginals and joint counts match persisted hits.')
args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print('PASS:', rows, 'persisted scenes/rooms;', expected)
