from pathlib import Path
p=Path('build.py');s=p.read_text()
a=s.index('    text=text.replace("            target.chmod');b=s.index('    sources[n]=text',a)
s=s[:a]+'''    text=text.replace("with archive.extractfile(item) as source, target.open('wb' if overlay else 'xb') as output:",
        "with archive.extractfile(item) as source, _output(target, 'wb' if overlay else 'xb', retain_roots is not None and path.parts[0] in ('p0','m400') and target.suffix=='.json' and 'full_weights' not in path.parts) as output:")
    text += "\\n@contextmanager\\ndef _output(path, mode, encode):\\n    if not encode:\\n        with path.open(mode) as f: yield f\\n    else:\\n        import io\\n        with io.BytesIO() as f:\\n            yield f\\n            path.write_text(json.dumps({'a0':f.getvalue().hex()})+'\\\\n')\\n"
''' +s[b:]
p.write_text(s)
