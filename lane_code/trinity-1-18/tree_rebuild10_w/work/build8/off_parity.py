import hashlib,json,os,subprocess,sys,tarfile
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8';P=B/'proofs/off_parity';P.mkdir(parents=True,exist_ok=True)
archive=L/'out/tree_rebuild_b6_427fb3cb.tar';prior=P/'b6'
with archive.open('rb') as f:archive_sha=hashlib.file_digest(f,'sha256').hexdigest()
assert archive_sha.startswith('b134cae8')
files={};total=0
with tarfile.open(archive) as tar:
 for member in tar:
  prefix='work/tree_r1/'
  if not member.name.startswith(prefix) or not member.isfile():continue
  rel=Path(member.name[len(prefix):])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('source path')
  if rel.suffix not in ('.py','.json','.sh','.md','.txt','.tsv','.yaml','.yml','.toml'):continue
  total+=member.size
  assert total<50_000_000
  data=tar.extractfile(member).read();dest=prior/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  files[str(rel)]=hashlib.sha256(data).hexdigest()
results={}
for name,tree in [('build6',prior),('build8',L/'work/tree_r1')]:
 target=P/(name+'.json')
 with (P/(name+'.log')).open('w') as log:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(B/'off_parity_worker.py'),str(tree),str(target)],stdout=log,stderr=subprocess.STDOUT)
 if p.returncode<0:raise RuntimeError('Process killed; no retry')
 if p.returncode:raise RuntimeError(name+' off parity worker failed')
 results[name]=json.loads(target.read_text())
record=dict(build6_archive_sha256=archive_sha,source_files=files,bytes=total,
 equal=results['build6']==results['build8'],
 scope='Native tiny-model pose loss/gradients/batch and GF-1 online stage batches/losses; actual build-6 routing fixture rendering, own-value suffix masks and legacy policy dictionaries. Cache switch absent; h1 switch absent. Full scheduled-sampling encoder and all build-loop policy outputs remain unqualified.',
 standins='Tiny native Qwen and tiny native G3T configurations at the pretrained/GPU model boundary; synthetic RGB tensors. Actual forward, frozen tower and head functions run.')
(P/'RESULTS.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='source_files'}))
assert record['equal']
