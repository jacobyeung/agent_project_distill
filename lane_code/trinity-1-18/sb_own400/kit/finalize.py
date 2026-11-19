"""Seal kit files and enumerate exact target paths without contacting the target."""
from core import *
import tarfile
O=ROOT/'out'
def main():
 files=[p for p in KIT.rglob('*') if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.parts]
 files.append(O/'BARS_FROZEN.json')
 atomic(KIT/'SEAL.json',{'schema':'sb-own400-seal-v1','input_sha256':{str(p):sha(p) for p in sorted(files)}})
 old=read(O/'REUSED_FILES.json');members={}
 with tarfile.open(KIT/'inputs/A10b_code.tgz') as t:
  for m in t:
   if m.isfile():members[m.name]={'sha256':__import__('hashlib').sha256(t.extractfile(m).read()).hexdigest(),'bytes':m.size}
 old['archive_members']={'archive':str(KIT/'inputs/A10b_code.tgz'),'sha256':sha(KIT/'inputs/A10b_code.tgz'),'members':members}
 atomic(O/'REUSED_FILES.json',old)
 arcs=read(KIT/'inputs/ARCHIVES.json');already=[];copy=[]
 for a in arcs['archives']:
  for p in a['parts']:
   (copy if pathlib.Path(p['path']).is_relative_to(ROOT) else already).append({**p,'presence':'local' if pathlib.Path(p['path']).is_relative_to(ROOT) else 'coordinator-reported; target not accessed'})
 seen=set()
 for c in read(KIT/'inputs/NEEDS_INPUTS.json')['captures']:
  for p in c['frames']:
   if p['path'] in seen:continue
   seen.add(p['path']);q=pathlib.Path(p['path']);already.append({'path':str(q),'sha256':p['sha256'],'bytes':q.stat().st_size if q.exists() else 'MISSING','presence':'coordinator-reported on target; bytes from local file'})
 for p in files+[KIT/'SEAL.json']:
  if not any(x['path']==str(p) for x in copy):copy.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'source':str(p),'presence':'copy from trinity-1-18 to the identical absolute path'})
 bootstrap=pathlib.Path('/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12')
 env=read(KIT/'inputs/ENV_REQUIRED.json')
 missing=[{'path':env['target_python'],'bytes':'MISSING','sha256':'MISSING','reason':'Exact step-544 environment and overlay archive not found locally; not replaced with A10b Torch 2.13 runtime'}]
 pins={str(KIT/'inputs/ARCHIVES.json'):sha(KIT/'inputs/ARCHIVES.json'),str(KIT/'inputs/NEEDS_INPUTS.json'):sha(KIT/'inputs/NEEDS_INPUTS.json'),str(KIT/'inputs/ENV_REQUIRED.json'):sha(KIT/'inputs/ENV_REQUIRED.json'),str(KIT/'finalize.py'):sha(__file__),str(bootstrap):sha(bootstrap)}
 spec={'input_sha256':pins,'already_there':already,'to_copy_from_1_18':copy,'missing':missing,'bootstrap_python':{'path':str(bootstrap),'bytes':bootstrap.stat().st_size,'sha256':sha(bootstrap),'presence':'target stage plan names this path; target presence not verified'},'g0':'Not consumed; this pass reuses G3T grids and never loads its model','exact_runtime_source':'STEP544_ENV.log; Torch 2.11.0+cu129 and Transformers 5.12.1 with numpy/scipy/fla overlays','copy_bytes':sum(x['bytes'] for x in copy),'frame_files':len(seen),'frame_bytes':sum(x['bytes'] for x in already if x['path'] in seen and isinstance(x['bytes'],int))}
 atomic(O/'STAGE_228.json',spec)
 lines=['Target: trinity-2-28. No SSH or target inspection was performed.','Columns: absolute target path | bytes | sha256','Already there means coordinator-reported; launcher rechecks every byte pin.','', 'ALREADY THERE (reported):']
 lines += [f"{x['path']} | {x['bytes']} | {x['sha256']}" for x in already]
 lines += ['','TO COPY FROM 1-18 (same absolute target path):']
 lines += [f"{x['path']} | {x['bytes']} | {x['sha256']}" for x in copy]
 lines += ['','MISSING REQUIRED ENVIRONMENT:',f"{env['target_python']} | MISSING | MISSING",'Exact runtime/overlay inventory and bytes are unavailable locally. ENV_REQUIRED.json pins the observed module versions and file hashes. Do not substitute another environment.','', 'BOOTSTRAP INTERPRETER (target stage plan names this path):',f"{bootstrap} | {bootstrap.stat().st_size} | {sha(bootstrap)}",'Its Python 3.12 standard library must be present. It is not the model environment.','', 'g0 is not needed: no G3T or SAM forward is performed.','All extraction, temporary files, caches, restored assets, and outputs stay under /scratch/jjyeung/orch_n30/sb_own400/out/gpu.','Scoring runs later on 1-18, where sb_scale1/sb_scale2 and their caches already exist. Return only out/gpu/captures for scoring.','',f"Copy bytes: {spec['copy_bytes']}; anchor frame files: {spec['frame_files']}; anchor frame bytes: {spec['frame_bytes']}", 'Command producing this inventory: python -B kit/finalize.py']
 (O/'STAGE_228.txt').write_text('\n'.join(lines)+'\n')
 print('sealed',len(files),'files; copy',spec['copy_bytes'],'bytes;',len(seen),'frames')
if __name__=='__main__':main()
