import json,hashlib,tarfile,os,time
from pathlib import Path
import route as R
from route import ROOT,TREE,load,pin,write,status
R.COMMAND=R.PREFIX+'work/package.py'
pin(__file__);pin(ROOT/'work/route.py')
manifest=load(ROOT/'out/ROUTE_MANIFEST.json');imports=load(ROOT/'out/TREE_IMPORTS.json')
assert not manifest['production_ready']
for name,s in manifest['slices'].items():
 for field in ['rows','coverage','upstream_receipt','envelope','transport_envelope','remove','audit','localized_first2000']:
  p=s[field];pin(p['path'],p['sha256'])
 e=load(s['envelope']['path']);c=load(s['coverage']['path']);u=load(s['upstream_receipt']['path'])
 assert e['exclusions']==c['exclusions']==u['exclusions']
 assert c['rows_sha256']==s['rows']['sha256']==e['rows']['sha256']
 assert sum(x['seen'] for x in u['counts'].values())==s['rows']['row_count']==s['native_counts']['seen']
 assert len(c['rows'])==len(e['row_bindings'])==s['rows']['row_count']
 assert sum(sh['row_count'] for sh in s['shards'])==s['rows']['row_count']
 for sh in s['shards']:
  for field in ['rows','coverage','envelope']:pin(sh[field]['path'],sh[field]['sha256'])
  pin(sh['result']['report']['path'],sh['result']['report']['sha256'])
  assert sh['result']['seen']==sh['row_count']
 for sh in s['shards']:
  sc=load(sh['coverage']['path']);se=load(sh['envelope']['path'])
  assert len(sc['rows'])==sh['row_count'] and sc['rows_sha256']==sh['rows']['sha256']
  assert se['upstream_receipts']==load(s['transport_envelope']['path'])['upstream_receipts']
print('manifest and all shard pins verified',flush=True)
rowfiles=[p for d in ['out/rows','out/variant_R','out/shards'] for p in (ROOT/d).rglob('*.jsonl')]
rowbytes=sum(p.stat().st_size for p in rowfiles)
assert rowbytes>300_000_000
archive=ROOT/'out/fbp_route.tar';members=[]
for top in ['work','out','prompts']:
 for p in sorted((ROOT/top).rglob('*')):
  if not p.is_file() or p.is_symlink():continue
  rel=str(p.relative_to(ROOT))
  if p.suffix=='.jsonl' or p.name in ['fbp_route.tar','fbp_route.tar.sha256','PACKAGE.json','package.log']:continue
  members.append((p,rel))
# Include exact imported tree source/data bytes under a separate snapshot directory.
for path,v in sorted(imports['files'].items()):
 p=Path(path);pin(p,v['sha256']);members.append((p,'tree_imports/'+str(p.relative_to(TREE))))
used=sum(p.lstat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())
projected=sum(((p.stat().st_size+511)//512+4)*512 for p,_ in members)+10240
assert used+projected+5_000_000<1_500_000_000,(used,projected)
# The final state is known before publishing: packaging stops with failure on any mismatch.
status(7,'The manifest, report, and all row/shard pins are verified. Four slices pass native intake; recovery and camera remain blocked by recorded contract checks. The metadata/code archive excludes row files and requires the separate frame host and tree-owner fixes.')
# Include the final stage status, without a circular archive digest in its own contents.
members=[(p,n) for p,n in members if n!='out/STATUS_7.md']+[(ROOT/'out/STATUS_7.md','out/STATUS_7.md'),(ROOT/'STATUS.md','STATUS.md')]
expected={name:pin(p)['sha256'] for p,name in members}
with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as tar:
 for p,name in members:tar.add(p,arcname=name,recursive=False)
checked=0
with tarfile.open(archive,'r:') as tar:
 assert set(tar.getnames())==set(expected)
 for item in tar:
  f=tar.extractfile(item);h=hashlib.sha256()
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  assert h.hexdigest()==expected[item.name],item.name;checked+=1
ap=pin(archive);(ROOT/'out/fbp_route.tar.sha256').write_text(ap['sha256']+'  fbp_route.tar\n')
used_after=sum(p.lstat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())
assert used_after<1_500_000_000
write('out/PACKAGE.json',dict(status='VERIFIED',archive=ap,archive_bytes=archive.stat().st_size,members_verified=checked,member_sha256=expected,row_files_included=False,excluded_new_row_file_bytes=rowbytes,workspace_regular_file_bytes_before_package_receipt=used_after,limit_bytes=1_500_000_000,report=pin(ROOT/'out/REPORT.md'),manifest=pin(ROOT/'out/ROUTE_MANIFEST.json'),scope='Every archive member was rehashed from the completed tar. No row file, RGB file, model, or store is included. The manifest and every shard binding were checked before packaging.'))
print(json.dumps(dict(archive=ap,archive_bytes=archive.stat().st_size,workspace_bytes=used_after,members_verified=checked)),flush=True)
