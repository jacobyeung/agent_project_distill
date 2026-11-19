"""Reviewer recipe, not executed by build24j. Requires authenticated P inputs."""
import argparse
from copy import deepcopy
import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import resource
import sqlite3
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--tree', required=True)
parser.add_argument('--n-config', required=True, help='Authenticated N config containing P p_run pins')
parser.add_argument('--paths', required=True, help='SHA256 to staged local path map')
parser.add_argument('--output', required=True, help='Fresh output at the exact reviewed logical path')
args = parser.parse_args()
sys.path.insert(0, str(Path(args.tree).resolve()))
resource.setrlimit(resource.RLIMIT_AS, (19 * 1024**3, 19 * 1024**3))
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from student_pilot.p3_provenance import load, pinned, digest, write, file_pin
from student_pilot.r1_persisted import scope
from student_pilot.s1_routing import build

ROUTING = 'ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984'
with scope(load(args.paths)):
    n = load(args.n_config)
    p_pin = n['r1_training']['p_run']['config']
    p = load(pinned(p_pin))
    pin = p['streams']['routing']
    if pin['sha256'] != ROUTING:
        raise ValueError('P_TRAINED_ROUTING_PIN_DIFFERS')
    receipt = load(pinned(pin))
    if not receipt['database']['sha256'].startswith('4e8e6c04'):
        raise ValueError('P_TRAINED_ROUTING_DATABASE_DIFFERS')
    # Resolve every referenced byte through pinned(); a prefix is never enough
    # to authenticate the database. The complete hash comes from ca0616db.
    p_db = pinned(receipt['database'])
    materialization = load(pinned(receipt['materialization']))
    cfg = deepcopy(p)
    cfg['s1_routing'] = materialization['inputs']
    cfg['streams']['routing'] = materialization['legacy']
    regenerated = build(cfg, Path(args.output), materialization['division'], materialization['base_model'])
    actual_db = pinned(regenerated['database'])
    hashes = [hashlib.sha256(), hashlib.sha256()]
    count = 0
    connections = [sqlite3.connect(path.as_uri()+'?mode=ro', uri=True) for path in (p_db, actual_db)]
    try:
        readers = [con.execute('SELECT i,row,target FROM rows ORDER BY i') for con in connections]
        for before, after in zip_longest(*readers):
            if before != after:
                raise ValueError('P_TRAINED_SELECTED_ROW_BYTES_OR_ORDER_DIFFER:'+str(count))
            for value, accumulator in zip((before, after), hashes):
                accumulator.update((json.dumps(value, separators=(',', ':'))+'\n').encode())
            count += 1
    finally:
        for con in connections:
            con.close()
    write(Path(args.output)/'reviewer_selection_evidence.json', dict(
        source_p_config=p_pin, source_routing=pin, source_database=receipt['database'],
        regenerated_database=regenerated['database'], regenerated_sha256=digest(regenerated),
        rows=count, selected_rows_equal=True, selected_row_hashes=[h.hexdigest() for h in hashes],
        scope='P regeneration only; N runtime receipt digest needs separate exact-path approval'))
