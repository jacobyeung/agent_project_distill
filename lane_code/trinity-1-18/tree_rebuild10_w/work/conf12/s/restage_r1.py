import json,os,sys,subprocess
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12');K=W/'pkg';B=K/'work/build12';T=K/'work/tree_r1'
sys.path[:0]=[str(T)];os.chdir(K)
P=W/'tmp/restage_proofs';os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS=str(P))
from launch_r1.build import build as r1_build,verify as r1_verify
kit=W/'restage_r1f';assert not kit.exists()
LI=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs');r=r1_build(LI/'config.json',LI,kit);out=dict(kit=r['kit_sha256'],verify=r1_verify(kit)==r['kit_sha256'],GO=r['GO'])
d=subprocess.run(['diff','-r','-q',str(kit),str(B/'kits/r1')],capture_output=True,text=True);out['diff_vs_packaged']=d.stdout.strip()[:2000] or 'IDENTICAL'
print(json.dumps(out,indent=1));(W/'RESTAGE_R1.json').write_text(json.dumps(out,indent=1))
