#!/usr/bin/env -S nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B
"""Arm a reviewed kit locally. Upload and launch remain separate operations."""
from pathlib import Path
import base64,hashlib,importlib.util,json,os,shutil,sys


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 v=json.loads(Path(p).read_text())
 if 'payload' in v:
  raw=base64.b64decode(v['payload'],validate=True)
  if __import__('hashlib').sha256(raw).hexdigest()!=v['sha256']:raise ValueError('R1_CAPSULE_CHANGED')
  return json.loads(raw)
 return v

def capsule(v):
 raw=json.dumps(v,sort_keys=True,indent=2).encode()+b'\n'
 return json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode()

def arm(review_path,expected,go,normal,output,upload_root,scan):
 review_path=Path(review_path)
 if not review_path.is_file() or review_path.is_symlink():raise ValueError('R1_REVIEW_RECEIPT_MISSING')
 raw=review_path.read_bytes()
 try:review=json.loads(raw)
 except (ValueError,UnicodeError):raise ValueError('R1_REVIEW_RECEIPT_INVALID') from None
 if not isinstance(review,dict) or review.get('verdict')!='PASS':raise ValueError('R1_REVIEW_RECEIPT_NOT_PASS')
 if review.get('config_identity')!=expected:raise ValueError('R1_REVIEW_IDENTITY_DIFFERS')
 # Independent authorship is checked by the reviewer/orchestrator, not asserted by this builder.
 h=hashlib.sha256(raw).hexdigest();go=Path(go);normal=Path(normal);output=Path(output);upload_root=Path(upload_root)
 if output.exists() or upload_root.exists():raise ValueError('R1_ARM_OUTPUT_EXISTS')
 if read(go/'k/a.json')['GO'] is not True:raise ValueError('R1_ARM_GO_REQUIRED')
 shutil.copytree(go,output)
 control=read(output/'k/a.json');control['review']={'path':'u/'+h,'sha256':h}
 (output/'k/a.json').write_bytes(capsule(control))
 files={str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt')}
 sums=''.join(v+'  '+n+'\n' for n,v in sorted(files.items()))
 (output/'SHA256SUMS.txt').write_text(sums)
 seal=hashlib.sha256(sums.encode()).hexdigest()
 build=read(output/'BUILD.json');build['kit_sha256']=seal
 (output/'BUILD.json').write_bytes(capsule(build))
 result=scan(output)
 if result.get('status')!='PASS':raise ValueError('R1_ARM_SCAN_REFUSED')
 upload_root.mkdir(parents=True)
 rows=[]
 for p in sorted(output.rglob('*')):
  if p.is_file() and (not (normal/p.relative_to(output)).is_file() or sha(p)!=sha(normal/p.relative_to(output))):
   n='n/'+str(p.relative_to(output));dest=upload_root/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
   rows.append(dict(name=n,sha256=sha(dest),bytes=dest.stat().st_size,local_path=str(dest)))
 if [r['name'] for r in rows]!=['n/BUILD.json','n/SHA256SUMS.txt','n/k/a.json']:raise ValueError('R1_ARM_UNEXPECTED_DELTA')
 dest=upload_root/'u'/h;dest.parent.mkdir();dest.write_bytes(raw)
 rows.append(dict(name='u/'+h,sha256=h,bytes=len(raw),local_path=str(dest)))
 return dict(schema='build24h-armed-diff-v1',config_identity=expected,review=control['review'],kit_seal=seal,files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),stream_root=str(upload_root),decoded_scan='PASS',upload_authorized=False,launch_authorized=False)


def scanner(base):
 sys.path[:0]=[str(base/'work/build21'),str(base/'work/tree_r1')]
 from unittest.mock import patch
 import environment21f as E
 spec=importlib.util.spec_from_file_location('armed_scan',base/'work/build24h/naming24h_n_go.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 def check(k):
  from launch_r1.build import verify
  verify(k)
  with patch.object(E,'__file__',str(base/'work/build24h/scanners/n_go/environment21f.py')):return module.scan_decoded(k)
 return check


def main():
 if len(sys.argv)!=2:raise SystemExit('usage: arm_go.py <review.json>')
 base=Path(__file__).resolve().parents[1]
 sys.path.insert(0,str(base/'out'))
 from identity import compute
 expected=compute(base)
 record=arm(sys.argv[1],expected,base/'out/kit_n_go',base/'work/build24/kits/n',base/'out/kit_n_go_armed',base/'out/upload_armed',scanner(base))
 (base/'out/UPLOADS_ARMED.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
 (base/'out/UPLOADS_ARMED.list').write_text(''.join(r['name']+'\n' for r in record['files']))
 print(json.dumps(dict(kit_seal=record['kit_seal'],config_identity=expected,files=record['total_files'],decoded_scan='PASS')))


if __name__=='__main__':
 import resource
 resource.setrlimit(resource.RLIMIT_AS,(19_000_000_000,19_000_000_000))
 os.environ.update(OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='')
 main()
