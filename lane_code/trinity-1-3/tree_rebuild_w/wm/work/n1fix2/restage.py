from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
(L/'work/merge11/kits').rename(L/'work/merge11/proofs/n1/kits/staged_before_report_binding')
subprocess.run([sys.executable,'-I','-s','-B',str(B/'stage9.py')],check=True)
