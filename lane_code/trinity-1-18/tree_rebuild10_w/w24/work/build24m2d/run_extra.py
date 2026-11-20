from common import *
import subprocess
records=[]
for script,args in [('native_host_tests',[]),*[("planner_all",[n]) for n in ('q','n','n_go','qd')],('source_pin_tests',[]),('publication_tests',[]),('discovery_shell',[]),('regression_tests',[])]:
 name=script+('_'+args[0] if args else '')
 with (D/(name+'.log')).open('w') as f:
  r=subprocess.run([sys.executable,'-B','-s',str(D/(script+'.py')),*args],stdout=f,stderr=subprocess.STDOUT)
 records.append(dict(name=name,returncode=r.returncode));J.write(D/'EXTRA_SUITES.json',records)
 print(name,r.returncode,flush=True)
 if r.returncode:print((D/(name+'.log')).read_text()[-3000:],flush=True)
