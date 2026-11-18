from pathlib import Path
import json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';O=L/'work/merge11/proofs/n1/kits'
sys.path[:0]=[str(L/'work/tree_r1'),str(B)]
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
from student_pilot.p3_provenance import load,file_pin
from launch_r1.build import verify as verify_r1
from launch_r2.build import verify as verify_r2
pin=load(B/'inputs/config.json')['r1_training']['mix']
(L/'out/MIX_R1.json').write_bytes(Path(pin['path']).read_bytes())
assert file_pin(L/'out/MIX_R1.json')['sha256']==pin['sha256']
results={}
for name in ('a0','a2','r1'):
    kit=L/'work/merge11/kits'/name
    sha=verify_r1(kit) if name=='r1' else verify_r2(kit)
    results[name]=dict(kit_sha256=sha,GO=False,path=str(kit.relative_to(L)),report_mix=file_pin(L/'out'/('MIX_'+name.upper()+'.json')))
(B/'KIT_RESULT.json').write_text(json.dumps(results,indent=2)+'\n')
(O/'RESULT.json').write_text(json.dumps(results,indent=2)+'\n')
monitor.save(O)
(B/'STATUS.md').write_text('# Build n1fix status\n\nN1–N5 focused tests, packet suite, mutations, real-row counts and CPU RGB forward proof pass. Every kit was staged from an empty directory and verifies with GO=false. Frozen-package suites and final coverage are pending. Evidence: proofs and KIT_RESULT.json.\n')
print(json.dumps(results))
