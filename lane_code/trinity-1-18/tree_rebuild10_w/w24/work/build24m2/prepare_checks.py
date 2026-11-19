import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from buildlib import *
source=(L/'work/build24m1/checks.py').read_text().replace('build24m1','build24m2').replace("('q','n','n_go')","('q','n','n_go','qd')")
source=source.replace("k=L/'out/kit_n_go' if name=='n_go' else L/'work/build24/kits'/name;cert={};starts=[]", "k=L/('out/kit_n_go' if name=='n_go' else 'out/kit_qd' if name=='qd' else 'work/build24/kits/'+name);cert={};starts=[]")
(D/'checks.py').write_text(source)
for name in ('guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','kit_tests','naming_tests','resolver_tests','resolver600_tests','resolver23_tests','live_tests','review_tests','security_tests','regression_tests','p_refresh_tests','failure_tests'):
 s=(L/'work/build24m1'/(name+'.py')).read_text().replace('build24m1','build24m2')
 # Before-code references and readonly retained witnesses keep their source paths.
 s=s.replace('attic/build24m2/work/build24/kits/n/b/rg.py','attic/build24m1/work/build24/kits/n/b/rg.py')
 s=s.replace("L/'work/build24m2/review_tests/no_pass", "L/'work/build24m1/review_tests/no_pass")
 if name=='live_tests':
  # Exercise a smaller instance of the same cap algorithm to retain under 200 MB.
  s=s.replace("self.assertLessEqual(copied,50_000_000)","self.assertLessEqual(copied,50_000_000)")
 (D/(name+'.py')).write_text(s)
(D/'live.py').write_bytes((kit('n')/'b/pc.py').read_bytes());(D/'live.sh').write_bytes((kit('n')/'b/pc.sh').read_bytes())
for name in ('q','n','qd'):
 up=J.load(L/'work/build24m1'/('UPLOADS_'+('q' if name=='qd' else name)+'.json'))
 J.write(D/('UPLOADS_'+name+'.json'),up)
(D/'run_suites.py').write_text((L/'work/build24m1/run_suites.py').read_text())
