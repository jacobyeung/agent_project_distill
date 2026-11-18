#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_7f1589c1
KH=/project/community/jjyeung/okh7/x_7f1589c1
printf '%s  %s\n' '08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd' "$BUN/p.tar" | sha256sum -c --quiet
# Optional argument: login-visible preserved C inputs directory from proof 172180.
[[ $# -le 1 ]] || exit 2
python3 -I -B - "$BUN" "$KH" "${1:-/tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/runs/05b8ac69/inputs}" <<'END'
"""Read-only checkpoint and population check; never extract a slot or run a model."""
import hashlib,importlib.util,json,re,sys,tarfile
from pathlib import Path
b,k=map(Path,sys.argv[1:3]);cinputs=Path(sys.argv[3])
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
need(pointer['rows']=='exact','population equality requires exact continuation')
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
old=k.with_name(k.name+'.f172180');log=raw(old/'o/172180.proof.log')
need(sha(log)=='0658f1614ad94ff6141b66ba1523b37d2ea60d28c074929ac6e6f2307b1d58a3','172180 log pin differs')
need(sha(raw(old/'o/172180.proof.json'))=='ed9aad679a1d9dd6302970dcb82d02d5b92fd6f3a53aede6bf219fca405f8d21','172180 receipt pin differs')
counts={}
for line in log.decode().splitlines():
 if line.startswith('{'):
  row=json.loads(line)
  if 'scene_exclusion' in row:
   v=row['scene_exclusion'];counts[v['source']]=v['retained']
differences=[]
for stream in sorted(aprep['streams']):
 if stream in counts:
  av=aprep['streams'][stream].get('count');cv=counts[stream];equal=av==cv
  print('STREAM_LOG '+stream+' '+('equal' if equal else 'different')+' A='+str(av)+' C='+str(cv))
  if not equal:differences.append('log:'+stream)
# The failed proof never copied its prepared seals into proof.json. Require the
# retained inputs to compare families; log counts alone cannot establish equality.
need(cinputs.is_dir(),'172180 prepared inputs are not login-visible; supply a preserved inputs directory as pre1.sh argument (no family comparison is inferred)')
c=load(cinputs/'data_receipt.json')
need(c['status']=='PREPARED' and c['rehearsal'] is False and c['real_frames_verified'] is True and c['world_size']==4,'C admission invalid')
need(c['input_streams']==cfg['streams'] and c['source_revision']==a['source_revision'],'C inputs differ from authenticated kit')
def cpin(pin):
 rel=Path(pin['path']).relative_to(Path(cfg['output'])/'inputs');need('..' not in rel.parts,'unsafe C input pin');return pinned(cinputs/rel,pin)
ccfg=cpin(c['config']);cprep=cpin(c['preparation']);need(cprep['config_sha256']==bridge.identity(ccfg),'C preparation identity differs')
amix=apin(aprep['type_mix_population']);cmix=cpin(cprep['type_mix_population'])
asamp=bridge.sampling(aprep);csamp=bridge.sampling(cprep)
def compare(label,av,cv):
 equal=json.dumps(av,sort_keys=True)==json.dumps(cv,sort_keys=True)
 print(label+' '+('equal' if equal else 'different'))
 if not equal:differences.append(label)
astr=dict(asamp.pop('streams'));cstr=dict(csamp.pop('streams'))
for stream in sorted(set(astr)|set(cstr)):compare('STREAM '+stream,astr.get(stream),cstr.get(stream))
compare('SAMPLING_POLICY',asamp,csamp)
for key in ('populations','effective','spec'):
 av,cv=amix[key],cmix[key]
 compare('MIX '+key,av,cv)
 if isinstance(av,dict) and isinstance(cv,dict):
  for stream in sorted(set(av)|set(cv)):
   aa,cc=av.get(stream),cv.get(stream)
   if isinstance(aa,dict) and isinstance(cc,dict):
    for family in sorted(set(aa)|set(cc)):compare('FAMILY '+key+'/'+stream+'/'+family,aa.get(family),cc.get(family))
   else:compare('FAMILY '+key+'/'+stream,aa,cc)
need(not differences,'population differs: '+','.join(differences))
print('PASS REAL A resume pointer and C/A preparation populations equal; no proof PASS granted')

END
