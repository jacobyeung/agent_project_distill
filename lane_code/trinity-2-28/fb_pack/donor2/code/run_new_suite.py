from pathlib import Path
import subprocess,sys,os
W=Path(__file__).resolve().parents[1];os.chdir(W)
with (W/'out/suite_new.log').open('w') as f:
 r=subprocess.run([sys.executable,'-B','code/run_suite_final.py','new'],stdout=f,stderr=subprocess.STDOUT)
sys.exit(r.returncode)
