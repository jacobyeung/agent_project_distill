from common import *
import subprocess
records=[]
for name in ("guard_q_legacy","guard_q_new","guard_n_legacy","guard_n_new"):
 with (D/(name+"_fixed.log")).open("w") as f:r=subprocess.run([sys.executable,"-B","-s",str(D/(name+".py"))],stdout=f,stderr=subprocess.STDOUT)
 records.append(dict(name=name,returncode=r.returncode));assert r.returncode==0,name
J.write(D/"GUARD_SUITES.json",records)
print("Guards PASS")
