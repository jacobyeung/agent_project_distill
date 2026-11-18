#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_ee227714
KH=/project/community/jjyeung/okh7/x_ee227714
printf '%s  %s\n' '3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b' "$BUN/p.tar" | sha256sum -c --quiet
# Verify the real A donor; rebind mode intentionally changes populations.
[[ $# == 0 ]] || exit 2
python3 -I -B - "$BUN" "$KH" <<'END'
"""Read-only checkpoint and population check; never extract a slot or run a model."""
import hashlib,importlib.util,json,re,sys,tarfile
from pathlib import Path
b,k=map(Path,sys.argv[1:3])
def need(ok,why):
 if not ok:raise SystemExit('REFUSED: '+why)
def raw(p):
 need(not p.is_symlink() and p.is_file(),'missing or linked '+str(p));return p.read_bytes()
def sha(v):return hashlib.sha256(v).hexdigest()
def load(p):return json.loads(raw(p))
def pinned(p,pin):
 v=raw(p);need(sha(v)==pin['sha256'],'SHA differs: '+str(p))
 if 'bytes' in pin:need(len(v)==pin['bytes'],'size differs: '+str(p))
 return json.loads(v)
manifest=dict(reversed(line.split('  ',1)) for line in raw(k/'SHA256SUMS.txt').decode().splitlines())
for name in ('b/c0.py','k/launch.json','k/a0.json','k/7.json'):
 need(sha(raw(k/name))==manifest.get(name),'kit manifest differs: '+name)
launch=load(k/'k/launch.json');cfg=pinned(k/launch['config']['file'],launch['config']);parent=load(k/'k/a0.json')
spec=importlib.util.spec_from_file_location('bridge',k/'b/c0.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
pointer=bridge.policy(cfg,parent)
need(pointer['rows']=='rebind','Cprime requires rebind continuation')
root=Path(pointer['root']);need(not root.is_symlink(),'linked A root')
need(load(root/'RUN.json')['run']==pointer['run'],'A run differs')
bound_raw=raw(root/'binding.json');bound=json.loads(bound_raw)
need(sha(bound_raw)==raw(root/'binding.json.sha256').decode().split()[0],'A binding mirror differs')
candidates=[]
for slot in ('A','B'):
 p=root/(slot+'.json')
 if not p.exists() and not p.is_symlink():continue
 r=load(p)
 print('SLOT '+slot+' verified='+str(r.get('verified'))+' step='+str(r.get('step')))
 if r.get('verified') is True and type(r.get('step')) is int and r['step']==200:candidates.append((slot,r))
need(bool(candidates),'no verified real step-200 slot')
slot,r=candidates[0];archive=root/(slot+'.tar')
need(r.get('slot')==slot and r.get('content_check')=='c1-slot-check-v1','slot record differs')
need(re.fullmatch(r'checkpoint_000200(?:_[0-9a-f]{32})?',r['checkpoint']),'checkpoint name differs')
need(not archive.is_symlink() and archive.stat().st_size==r['bytes'],'archive size differs')
need(raw(root/(slot+'.sha256')).decode().split()[0]==r['archive_sha256'],'archive sidecar differs')
for key,want in (('archive_sha256','76bed2480fe66ad526bcf4783e921ca172a7b86cc7d635e4d840e99c4ab0f1ba'),('manifest_sha256','c11b603fb3b6dc986e2cbb9b494954b48204ba5f4d108ad563cb7c8c564d9430'),('checkpoint','checkpoint_000200_a09ca55b784a404f97ac7dfea8d7226b'),('job','171377'),('bytes',113540341760)):need(r.get(key)==want,'A slot field differs: '+key)
print('PASS LIGHT A slot '+slot+' step 200 verified; fields equal the pinned 76bed248/c11b603f/a09ca55b; size and sidecar equal; pointer root '+str(root)+' step '+str(pointer['step'])+' rows '+pointer['rows']+'; full payload stream left to the in-job bridge',flush=True)
raise SystemExit(0)
h=hashlib.sha256();files={};metadata={};seen=set()
class Reader:
 def __init__(self,f):self.f=f
 def read(self,n=-1):
  v=self.f.read(n);h.update(v);return v
with archive.open('rb') as f:
 reader=Reader(f)
 with tarfile.open(fileobj=reader,mode='r|') as tf:
  for m in tf:
   name=Path(m.name)
   need(not name.is_absolute() and '..' not in name.parts and m.name not in seen,'unsafe or duplicate slot member');seen.add(m.name)
   need(name.parts[0] in (r['checkpoint'],'inputs','binding.json') and (m.isdir() or m.isfile()),'unexpected slot member')
   if m.isdir():continue
   mh=hashlib.sha256();chunks=[];retain=m.name.endswith('.json') and m.size<=16_000_000
   with tf.extractfile(m) as src:
    for chunk in iter(lambda:src.read(1<<20),b''):
     mh.update(chunk)
     if retain:chunks.append(chunk)
   files[m.name]=dict(sha256=mh.hexdigest(),bytes=m.size)
   if retain:metadata[m.name]=b''.join(chunks)
 for chunk in iter(lambda:reader.read(1<<20),b''):pass
need(h.hexdigest()==r['archive_sha256'],'real archive digest differs')
need(metadata['binding.json']==bound_raw,'archived binding differs')
cp=r['checkpoint'];mraw=metadata[cp+'/complete.json'];m=json.loads(mraw)
need(sha(mraw)==r['manifest_sha256'] and m['schema']=='c1-checkpoint-v1' and type(m['step']) is int and m['step']==pointer['step'] and m['binding']==bound,'checkpoint manifest differs')
required={'replicated.pt'}|{f'{s}{i:03d}.pt' for i in range(4) for s in ('rng','shards/rank')}
need(required<=set(m['files']),'checkpoint payload missing')
for name,pin in m['files'].items():
 actual=files.get(cp+'/'+name);need(actual and actual['sha256']==pin['sha256'] and ('bytes' not in pin or actual['bytes']==pin['bytes']),'checkpoint payload differs: '+name)
def apin(pin):
 rel=Path(pin['path']).relative_to(Path(parent['output'])/'inputs');name='inputs/'+str(rel)
 need('..' not in rel.parts and name in metadata,'A prepared metadata unavailable: '+name)
 v=metadata[name];need(sha(v)==pin['sha256'],'A preparation pin differs: '+name);return json.loads(v)
a=json.loads(metadata['inputs/data_receipt.json']);acfg=apin(a['config']);aprep=apin(a['preparation'])
need(a['status']=='PREPARED' and a['rehearsal'] is False and a['real_frames_verified'] is True and a['world_size']==4,'A admission invalid')
need(bridge.identity(acfg)==bound['config_sha256'] and bound['preparation']==a['preparation'],'A effective binding differs')
need(a['input_streams']==parent['streams'] and a['source_revision']==bound['trainer_commit']==load(k/'k/7.json')['commit'],'A input or trainer identity differs')
print('PASS REAL A step-200 checkpoint, archive, manifest, shards and C resume pointer '+slot,flush=True)
print("PASS REAL A resume pointer; Cprime rebind policy verified; production admission runs in job")
END
