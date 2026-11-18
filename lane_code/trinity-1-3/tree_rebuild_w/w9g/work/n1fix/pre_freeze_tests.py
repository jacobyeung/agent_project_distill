from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix'
result=subprocess.run([sys.executable,'-I','-s','-B',str(B/'test_runner.py'),
    str(B/'proofs/pre_freeze'),'tests.test_r2_n1fix','tests.test_r2_build_n1'],cwd=L)
if result.returncode<0:raise SystemExit('Targeted test process killed; stop without retry.')
raise SystemExit(result.returncode)
