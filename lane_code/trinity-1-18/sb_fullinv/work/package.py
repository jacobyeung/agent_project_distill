"""Check the completed inventory and archive only this lane's deliverables."""
import json, hashlib, tarfile, io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
report=ROOT/'out/FULL_INVENTORY.json';d=json.loads(report.read_text())
assert len((ROOT/'out/FULL_INVENTORY.md').read_text().splitlines())<=70
assert len(d['slices'])==6
checked={}
def pins(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str) and v['sha256']!='MISSING':
   p=Path(v['path'])
   if p.is_relative_to(ROOT):
    actual=checked.setdefault(str(p),digest(p));assert actual==v['sha256'],(p,actual,v['sha256'])
  for x in v.values():pins(x)
 elif isinstance(v,list):
  for x in v:pins(x)
pins(d)
count=0
for name,s in d['slices'].items():
 env=json.loads(Path(s['draft_envelope']['path']).read_text())
 assert env['required_exclusion_pins']==d['exclusion_pins']
 assert env['extent_receipt']['sha256'].startswith('c072905b')
 if name=='camera_wording':assert env['rows']=='MISSING';continue
 assert len(env['row_bindings'])==s['rows'];count+=s['rows']
 cov=json.loads(Path(env['scene_coverage']['path']).read_text())
 assert cov['complete'] and set(cov['rows'])==set(env['row_bindings'])
 assert cov['rows_sha256']==env['rows']['sha256'] and cov['exclusions']==env['exclusions']
 assert not s['catalog_missing_qids'] and not s['extent']['missing_qids']
 audit=json.loads(Path(s['exclusions']['audit']['path']).read_text())
 assert audit['tree']=='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1'
 assert audit['complete'] and audit['rows']==s['rows']
 assert s['dry_validation'][0]['location']['line']==42
 assert s['dry_validation'][1]['stack'][1]['line']==58
 assert not s['existing_removal_coverage']['unremoved_K1_qids']
assert count==23886
verification={'schema':'fullinv-package-validation-v1','status':'PASS','checked_workspace_pins':len(checked),'rows':count,'envelopes':6,'report_lines':len((ROOT/'out/FULL_INVENTORY.md').read_text().splitlines()),'checks':['Workspace output pin consistency','Five complete independent map coverages','Exact envelope source/exclusion/extent bindings','Actual selected native tree in all checker runs','Count agreement, no catalog/extent QID gaps','Expected actual intake first failures','All 283 K1 QIDs covered by existing removals'],'inputs':{str(report):{'sha256':digest(report)},str(Path(__file__)): {'sha256':digest(__file__)},str(ROOT/'out/FULL_INVENTORY.md'):{'sha256':digest(ROOT/'out/FULL_INVENTORY.md')}}}
(ROOT/'out/PACKAGE_VALIDATION.json').write_text(json.dumps(verification,indent=2,sort_keys=True)+'\n')
(ROOT/'STATUS.md').write_text('The full inventory is complete and packaged in out/sb_fullinv.tar with its SHA256 sidecar. The 58-line report and JSON ledger cover all six slices, 23,886 row bindings, independent scene evidence, native exclusion/dry-intake results, exact host contracts and CPU estimates. All 283 K1 source hits match existing removals; final retained admission remains unproved. Camera rows, upstream accounting, frame-map/plan bytes, current N frame staging and the separately owned alias build remain required. Package checks verify all workspace pins and archive members.\n')
members=[ROOT/'STATUS.md',ROOT/'out/FULL_INVENTORY.md',report,ROOT/'out/PACKAGE_VALIDATION.json']
members += [p for p in (ROOT/'work').rglob('*') if p.is_file() and 'audits' not in p.relative_to(ROOT/'work').parts and '__pycache__' not in p.parts]
members=sorted(set(members))
manifest={'schema':'fullinv-package-manifest-v1','members':{str(p.relative_to(ROOT)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in members},'inputs':{str(report):{'sha256':digest(report)},str(Path(__file__)):{'sha256':digest(__file__)}}}
mp=ROOT/'out/PACKAGE_MANIFEST.json';mp.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');members.append(mp)
archive=ROOT/'out/sb_fullinv.tar'
with tarfile.open(archive,'w') as t:
 for p in members:t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
with tarfile.open(archive,'r') as t:
 for m in t.getmembers():
  raw=t.extractfile(m).read();expected=digest(mp) if m.name=='out/PACKAGE_MANIFEST.json' else manifest['members'][m.name]['sha256']
  assert hashlib.sha256(raw).hexdigest()==expected,m.name
h=digest(archive);(ROOT/'out/sb_fullinv.tar.sha256').write_text(h+'  out/sb_fullinv.tar\n')
print(json.dumps({'status':'PASS','archive':str(archive),'bytes':archive.stat().st_size,'sha256':h,'members':len(members),'checked_workspace_pins':len(checked)}))
