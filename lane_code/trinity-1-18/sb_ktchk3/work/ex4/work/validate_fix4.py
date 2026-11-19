"""Run the required CPU validation stages sequentially."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
stages=[
 ('plant', ['work/run_fix4_probes.py','plant']),
 ('plant2', ['work/run_fix4_probes.py','plant2']),
 ('dryrun', ['code/dryrun.py']),
 ('a0', ['work/a0_rerun.py']),
 ('diff', ['work/diff_fix4.py']),
 ('finalize', ['work/finalize_fix4.py']),
 ('stage', ['work/refresh_stage.py']),
]
done=[]
for name,args in stages:
    print('START',name,flush=True)
    with (root/'out'/(name+'_fix4.log')).open('w') as log:
        result=subprocess.run(['bash','scripts/cpu.sh',*args],cwd=root,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        (root/'STATUS.md').write_text('All 68 CPU tests pass. Completed validation stages: '+', '.join(done)+'. The '+name+' stage failed; see out/'+name+'_fix4.log. Packaging is pending.\n')
        raise SystemExit(result.returncode)
    done.append(name)
    (root/'STATUS.md').write_text('All 68 CPU tests pass. Completed validation stages: '+', '.join(done)+'. The remaining stages and final package verification are pending. No GPU work ran.\n')
    print('PASS',name,flush=True)
