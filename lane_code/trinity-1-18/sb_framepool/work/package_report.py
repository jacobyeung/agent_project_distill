import json,tarfile,hashlib
from pathlib import Path
from scan_rows import sha
root=Path.cwd();out=root/'out';d=json.load(open(out/'FRAMEPOOL.json'));reg=json.load(open('work/metadata_fixed.json'))['files'];items={}
def add(path,name=None):
 p=Path(path);items[name or str(p.relative_to(root))]=p
for name in ['FRAMEPOOL_REPORT.md','FRAMEPOOL.json','CAPTURES.tsv','CAPTURE_MEMBERSHIPS.tsv','VALIDATION.json']:add(out/name)
for p in Path('work').glob('*.py'):add(p.resolve())
for name in ['captures.json','row_results.json','archive_store_results.json','verified_hits.json','evaluation_results.json','local_store_inventory.json','metadata_row_results.json','frame_map.jsonl.gz','frame_plan.json.gz','captures_recheck.log','scan_rows.log','scan_archive_stores.log','eval_join.log']:
 add(root/'work'/name)
for s in d['streams']:
 if s['kind']=='archived_training_metadata_sample' and s['hits']:
  h=s['source_sha256'];add(root/reg[h]['blob'],'evidence/'+h+'.jsonl')
for h in d['input_members']:
 if h.startswith('26196837') or any(h==s.get('source_sha256') for s in d['streams'] if s['kind']=='prepared_production_stream'):
  add(root/reg[h]['blob'],'evidence/'+h+'.json')
for p in d['inputs']:
 if p.endswith('benchmark_scene_exclusions.json'):add(p,'evidence/benchmark_scene_exclusions.json')
 if p.endswith('r2_policy.py'):add(p,'evidence/r2_policy.py')
 if p.endswith('TIERED_ALIAS_MAP.json'):add(p,'evidence/TIERED_ALIAS_MAP.json')
contents={n:dict(sha256=sha(p),bytes=p.stat().st_size,source=str(p)) for n,p in sorted(items.items())}
manifest=out/'PACKAGE_CONTENTS.json';manifest.write_text(json.dumps(dict(command='/usr/bin/python3 work/package_report.py',inputs={v['source']:{'sha256':v['sha256']} for v in contents.values()},members=contents,note='This manifest excludes itself and the tar SHA256 sidecar to avoid self-reference.'),indent=2)+'\n');add(manifest)
archive=out/'sb_framepool.tar'
with tarfile.open(archive,'w') as tar:
 for n,p in sorted(items.items()):tar.add(str(p),arcname=n,recursive=False)
digest=sha(archive);(out/'sb_framepool.tar.sha256').write_text(digest+'  sb_framepool.tar\n')
# Verify bytes inside the finished archive, including the report and all evidence.
with tarfile.open(archive,'r:') as tar:
 for m in tar:
  if m.name=='out/PACKAGE_CONTENTS.json':continue
  f=tar.extractfile(m);h=hashlib.sha256()
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
  assert h.hexdigest()==contents[m.name]['sha256'],m.name
(root/'STATUS.md').write_text('COMPLETE: out/FRAMEPOOL_REPORT.md (62 lines), out/FRAMEPOOL.json, exact capture and membership TSVs, and out/sb_framepool.tar are written and validated. The audit reproduces 146 unique captures / 148 memberships; 1,193 matching records occur in archived training-source metadata samples across 125 captures, while reachable v7 has 0/204,413. Production step-544/R1 consumption remains MISSING because pinned source databases are absent; evaluation-only staging is unproven. All packaged member hashes verify. Archive SHA256: '+digest+'.\n')
print(digest,archive.stat().st_size,'bytes',len(items),'members')
