"""Freeze report-only arms and stage compact, authenticated G3T FoVs."""
from core import *
import numpy as np,shutil,datetime

def main():
 bars_path=ROOT/'out/BARS_FROZEN.json';bars=read(bars_path)
 lane=pathlib.Path('/scratch/jjyeung/orch_n30/so_reads228/out')
 plan=read(lane/'STAGE_PLAN.json');env=plan['environment']
 shutil.copyfile(lane/'STAGE_PLAN.json',KIT/'inputs/READER_STAGE_PLAN.json')
 shutil.copyfile(lane/'evidence/q/env.json',KIT/'inputs/READER_ENV.json')
 arcs=[{'path':p['target'],'sha256':p['sha256'],'bytes':p['bytes']} for a in plan['input_archives'] for p in a['parts'] if pathlib.Path(p['target']).name in ('a2.tar','a3.tar','a4.tar')]
 required={'input_sha256':{str(KIT/'inputs/READER_STAGE_PLAN.json'):sha(KIT/'inputs/READER_STAGE_PLAN.json'),str(KIT/'inputs/READER_ENV.json'):sha(KIT/'inputs/READER_ENV.json')},'target_python':env['python'],'python_args':['-B','-I'],'base_env':env['local_base_env'],'base_python':env['local_base_python'],'env_roots':env['env_roots'],'receipt':env['receipt'],'modules':{k:{'version':v} for k,v in env['versions'].items()},'archives':arcs,'runtime_archives':plan['runtime_archives'],'status':'Pinned reader environment; target imports unverified; no substitution','confound':'400: Torch 2.13.0+cu130; A544: Torch 2.11.0+cu129'}
 atomic(KIT/'inputs/ENV_REQUIRED.json',required)
 p=ROOT/'out/BARS_FROZEN_B.json'
 if p.exists():raise Refusal('Variant bars already frozen')
 atomic(p,{'schema':'sb-own400b-bars-v1','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_sha256':{str(bars_path):sha(bars_path),str(KIT/'inputs/ENV_REQUIRED.json'):sha(KIT/'inputs/ENV_REQUIRED.json'),str(pathlib.Path(__file__)):sha(__file__)},'decision':'Only BARS_FROZEN.json decides; V1/V2 report-only','arms':{'A':'544 pose-head FoV','B':'400 pose-head FoV','V1':'400 private depth.fov on private captured.states','V2':'400 frozen G3T raw_pose[anchor_slots,7:9]'},'folds':bars['folds'],'metric':bars['metric'],'thresholds':bars['thresholds'],'bootstrap':bars['bootstrap'],'pairs':bars['pairs'],'fov_agreement':'median absolute degrees over anchors and both axes, pairwise by dataset','env_sensitivity':'B=m*A scale; search all score-change events for the first m>1 passing both folds and combined; also report closest decrease below 1; synthetic only'})
 pins={str(bars_path):sha(bars_path)};items={}
 for r in bars['captures']:
  t=r['tower'];checked(t['path'],t['sha256']);pins[t['path']]=t['sha256'];pins[t['receipt']]=sha(t['receipt'])
  rec=read(t['receipt']);assert rec['capture_sha256']==r['capture_sha256'] and not rec['synthetic']
  with np.load(t['path']) as z:
   slots=z['anchor_slots'];assert np.array_equal(z['frame_indices'][slots],r['anchor_indices'])
   fov=z['raw_pose'][slots,7:9];assert fov.shape==(32,2) and np.isfinite(fov).all() and ((fov>0)&(fov<np.pi)).all()
  items[r['canonical']]={'capture_sha256':r['capture_sha256'],'anchor_indices':r['anchor_indices'],'fov_hw_rad':fov.tolist(),'source_sha256':t['sha256']}
 atomic(KIT/'inputs/G3T_FOV.json',{'input_sha256':pins,'conversion':'g3t_online.pose9 already unpads square FoV: 2*atan(crop_hw*tan(local_fov/2)); cached columns are vertical,horizontal radians','captures':items})
 first=bars['captures'][0];assert first['canonical']=='arkitscenes/41048124'
 for name,arm in [('OWN544_ONE.npz','own544'),('TOWER_ONE.npz','tower')]:
  checked(first[arm]['path'],first[arm]['sha256']);shutil.copyfile(first[arm]['path'],KIT/'inputs'/name)
 atomic(KIT/'inputs/CPU_ONE.json',{'input_sha256':{str(bars_path):sha(bars_path),**{str(KIT/'inputs'/n):sha(KIT/'inputs'/n) for n in ('OWN544_ONE.npz','TOWER_ONE.npz')}},'capture':first})
 (ROOT/'STATUS.md').write_text('Stage B inputs are frozen before variant scoring. The reader environment pins Torch 2.13.0+cu130 and Transformers 5.19.0; target imports remain unverified. All cached G3T FoVs and the first capture’s 544 and tower grids are authenticated and staged. BARS_FROZEN.json remains unchanged.\n')
if __name__=='__main__':main()
