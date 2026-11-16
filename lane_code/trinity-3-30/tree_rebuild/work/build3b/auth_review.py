from pathlib import Path
L=Path(__file__).resolve().parents[2]
p=L/'work/tree_r1/student_pilot/r2_scene_bindings.py'
s=p.read_text().replace('from collections import Counter','from collections import Counter\nfrom contextlib import closing').replace('import os\n','import os\nimport sqlite3\n')
a=s.index('def rows(pin):');b=s.index('\n\ndef rebuild_pool',a)
s=s[:a]+'''def decoded(lines):
    for index, line in enumerate(lines):
        if index >= 2000 and os.uname().nodename.startswith('trinity'):
            raise ValueError('Local metadata slices must contain at most 2000 rows per family')
        value = json.loads(line)
        yield value.get('row', value)


def rows(pin):
    path = pinned(pin)
    with path.open('rb') as handle:
        header = handle.read(16)
    if header == b'SQLite format 3\\x00':
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as connection:
            yield from decoded(row[0] for row in connection.execute('SELECT row FROM rows ORDER BY i'))
    else:
        opener = gzip.open if header[:2] == b'\\x1f\\x8b' else open
        with opener(path, 'rt') as handle:
            yield from decoded(handle)
'''+s[b:]
s=s.replace("    if old.get('count') != spec['count']:","    if spec['rows'] != old.get('rows_metadata', old.get('database')):\n        raise ValueError('Source metadata is not bound by its input receipt')\n    if old.get('count') != spec['count']:")
s=s.replace("    result = {**old, 'source_scene_exclusions': report, 'count': len(kept),", "    result = {'schema': 'r2-source-scene-selection-v1', 'source_scene_exclusions': report, 'count': len(kept),")
s=s.replace("    shared_counts, draw = {}, Withheld()", "    shared_counts, draw = {}, Withheld()\n    population_total, final_types, pending_types = 0, Counter(), Counter()")
s=s.replace("        seen, listed_count = 0, 0", "        seen, listed_count, retained = 0, 0, Counter()")
s=s.replace("            listed_count += int(any(matches.values()) or pair in original.lists['room_release_gate'])", "            excluded = any(matches.values()) or pair in original.lists['room_release_gate']\n            listed_count += int(excluded)\n            if not excluded:\n                retained[row['question_type']] += 1")
s=s.replace("        source['after_exclusions'] = dict(rows=seen-listed_count)","        source['after_exclusions'] = dict(rows=seen-listed_count, per_type=dict(retained))\n        population_total += seen\n        (final_types if source['status'] == 'final' else pending_types).update(retained)\n    value['totals'] = dict(rows_in_files=population_total,\n                          final_after_exclusions=dict(rows=sum(final_types.values()), per_type=dict(final_types)),\n                          pending_review_after_exclusions=dict(rows=sum(pending_types.values()), per_type=dict(pending_types)))")
p.write_text(s)
p=L/'work/tree_r1/tests/test_r2_build3b.py';s=p.read_text()
s=s.replace("count=len(values)))", "count=len(values), rows_metadata=m['rows']))")
s=s.replace("write(root/'incomplete.json',dict(count=4))", "write(root/'incomplete.json',dict(count=4,rows_metadata=one['rows']))")
s += '''
    def test_bound_native_sqlite_and_opaque_metadata(self):
        root=directory()
        values=[dict(qid=str(i),canonical=scene) for i,scene in enumerate(('d1/clean',NATIVE,ALIAS))]
        path=root/'a.bin'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE rows (i INTEGER, row TEXT)')
            db.executemany('INSERT INTO rows VALUES (?,?)',[(i,json.dumps(row)) for i,row in enumerate(values)])
        self.assertEqual(list(S.rows(file_pin(path))),values)
        write(root/'receipt.json',dict(count=len(values),database=file_pin(path)))
        spec=dict(receipt=file_pin(root/'receipt.json'),rows=file_pin(path),count=len(values),source='vqa')
        pin=S.rebuild_receipt(spec,DEV,BENCH,root/'out')
        self.assertEqual(load(pinned(pin))['count'],1)
        self.assertEqual(load(pinned(load(pinned(pin))['indices'])),[0])
        zipped=root/'b.bin'
        with gzip.open(zipped,'wt') as handle:handle.write(''.join(json.dumps(r)+'\\n' for r in values))
        self.assertEqual(list(S.rows(file_pin(zipped))),values)
        with self.assertRaisesRegex(ValueError,'not bound'):
            S.rebuild_receipt({**spec,'rows':file_pin(zipped)},DEV,BENCH,root/'bad')
'''
p.write_text(s)
p=L/'work/build3b/STATUS.md'
p.write_text(p.read_text()+"\nSource authentication now requires the metadata pin in the original receipt. Native SQLite reads are read-only; opaque compressed metadata is detected by its header. Rebuilt selections use a separate schema instead of carrying stale native database counts. Pool summary counts are recomputed. These changes await closure tests.\n")
