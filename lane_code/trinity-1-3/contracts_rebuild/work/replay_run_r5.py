from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[1]
for arm in ('base','off','on'):
    with (L/f'work/replay_{arm}_r5.log').open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/real_replay_r5/replay.py'),arm,'--tag','completed_r5'],stdout=log,stderr=subprocess.STDOUT)
    print(arm,result.returncode,flush=True)
    assert result.returncode == 0
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/real_replay_r5/summarize.py')],check=True)
