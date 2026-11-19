from pathlib import Path
import sys,subprocess
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";A=L/"attic/build24e"
if (D/"generated").exists():(D/"generated").rename(A/"generated_before_extended")
for name in ("q","n"):
 p=D/"sequence_final"/name/"q_22c714e1_20/p"
 if p.exists():p.rename(A/("sequence_"+name+"_p"))
for name in ("invariants","checks","sequence_final","pin_tests","kit_tests","launch_tests"):
 with (D/(name+"_validated.log")).open("w") as log:r=subprocess.run([sys.executable,"-I","-s","-B",str(D/(name+".py"))],stdout=log,stderr=subprocess.STDOUT)
 print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
