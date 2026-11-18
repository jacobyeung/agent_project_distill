"""Stage all review kits from fresh directories with no launch authorization."""
from pathlib import Path
import hashlib,json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';P=B/'proofs/kits';P.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(P))
from student_pilot.p3_provenance import load,file_pin
from launch_r1.build import build as r1_build,verify as r1_verify
from launch_r2.build import build,verify,capsule_json
from tests.test_r2_build import inputs
root=B/'kits';root.mkdir(exist_ok=True)
results={}
inherited=json.loads((L.parent/'work/build9/kits/RESULTS.json').read_text())
for name,connector in [('a2','gf1'),('a0','none')]:
    kit=root/name
    assert not kit.exists() or not any(kit.iterdir())
    old=next(v for v in inherited if v['kit_path'].endswith('/'+name))
    value=old['launch_inputs']
    result=build(L/'fixtures/work/kit07ca49df_meta/m',kit,connector=connector,records=inputs(),launch_inputs=value)
    assert verify(kit)==result['kit_sha256']
    cfg=load(kit/result['config']['path']);pin=cfg['r2_build2']['mix']
    raw=(kit/pin['path']).read_bytes();report=L/'out'/('MIX_'+name.upper()+'.json')
    report.write_bytes(raw)
    assert cfg['r2_build2']['admission'] is False
    result.update(report_mix=file_pin(report),GO=False)
    results[name]=result
kit=root/'r1';assert not kit.exists() or not any(kit.iterdir())
result=r1_build(B/'inputs/config.json',B/'inputs',kit);assert r1_verify(kit)==result['kit_sha256'];assert result['GO'] is False
assert load(B/'inputs/config.json')['r1_training']['mix']['sha256']==file_pin(L/'out/MIX_R1.json')['sha256']
results['r1']=result
(B/'KIT_RESULT.json').write_text(json.dumps(results,indent=2)+'\n')
(P/'RESULT.json').write_text(json.dumps(results,indent=2)+'\n')
monitor.save(P)
print(json.dumps({k:{a:v[a] for a in ('kit_sha256','GO')} for k,v in results.items()}))
