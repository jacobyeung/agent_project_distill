"""Inspect only catalog-listed local files; do not search external roots."""
import json,sys
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(H/'tools'),str(H/'build/tree')]
import selection_check as sc
from student_pilot.s1_pool import implementation
out=H/'evidence/fix7_selection'
(out/'implementation.json').write_text(sc.enc(implementation())+'\n')
raw=sc.load(H/'evidence/derivation/d0/k/pool_selection.json')
base=sc.load(H/'payload/d_f232d4160d75b582.json')
assert sc.project(raw)==base
cfg=sc.load(H/'build/fx/k/4aa7c6fc.json');resolver=sc.Resolver(H/'build/fx',cfg['s1_routing']['catalog'])
manifest=sc.load(resolver(raw['manifest']))
sizes={v['sha256']:v['bytes'] for e in manifest['sets'] for k,v in e['files'].items() if k in ('rows','packed')}
records=[]
for pin in sc.input_pins(raw,manifest):
 p=resolver.path(pin);present=p.is_file()
 if present:assert sc.sha(p)==pin['sha256']
 records.append(dict(original_path=pin['path'],logical_path=resolver.catalog[pin['sha256']],
  orchard='/project/community/jjyeung/okh7/x_07ca49df/'+str(p.relative_to(H/'build/fx')),
  sha256=pin['sha256'],bytes=p.stat().st_size if present else sizes[pin['sha256']],
  local=str(p) if present else None,size_basis='measured' if present else 'pinned manifest'))
(out/'inputs.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(inputs=len(records),missing=sum(v['local'] is None for v in records),
 missing_bytes=sum(v['bytes'] for v in records if v['local'] is None),projection='exact'),indent=2))
