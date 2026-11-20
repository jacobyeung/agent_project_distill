from common import *
s=(D/'cs.py').read_text()
s=s.replace("def publish(kit,root,cfg,job):","def final_sources(root,cfg):")
start=s.index("    reader=Rows(load(pinned(cfg['preparation'])),None)")
s=s[:start]+s[start:].replace("    reader=Rows(load(pinned(cfg['preparation'])),None)","    return source\n\ndef publish(kit,root,cfg,job):\n    from student_pilot.p3_provenance import load,pinned\n    from student_pilot.carrier_c1_run import Rows\n    root=Path(root);source=final_sources(root,cfg)\n    reader=Rows(load(pinned(cfg['preparation'])),None)",1)
s=s.replace("    expected=identity(cfg);stores=store_pins(cfg)","    expected=identity(cfg);stores=store_pins(cfg);expected_sources=final_sources(root,cfg)")
s=s.replace("        authenticate(r.get('source_pins'))","        if r.get('source_pins')!=expected_sources[stream]:raise ValueError('R1_CENSUS_SOURCE_PINS_DIFFER:'+stream)\n        authenticate(r['source_pins'])")
s=s.replace("            raise ValueError('R1_CENSUS_NOT_PASS:'+stream)\n    return file_pin(path)","            raise ValueError('R1_CENSUS_NOT_PASS:'+stream)\n        if r.get('status')=='PASS':\n            counts=r['counts'];result=r['result']\n            if result.get('stream')!=stream or result.get('admitted_rows')!=stores[stream]['count'] or counts.get('admitted')!=stores[stream]['count'] or result.get('source_rows')!=sum(e['count'] for e in expected_sources[stream]) or counts.get('source')!=result['source_rows']:\n                raise ValueError('R1_CENSUS_COUNT_DIFFERS:'+stream)\n    return file_pin(path)")
replace(D/'cs.py',s)
for name in ('q','n','n_go','qd'):
 k=kit(name);replace(k/'b/cs.py',s)
 # Match the native pointing canonical source first; the final tree check stays authoritative.
 v=(k/'b/sv.py').read_text()
 v=v.replace('if stream=="pointing" and how=="unresolved":\n            canonical=(row.get("provenance") or {}).get("canonical_scene")','if stream=="pointing":\n            canonical=(row.get("provenance") or {}).get("canonical_scene") or canonical')
 v=v.replace('        if not canonical:raise ValueError("R1_SCENE_STATUS_UNRESOLVED:"+stream)',"""        if not canonical:raise ValueError("R1_SCENE_STATUS_UNRESOLVED:"+stream)""")
 replace(k/'b/sv.py',v)
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 print(name,reseal(k))
