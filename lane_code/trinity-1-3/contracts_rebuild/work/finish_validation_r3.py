from pathlib import Path
import subprocess
L=Path(__file__).resolve().parents[1];P='/scratch/jjyeung/envs/p1cpu/bin/python'
steps=[
 ('final_suite',[str(L/'work/run_tests_r3.py'),'r3_proof/base','FINAL_APPLIED_R3','contract']),
 ('snapshot_suite',[str(L/'work/run_tests_r3.py'),'r3_snapshot','SNAPSHOT_R3','contract']),
 ('replay_base',[str(L/'work/real_replay_r3/replay.py'),'base','--tag','completed_r3']),
 ('replay_off',[str(L/'work/real_replay_r3/replay.py'),'off','--tag','completed_r3']),
 ('replay_on',[str(L/'work/real_replay_r3/replay.py'),'on','--tag','completed_r3']),
 ('replay_summary',[str(L/'work/real_replay_r3/summarize.py')]),
 ('real_audit',[str(L/'work/real_audit_r3.py')]),
]
for name,args in steps:
    print('START',name,flush=True)
    with (L/f'work/{name}_r3.log').open('w') as log:
        result=subprocess.run([P,'-I','-s','-B',*args],stdout=log,stderr=subprocess.STDOUT)
    print('FINISH',name,result.returncode,flush=True)
    assert result.returncode==0,name
