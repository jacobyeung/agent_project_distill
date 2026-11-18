from pathlib import Path
import subprocess,json,sys,os
W=Path(__file__).resolve().parent
script=W/'py36_guard.py'
script.write_text('''import json,sys,tempfile,os,subprocess\nfrom pathlib import Path\no=Path(sys.argv[1]);sys.path[:0]=[str(o),str(o/'src')]\nimport node_check\nfrom orchard_h10.common import install_process_guard,write,sha\nr=o/'checks'/('a'+os.urandom(6).hex());r.mkdir()\ninstall_process_guard(r)\nproof=node_check.check_bundle_guard(o/'package',r)\nwrite(r/'a/1.json',dict(action=1,config={}))\nargv=[sys.executable,'-I','-s','-B',str(r/'a/5.py'),str(r/'a/1.json')]\ncalls=[]\nproof=node_check.dispatch_operator(r,proof,argv,lambda a,**kw:calls.append(a))\nassert calls[0][-2]==str(r/'7.py') and proof['entry_sequence_passed'] is True\n(o/'PY36_GUARD.json').write_text(json.dumps(proof,sort_keys=True,indent=2)+'\\n')\nprint('guard and dispatch passed')\n''')
for k in ('A','B'):
 (W/k/'checks').mkdir(exist_ok=True)
 r=subprocess.run(['/usr/bin/python3','-I','-s','-B',str(script),str(W/k)],env=dict(PATH='/usr/bin:/bin',HOME=os.environ['HOME'],USER='jjyeung',CUDA_VISIBLE_DEVICES=''),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 print(k,r.returncode,r.stdout.decode(),r.stderr.decode());assert r.returncode==0
