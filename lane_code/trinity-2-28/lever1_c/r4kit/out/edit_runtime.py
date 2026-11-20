from pathlib import Path
p=Path('src/runtime.py');s=p.read_text()
s=s.replace('import time\n','import time\nimport importlib.util\n\nC = None\n\ndef read(path): return C.loads(Path(path).read_bytes())\n')
s=s.replace("Path(path).write_text(json.dumps(value, sort_keys=True, allow_nan=False)+'\\n')", "C.store(path, value)")
s=s.replace('    started = time.monotonic()', "    global C\n    started = time.monotonic()",1)
s=s.replace("    cfg = json.loads((p/'2.json').read_text())", "    spec = importlib.util.spec_from_file_location('a_storage', p/'9.py')\n    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)\n    cfg = read(p/'2.json')")
s=s.replace("    (p/'c/b/work/tmp').mkdir(parents=True, exist_ok=True)\n    sources = p/'c'\n    sys.path[:0] = [str(sources/'b'), str(sources/'tree'), str(p)]", "    finder = C.install(p, outputs=[d/'e'])\n    (p/'c/b/work/tmp').mkdir(parents=True, exist_ok=True)\n    sources = finder.Path(p/'c')")
s=s.replace("    data = json.loads((p/'1.json').read_text())", "    data = read(p/'1.json')")
s=s.replace("receipt = json.loads((export/'receipt.json').read_text())", "receipt = read(export/'receipt.json')")
s=s.replace("config = json.loads(Path(settings['config']).read_text())", "config = read(settings['config'])")
s=s.replace("manifest = json.loads(Path(receipt['model']['path']).read_text())", "manifest = read(receipt['model']['path'])")
s=s.replace("prefix_27_1884=processor.tokenizer.decode([27,1884],skip_special_tokens=False)=='<ground'))", "prefix_27_1884=processor.tokenizer.decode([27,1884],skip_special_tokens=False)=='<ground'))\n        signal.setitimer(signal.ITIMER_REAL, 0)")
a=s.index('    records = 0');b=s.index('\n\nif __name__',a)
s=s[:a]+'''    spec = importlib.util.spec_from_file_location('a_batch', p/'10.py')
    batched = importlib.util.module_from_spec(spec); spec.loader.exec_module(batched)
    records = 0
    status = 'failed'
    try:
        with (out/'0.jsonl').open('xb') as stream, torch.no_grad():
            for start in range(0, len(data['rows']), 8):
                deadline()
                rows = data['rows'][start:start+8]
                assert all(rows[j]['i']==rows[j+1]['i'] and (rows[j]['a'], rows[j+1]['a'])==(0,1) for j in range(0,len(rows),2))
                t0 = time.monotonic()
                batches = [prompt_batch(processor, row_for(row), loaded['config'], 'routed') for row in rows]
                batches = [{k:v.to('cuda:0') if hasattr(v, 'to') else v for k,v in b.items()} for b in batches]
                pending = {}
                def emit(i, result):
                    nonlocal records
                    row = rows[i]
                    result.update(i=row['i'], r=row['r'], a=row['a'], s=time.monotonic()-t0)
                    pending[i] = result
                    pair = i-i%2
                    if pair in pending and pair+1 in pending:
                        raw = b''.join(C.pack(json.dumps(pending[j], sort_keys=True, allow_nan=False)) for j in (pair,pair+1))
                        assert len(raw) <= 262144 and stream.tell()+len(raw) < 49000000
                        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                        records += 2
                        del pending[pair]; del pending[pair+1]
                batched.generate(model, processor, batches, probe, emit, deadline)
                batches = None
        status = 'complete'
    except Deadline:
        status = 'timeout'
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        write(out/'1.json', dict(passed=status=='complete' and records==580, mode='g',
            records=records, status=status, frozen=cfg['frozen'], artifact=pins['artifact']['sha256'],
            load_s=loading, seconds=time.monotonic()-started, tools_served=0,
            external_components_loaded=False, max_new_tokens=64))
''' +s[b:]
s=s.replace("        write(root/'a/2.json',", "        if C is None:\n            spec = importlib.util.spec_from_file_location('a_storage', root/'9.py')\n            C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)\n        write(root/'a/2.json',")
p.write_text(s)
p=Path('score.py');s=p.read_text().replace("probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)","probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)\nspec=importlib.util.spec_from_file_location('a_storage',ROOT/'src/storage.py')\nC=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)")
s=s.replace("receipt=json.load(t.extractfile('1.json'))", "receipt=C.loads(t.extractfile('1.json').read())").replace("rows=[json.loads(x) for x in t.extractfile('0.jsonl')]", "rows=[C.loads(x) for x in t.extractfile('0.jsonl')]")
p.write_text(s)
p=Path('tests/test_probe.py');s=p.read_text().replace("DATA=json.loads(PAYLOAD['1.json'])", "DATA=builder.storage.loads(PAYLOAD['1.json'])")
s=s.replace("json.loads(gzip.decompress(FILES['8.bin']))", "builder.storage.loads(FILES['8.bin'])").replace("cfg=json.loads(FILES['2.json'])", "cfg=builder.storage.loads(FILES['2.json'])")
a=s.index("        for name,text in code.items():",s.index('def test_runtime_compiles'));b=s.index('        from e2e_reader',a)
s=s[:a]+"        builder.storage.materialize(root,code)\n"+s[b:]
s=s.replace("control.opaque(['--dev-bind','/dev','CUDA_VISIBLE_DEVICES=0','a15_cot_apabcdef123'])", "control.opaque(['a15_cot_apabcdef123'])\n        self.assertEqual(set(control.EXTERNAL), {'--dev-bind','/dev'})\n        with self.assertRaises(ValueError):control.opaque(['CUDA_VISIBLE_DEVICES=ground'])")
p.write_text(s)
