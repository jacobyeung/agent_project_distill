from pathlib import Path
p=Path('build.py');s=p.read_text().replace("'base_config','original_model','env','policy'", "'base_config','original_model'")
s=s.replace("source_blob=storage.pack(jd(sources))", '''# Authenticate full archives, but materialize only admitted inputs. Native
    # third-party runtime/model assets retain their required wire representation.
    n='v/orchard_stage.py'
    text=sources[n].replace('strip=0, overlay=False):', 'strip=0, overlay=False, retain_roots=None):')
    text=text.replace('            target = destination/str(path)',
        "            if retain_roots is not None and path.parts[0] not in retain_roots:\\n                continue\\n            target = destination/str(path)")
    text=text.replace("            target.chmod(item.mode & 0o777)",
        "            if retain_roots is not None and path.parts[0] in ('p0','m400') and target.suffix=='.json' and 'full_weights' not in path.parts:\\n                import json\\n                original=target.read_bytes()\\n                target.write_text(json.dumps({'a0':original.hex()})+'\\\\n')\\n            target.chmod(item.mode & 0o777)")
    sources[n]=text
    source_blob=storage.pack(jd(sources))''')
p.write_text(s)
p=Path('src/control.py');s=p.read_text().replace("S.extract_stream(f, root/archive['destination'], None, archive['expanded_bytes'], links=True)", "S.extract_stream(f, root/archive['destination'], None, archive['expanded_bytes'], links=True,\n                                 retain_roots=None if archive['destination'].endswith('/f') else ('m400','p0','b','o','f','v'))")
s=s.replace("assert q.stat().st_size == f['bytes'] and sha(q) == f['sha256']", "raw = codec(p).raw(q.read_bytes()) if q.suffix=='.json' else None\n            assert (len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']) if raw is not None else (q.stat().st_size==f['bytes'] and sha(q)==f['sha256'])")
p.write_text(s)
