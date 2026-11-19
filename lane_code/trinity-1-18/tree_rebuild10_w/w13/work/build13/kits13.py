"""Stage every review kit from an empty directory, with GO=false."""
from pathlib import Path
import sys,os,json
L=Path(__file__).resolve().parents[2];B=L/'work/build13';T=L/'work/tree_r1';O=B/'proofs/kits'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
m=Monitor(T)
from student_pilot.p3_provenance import load,file_pin
from launch_r1.build import build as r1_build,verify as r1_verify
from launch_r2.build import build,verify
from tests.test_r2_build import inputs
root=B/'kits';root.mkdir(exist_ok=True);results={}
prior=load(L/'work/n1fix2/inherited/KIT_RESULT.json')
for name,connector in [('a2','gf1'),('a0','none')]:
    kit=root/name;assert not kit.exists() or not any(kit.iterdir())
    result=build(L/'fixtures/work/kit07ca49df_meta/m',kit,connector=connector,records=inputs(),launch_inputs=prior[name]['launch_inputs'])
    assert verify(kit)==result['kit_sha256']
    cfg=load(kit/result['config']['path']);assert cfg['r2_build2']['admission'] is False
    result['GO']=False;results[name]=result
kit=root/'r1';assert not kit.exists() or not any(kit.iterdir())
result=r1_build(B/'inputs/kit_config.json',L/'work/n1fix2/inputs',kit)
assert r1_verify(kit)==result['kit_sha256'] and result['GO'] is False
cfg=load(kit/'k/c.json');staging=load(kit/'k/s.json');host=load(kit/'k/h.json')
for pin in cfg['r1_training']['row_slice_inputs'].values():
    assert staging['entries'][pin['path']].get('required_parameter')=='verified_remote_source'
assert 'payload' in staging['entries'][cfg['r1_training']['source_membership']['path']]
assert host['steps']==['s1_routing.build','r1_routing.compose_native','carrier_c1_run.prepare','r1_population.bind_prepared','r1_loader.production_audit']
results['r1']=dict(result,slices=cfg['r1_training']['row_slice_inputs'],membership=cfg['r1_training']['source_membership'])
(B/'KIT_RESULT.json').write_text(json.dumps(results,indent=2));(O/'RESULT.json').write_text(json.dumps(results,indent=2))
m.save(O)
(B/'STATUS.md').write_text('# Build 13 status\n\nGO=false. Every kit was staged from empty and passed its scanner/hash verifier. R1 carries the three slice requirements and pinned membership catalog; remote delivery and host inputs remain unresolved. Evidence: KIT_RESULT.json. Final suites and coverage remain.\n')
print(json.dumps({k:v['kit_sha256'] for k,v in results.items()}))
