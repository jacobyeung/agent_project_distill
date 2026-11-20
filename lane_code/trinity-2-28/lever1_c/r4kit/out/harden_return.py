from pathlib import Path
p=Path('src/control.py');s=p.read_text().replace("sources = C.loads((p/'8.bin').read_bytes())\n    C.materialize(root, sources)", "sources = C.loads((p/'8.bin').read_bytes())\n    C.materialize(root, {k:v for k,v in sources.items() if k.startswith('v/')})")
a=s.index("    if not (records/'1.json').exists():",s.index('def finalize'));b=s.index('    receipt = dict(',a)
s=s[:a]+'''    # A deadline may interrupt a write. Publish only complete arm pairs and
    # reconstruct malformed/missing summaries rather than losing the return.
    C = codec(p)
    content = {}; completed = []; n = 0
    if (records/'0.jsonl').exists():
        with (records/'0.jsonl').open('rb') as f:
            while True:
                first, second = f.readline(262145), f.readline(262145)
                if not first: break
                try:
                    a, b = C.loads(first), C.loads(second)
                    if a['i'] != b['i'] or (a['a'],b['a']) != (0,1): break
                    if sum(map(len, completed))+len(first)+len(second) > LIMIT-200000: break
                except (ValueError, KeyError, TypeError): break
                completed.extend((first,second)); n += 2
        content['0.jsonl'] = b''.join(completed)
    try:
        summary = read(records/'1.json')
        assert isinstance(summary, dict) and type(summary['passed']) is bool
        if mode == 'g' and summary.get('records') != n: summary['passed'] = False
    except (OSError, ValueError, KeyError, AssertionError):
        summary = dict(passed=False, mode=mode, status='failed')
    summary.update(records=n, frozen=cfg['frozen'], artifact=cfg['export']['artifact']['sha256'],
                   tools_served=0, max_new_tokens=64, external_components_loaded=False)
    if code or error is not None: summary['passed'] = False
    write(records/'1.json', summary)
    content['1.json'] = (records/'1.json').read_bytes()
    if (records/'2.json').exists(): content['2.json'] = (records/'2.json').read_bytes()[:65536]
    dest = p/'a'/mode; dest.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tarfile.open(dest/'0.tgz', 'w:gz') as t:
        for name, raw in content.items():
            item = tarfile.TarInfo(name); item.size = len(raw); item.mode = 0o600
            t.addfile(item, io.BytesIO(raw))
''' +s[b:]
p.write_text(s)
p=Path('tests/test_fixes.py');s=p.read_text().replace("dict(i='a',a=a,text='<ground',n=1)", "dict(i='a',a=a,text='<ground',n=1)")
# Include interrupted record and summary writes in the finalizer regression.
s=s.replace("        ctl.finalize(p,records,cfg,'g','123',time.time(),1,ctl.Deadline())", "        with (records/'0.jsonl').open('ab') as f:f.write(b'{\"a0\":\"7b')\n        (records/'1.json').write_bytes(b'{')\n        ctl.finalize(p,records,cfg,'g','123',time.time(),1,ctl.Deadline())")
s=s.replace("        scan(records)\n        EVIDENCE['partial_pairs']", "        for name,raw in returned.items():\n            self.assertFalse(any(w.encode() in raw.lower() for w in B.DENY))\n        EVIDENCE['partial_pairs']")
p.write_text(s)
