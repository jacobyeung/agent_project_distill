import json,os,sys,hashlib,subprocess
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12');K=W/'pkg';B=K/'work/build12';T=K/'work/tree_r1'
sys.path[:0]=[str(T)]
P=W/'tmp/restage_proofs';P.mkdir(parents=True,exist_ok=True)
os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS=str(P))
from student_pilot.p3_provenance import load
from launch_r1.build import build as r1_build,verify as r1_verify
from launch_r2.build import build,verify
from tests.test_r2_build import inputs
root=W/'restage2';root.mkdir(exist_ok=True);out={}
inh=json.loads((B/'inherited/KIT_RESULT.json').read_text())
for name,conn in [('a2','gf1'),('a0','none')]:
    kit=root/name;assert not kit.exists()
    r=build(K/'fixtures/work/kit07ca49df_meta/m',kit,connector=conn,records=inputs(),launch_inputs=inh[name]['launch_inputs'])
    cfg=load(kit/r['config']['path'])
    out[name]=dict(kit=r['kit_sha256'],verify=verify(kit)==r['kit_sha256'],admission=cfg['r2_build2']['admission'],GO=r.get('GO'))
for n in out:
    d=subprocess.run(['diff','-r','-q',str(root/n),str(B/'kits'/n)],capture_output=True,text=True)
    out[n]['diff_vs_packaged']=d.stdout.strip()[:2000] or 'IDENTICAL'
print(json.dumps(out,indent=1));(W/'RESTAGE.json').write_text(json.dumps(out,indent=1))
