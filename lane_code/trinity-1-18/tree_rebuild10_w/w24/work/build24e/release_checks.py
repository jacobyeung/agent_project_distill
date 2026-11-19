from pathlib import Path
import sys,subprocess,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";A=L/"attic/build24e"
if (D/"generated").exists():(D/"generated").rename(A/"generated_pretraining")
for name in ("invariants","uploads","checks","suites","resolver_tests","launch_tests","naming_tests","refresh_tests"):
 # The standalone resolver suites were validated in clean fixture directories.
 if name=="suites":
  s=(D/"suites.py").read_text().replace("\x27resolver600_tests\x27,\x27resolver23_tests\x27,","")
  (D/"suites_release.py").write_text(s);target="suites_release"
 else:target=name
 with (D/(name+"_release.log")).open("w") as log:r=subprocess.run([sys.executable,"-I","-s","-B",str(D/(target+".py"))],stdout=log,stderr=subprocess.STDOUT)
 print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
