from common import *
import subprocess
records=[]
for name in ("kit_tests","naming_tests","guard_q_new","guard_n_new","guard_q_legacy","guard_n_legacy","review_tests"):
    with (D/(name+".log")).open("w") as f:
        p=subprocess.run([sys.executable,"-B","-s",str(D/(name+".py"))],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,"B21C_PORTABLE":"1"})
    records.append(dict(name=name,returncode=p.returncode));J.write(D/"REGRESSIONS.json",records)
    print(name,p.returncode,flush=True)
    if p.returncode:print((D/(name+".log")).read_text()[-2000:],flush=True)
