from pathlib import Path
import json, time
L=Path(__file__).resolve().parents[2]
def replace(p,text):
 p=L/p
 if p.exists():
  old=L/'attic/build24m4q'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
  if old.exists():old=old.with_name(old.name+'.'+str(time.time_ns()))
  p.rename(old)
 p.write_text(text)
p='out/rcj/pc.py';s=(L/p).read_text()
a=s.index('        matches = [line for line in lines');b=s.index('    except OSError:',a)
s=s[:a]+'''        starts = [i for i, line in enumerate(lines) if line == 'Traceback (most recent call last):']
        if starts:
            # The exception terminates this traceback. Later stdout and notes
            # are not exception records, even when they contain a colon.
            frames = False
            for line in lines[starts[-1]+1:]:
                if line.startswith('  File '):
                    frames = True
                if frames and re.fullmatch(r'[A-Za-z_][\\w.]*(?::.*)?', line):
                    reason += ':'+line[:4096]
                    break
'''+s[b:]
a=s.index('\ndef run_bound(')
s=s[:a]+'''
# AutoProcessor's local metadata closure; weight indices and shards are excluded.
ASSETS = frozenset(('config.json', 'processor_config.json', 'preprocessor_config.json',
    'video_preprocessor_config.json', 'tokenizer_config.json', 'tokenizer.json',
    'special_tokens_map.json', 'added_tokens.json', 'vocab.json', 'vocab.txt',
    'merges.txt', 'tokenizer.model', 'spiece.model', 'sentencepiece.bpe.model',
    'chat_template.jinja', 'chat_template.json'))


def metadata_mounts(value, root):
    from student_pilot.p3_provenance import pinned
    logical = Path(value['root'])
    if not logical.is_absolute() or '..' in logical.parts:
        raise ValueError('E95:root')
    mounts = {}
    for name, h in sorted(value['files'].items()):
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('E95:path')
        if name not in ASSETS and not (path.parent == Path('chat_templates') and path.suffix == '.jinja'):
            continue
        target = str(logical/name)
        try:
            source = pinned(dict(path=target, sha256=h))
        except (OSError, ValueError):
            # Mode r already stages these bytes from the resolved metadata pins.
            source = pinned(dict(path=str(Path(root)/'m'/name), sha256=h))
        mounts[target] = dict(source=str(source), sha256=h)
    if 'config.json' not in value['files'] or not mounts:
        raise ValueError('E95:metadata')
    return mounts

'''+s[a:]
s=s.replace("write(control,dict(config=config,model=model,model_value=load(pinned(model)),environment=env,tree_sha256=sealed['tree_sha256'],samples=str(sample_path),output=str(result)))", "value=load(pinned(model)); assets=metadata_mounts(value,root)\n            write(control,dict(config=config,model=model,model_value=value,assets=assets,environment=env,tree_sha256=sealed['tree_sha256'],samples=str(sample_path),output=str(result)))")
s=s.replace("            cmd[-3:]=[str(script),str(control),str(source)]", "            at=cmd.index('--chdir')\n            for dest,item in sorted(assets.items()):\n                cmd[at:at]=['--ro-bind',item['source'],dest]; at+=3\n            cmd[-3:]=[str(script),str(control),str(source)]")
s=s.replace("    processor=processor_for_receipt(value['model_value'],value['config'])", "    for dest,item in value['assets'].items():\n        pinned(dict(path=dest,sha256=item['sha256']))\n    processor=processor_for_receipt(value['model_value'],value['config'])")
replace(p,s)
p='out/rcj/nd.py';s=(L/p).read_text();a=s.index('    # Same precedence as the native family reader');b=s.index('\n\ndef type_table',a)
s=s[:a]+"    from student_pilot.r1_population import family\n    return family(row, 'routing')\n"+s[b:]
s=s.replace("    counts = Counter()\n    with opened(database) as c:","    native_rules(database)\n    counts = Counter()\n    with opened(database) as c:")
replace(p,s)
p='out/TASKA_FIELDS_24M4P.md';s=(L/p).read_text().replace('`student_pilot/r0_exclusion.py:49`, `:71`','`student_pilot/r0_exclusion.py:39`, `:60`');replace(p,s)
