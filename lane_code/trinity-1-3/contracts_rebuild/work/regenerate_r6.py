from pathlib import Path
import subprocess, sys
L=Path(__file__).resolve().parents[1]; W=L/'work/row_families_r6'
for arm in ('base','off','on'):
    for script,stem in [('render_arms.py',''),('supplement.py','supplement_')]:
        with (W/f'{stem}{arm}.log').open('w') as log:
            result=subprocess.run([sys.executable,'-I','-s','-B',str(W/script),'--arm',arm,'--output',str(W/f'{stem}{arm}.json')],stdout=log,stderr=subprocess.STDOUT)
        print(arm,script,result.returncode,flush=True)
        assert result.returncode == 0
subprocess.run([sys.executable,'-I','-s','-B',str(W/'compare.py')],check=True)
