from pathlib import Path
L=Path(__file__).resolve().parents[2]
p=L/'work/tree_r1/student_pilot/r2_scene_bindings.py'
s=p.read_text().replace('from .r2_withheld import SHA256, Withheld','from .r2_withheld import SHA256, Withheld, room')
s=s.replace('from .p3_provenance import encoded, file_pin, load, pinned, write','from .p3_provenance import encoded, file_pin, load, pinned, write, digest')
s=s.replace("draw.touches(row, dict(names=list(rule.identifiers(row))))", "any(room(name) in draw.aliases for name in rule.identifiers(row))")
s=s.replace("report = prepare(file_pin(output/'0.json'), output/'p', remove_files, tokenizer, room_sets or ROOM_SETS)", "report = prepare(file_pin(output/'0.json'), output/'p', remove_files, tokenizer, room_sets or ROOM_SETS, opaque=True)")
s=s.replace('dict(pool_rows_withheld=shared_counts, receipt=', 'dict(pool_rows_withheld={digest(name):count for name,count in shared_counts.items()}, receipt=')
s=s.replace('dict(source=name, rows_withheld=withheld, counts=', 'dict(source=digest(name), rows_withheld=withheld, counts=')
p.write_text(s)
p=L/'work/tree_r1/student_pilot/s1_pool.py';s=p.read_text()
s=s.replace('sha256, source_files, write','sha256, source_files, write, digest')
s=s.replace('def prepare(manifest, output, remove_files=(), tokenizer=None, room_sets=ROOM_SETS):','def prepare(manifest, output, remove_files=(), tokenizer=None, room_sets=ROOM_SETS, *, opaque=False):')
s=s.replace('selection = output / (name+".json")','selection = output / ((digest(name) if opaque else name)+".json")')
s=s.replace('print(json.dumps(dict(pool_source=name, **record)), flush=True)', 'print(json.dumps(dict(source=digest(name), retained=record.get("retained", 0), status=record["status"])\n                         if opaque else dict(pool_source=name, **record)), flush=True)')
p.write_text(s)
p=L/'work/tree_r1/tests/test_r2_build3b.py';s=p.read_text()
s+='''
    def test_pool_outputs_and_logs_are_opaque(self):
        import io
        from contextlib import redirect_stdout
        from launch_r2.build import bad_string
        root=directory();pin=pool_fixture(root/'pool')
        value=load(pinned(pin));value['sets'][0]['name']='ARKIT_gen_r2'
        write(root/'manifest.json',value)
        log=io.StringIO()
        with redirect_stdout(log):
            receipt=S.rebuild_pool(file_pin(root/'manifest.json'),DEV,BENCH,root/'opaque')
        self.assertNotIn('ARKIT',log.getvalue())
        hashes=load(LANE/'work/tree_r1/launch_s1/b/wh.json')
        for path in (root/'opaque').rglob('*'):
            self.assertFalse(bad_string(str(path.relative_to(root/'opaque')),hashes))
        self.assertEqual([r['qid'] for r in s1_pool.selected_rows(receipt,'ARKIT_gen_r2')],['T0_gen_r20'])
        native=s1_pool.prepare(load(pinned(receipt))['manifest'],root/'native')
        self.assertEqual(native['selected_rows'],load(pinned(receipt))['selected_rows'])
'''
p.write_text(s)
