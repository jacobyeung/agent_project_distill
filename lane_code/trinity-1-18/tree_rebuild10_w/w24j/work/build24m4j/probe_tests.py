from common import *
import subprocess,copy
sys.path.insert(0,str(kit('qd')/'b'))
import rb
F=D/'probe';F.mkdir();env=rb.environment();results=[]
for label,change,want in [('real',{},None),('missing',{'probe_modules':['q_missing_24j']},'R1_RECONSTRUCTION_IMPORT_MISSING:q_missing_24j'),('shadow',{},'R1_RECONSTRUCTION_MODULE_SHADOWED:student_pilot')]:
 e=copy.deepcopy(env)
 if label=='shadow':
  site=F/'site';(site/'student_pilot').mkdir(parents=True);(site/'student_pilot/__init__.py').write_text('raise AssertionError("must not execute")\n');e['paths'].insert(0,str(site));e['binds'].append(str(site))
 c=F/(label+'.json');J.write(c,dict(root=str(F),directory=label,environment=e,probe_only=True,**change))
 cmd=rb.command(F,c,D/'p_tree',{},e)
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (F/(label+'.log')).write_text(p.stdout)
 record=J.load(F/(label+'_imports.json'));results.append(dict(case=label,returncode=p.returncode,probe=record))
 print(label,p.returncode,record.get('refusal'),flush=True)
 if want:assert p.returncode and record['refusal']==want,p.stdout
 else:
  print(p.stdout[-2500:],flush=True)
J.write(D/'PROBE_TESTS.json',results)
