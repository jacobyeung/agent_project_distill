"""Seal the variant kit and preserve the original staging inventory."""
from core import *

def main():
 out=ROOT/'out';original=read(out/'BARS_FROZEN_B.json')['input_sha256'][str(out/'BARS_FROZEN.json')];checked(out/'BARS_FROZEN.json',original)
 files=sorted(p for p in KIT.rglob('*') if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.parts)
 files += [out/'BARS_FROZEN.json',out/'BARS_FROZEN_B.json']
 atomic(KIT/'SEAL.json',{'schema':'sb-own400b-seal-v1','input_sha256':{str(p):sha(p) for p in files}})
 previous=read(out/'STAGE_228.json');env=read(KIT/'inputs/ENV_REQUIRED.json')
 copies=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files+[KIT/'SEAL.json']]
 already=previous['already_there'];known={x['path'] for x in already}
 for a in env['archives']:
  if a['path'] not in known:already.append({**a,'presence':'reader lane reports staged; target not inspected'})
 runtime=[]
 for group in env['runtime_archives']:
  for p in group['parts']:runtime.append({'path':p['target'],'sha256':p['sha256'],'bytes':p['bytes'],'presence':p.get('availability','MISSING: target presence unverified')})
 missing=[{'path':env['target_python'],'status':'MISSING target import verification; wrapper/base runtime must be prepared by reader lane','base_env':env['base_env']},*runtime]
 pins={str(p):sha(p) for p in (KIT/'SEAL.json',KIT/'inputs/ENV_REQUIRED.json',out/'STAGE_228.json',pathlib.Path(__file__))}
 atomic(out/'STAGE_228_B.json',{'input_sha256':pins,'environment':env,'already_there':already,'runtime_requirements':missing,'to_copy_from_1_18':copies,'copy_bytes':sum(p['bytes'] for p in copies),'target':'trinity-2-28','remote_verification':False,'gpu_output':str(out/'gpu_b'),'cpu_output':str(out/'cpu228_b')})
 lines=['Target: trinity-2-28. No remote inspection or transfer was performed.',f"Pinned interpreter: {env['target_python']} -B -I",f"Base environment: {env['base_env']}", 'Torch 2.13.0+cu130; Transformers 5.19.0; torchvision 0.28.0+cu130; SciPy 1.14.1.', 'The reader lane must prepare its runtime. The import probe refuses other versions, roots, or archive hashes.', 'The base runtime archive parts were marked missing by the reader lane; a2/a3/a4 alone do not contain it.', '', 'ALREADY ON 2-28 (coordinator/reader-lane reports; verify before forward):']
 lines += [f"{x['path']} | {x['bytes']} | {x['sha256']}" for x in already]
 lines += ['', 'RUNTIME PARTS (reader lane prerequisites; presence unverified):']
 lines += [f"{x['path']} | {x['bytes']} | {x['sha256']}" for x in runtime]
 lines += ['', 'TO COPY FROM 1-18 TO IDENTICAL ABSOLUTE PATHS:']
 lines += [f"{x['path']} | {x['bytes']} | {x['sha256']}" for x in copies]
 lines += ['',f"Copy bytes: {sum(p['bytes'] for p in copies)}",'CPU command: kit/cpu_check_228.sh','GPU command (coordinator only): kit/launch_gpu.sh --card <i>','GPU output: out/gpu_b/captures; all three arms share the 4320-second cap.','No G3T/SAM model is loaded. G3T FoVs and the one-capture tower/544 grids are in kit/inputs.','Real scoring on 1-18: kit/score_400b.py --own-root out/gpu_b/captures --out out/real_score_b','The original staging inventory remains in STAGE_228.json and kit_before_b/STAGE_228.txt.','Command producing this inventory: python -B kit/finalize_b.py']
 (out/'STAGE_228.txt').write_text('\n'.join(lines)+'\n')
 print('seal and staging complete',sum(p['bytes'] for p in copies))
if __name__=='__main__':main()
