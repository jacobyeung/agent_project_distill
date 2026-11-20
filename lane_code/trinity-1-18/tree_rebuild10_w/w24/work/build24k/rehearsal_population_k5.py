"""Supply complete bounded fixture databases through authenticated stream pins."""
from collections import Counter
from contextlib import closing
from copy import deepcopy
from pathlib import Path
import ast
import json
import os
import sqlite3


def bound_population(root, capacity, cfg, J):
    assert os.uname().nodename == 'trinity-1-18'
    native = root/'source/student_pilot/r2_scene_bindings.py'
    tree = ast.parse(native.read_text())
    decoded = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'decoded')
    comparison = next(n for n in ast.walk(decoded) if isinstance(n, ast.Compare)
                      and isinstance(n.left, ast.Name) and n.left.id == 'index')
    assert len(comparison.comparators) == 1 and isinstance(comparison.ops[0], ast.GtE)
    limit = ast.literal_eval(comparison.comparators[0])
    assert limit == 2000, 'Reassess fixture sizing for a different native limit'
    folder = root/'fixture'
    folder.mkdir()
    records = []

    def bounded(pin, name):
        source_receipt = Path(pin['path'])
        assert source_receipt.is_relative_to(capacity) and J.sha(source_receipt) == pin['sha256']
        old = J.load(source_receipt)
        source_db = Path(old['database']['path'])
        assert source_db.is_relative_to(capacity) and J.sha(source_db) == old['database']['sha256']
        destination = folder/name
        destination.mkdir()
        db_path = destination/'rows.sqlite'
        assert not db_path.exists()
        with closing(sqlite3.connect(source_db.as_uri()+'?mode=ro&immutable=1', uri=True)) as original:
            original_count = original.execute('SELECT COUNT(*) FROM rows').fetchone()[0]
            assert original_count == old['count'] and original_count >= limit
            schema = original.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='rows'").fetchone()[0]
            selected = original.execute('SELECT i,row,target FROM rows ORDER BY i LIMIT ?', (limit,)).fetchall()
        assert [r[0] for r in selected] == list(range(limit))
        with closing(sqlite3.connect(db_path)) as target:
            # Persistent journal mode avoids SQLite removing a temporary journal.
            target.execute('PRAGMA journal_mode=PERSIST')
            target.execute(schema)
            target.executemany('INSERT INTO rows VALUES (?,?,?)', selected)
            target.commit()
            assert target.execute('SELECT COUNT(*) FROM rows').fetchone()[0] == limit
        receipt = deepcopy(old)
        receipt['count'] = limit
        receipt['database'] = dict(path=str(db_path), sha256=J.sha(db_path))
        values = [json.loads(row) for _, row, _ in selected]
        if 'types' in receipt:
            # Routing's original sole type is retained in this synthetic subset.
            assert len(old['types']) == 1 and sum(old['types'].values()) == original_count
            receipt['types'] = {next(iter(old['types'])): limit}
        if 'head_layouts' in receipt:
            receipt['head_layouts'] = dict(Counter(v.get('head_layout', v.get('routing', {}).get('head_layout')) for v in values))
            if set(receipt['head_layouts']) == {None}:
                assert len(old['head_layouts']) == 1
                receipt['head_layouts'] = {next(iter(old['head_layouts'])): limit}
        if 'target_filter' in receipt:
            # Preserve the native reader's required filter settings; the host
            # recalculates removal and target counts from these actual rows.
            receipt['target_filter'] = {'settings': old['target_filter']['settings']}
        receipt['fixture_subset'] = dict(source_receipt=pin, source_database=old['database'],
                                        selection='first rows in native i order', rows=limit)
        new_pin = J.write(destination/'receipt.json', receipt)
        records.append(dict(source=name, original_receipt=pin, original_database=old['database'],
                            original_count=original_count, receipt=new_pin,
                            database=receipt['database'], count=limit,
                            row_and_target_bytes_preserved=True))
        return new_pin

    for stream in ('routing', 'pointing', 'vqa'):
        cfg['streams'][stream] = bounded(cfg['streams'][stream], stream)
    pose_pin = cfg['streams']['pose']
    assert J.sha(Path(pose_pin['path'])) == pose_pin['sha256']
    pose = deepcopy(J.load(pose_pin['path']))
    assert len(pose['sources']) == 2
    for index, source in enumerate(pose['sources']):
        assert source['kind'] == 'rows'
        source['receipt'] = bounded(source['receipt'], 'pose'+str(index))
        if 'count' in source: source['count'] = limit
    cfg['streams']['pose'] = J.write(folder/'pose.json', pose)
    J.write(root/'BOUNDED_POPULATION.json', dict(native_source=str(native), native_sha256=J.sha(native),
            host=os.uname().nodename, native_limit=limit, records=records,
            native_limit_unchanged=True, complete_fixture_populations=True,
            sampling_capacity_gate_unchanged=True,
            scope='Synthetic fixture subsets; not a census of the full source stores.'))
