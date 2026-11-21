import json,os,subprocess,sys,shutil
from pathlib import Path
J=Path.cwd();W=J/"work/observer_contract";W.mkdir();N=W/"n";(N/"k/b").mkdir(parents=True);(N/"obs").mkdir()
shutil.copyfile(J/"out/e3/observe.py",N/"observe.py")
(N/"k/b/pc.py").write_text("import subprocess,sys\nfrom pathlib import Path\np=Path(__file__).with_name('gc.py')\nr=subprocess.run([sys.executable,'-I','-s','-B',str(p)],check=True)\n")
(N/"k/b/gc.py").write_text("import http.client\nassert http.client.HTTPSConnection.__module__=='http.client'\nassert http.client.HTTPSConnection.getresponse.__module__=='__main__'\nhttp.client.HTTPSConnection('example.invalid',443,timeout=1)\nprint('INJECTION_PASS')\n")
env={**os.environ,"E3_N":str(N)}
r=subprocess.run([sys.executable,"-I","-s","-B",str(N/"observe.py"),str(N/"k/b/pc.py")],env=env,capture_output=True,text=True)
assert r.returncode==0 and "INJECTION_PASS" in r.stdout,(r.stdout,r.stderr)
(W/"injection.log").write_text(r.stdout+r.stderr)
r=subprocess.run([sys.executable,"-I","-s","-B",str(N/"observe.py"),str(W/"disallowed.py")],env=env,capture_output=True,text=True)
assert r.returncode==92,r.returncode
(N/"k/b/ep.py").write_text("import http.client,json\nc=http.client.HTTPSConnection('example.invalid',443,timeout=1)\nr=c.getresponse()\nassert r.status==201 and r.getheader('Range')=='bytes=0-6'\nassert json.loads(r.read())['name']=='q'\nprint('REPLY_PASS')\n")
code="""import http.client,sys,runpy,json
class Response:
 status=201
 def getheader(self,name):return 'bytes=0-6'
 def read(self):return json.dumps(dict(size='7',crc32c='c',md5Hash='m',name='q',generation='g',ignored='drop')).encode()
C=http.client.HTTPSConnection
C.getresponse=lambda self:Response()
path=sys.argv[1];sys.argv=sys.argv[1:]
runpy.run_path(path,run_name='__main__')
assert http.client.HTTPSConnection is C
"""
r=subprocess.run([sys.executable,"-I","-s","-B","-c",code,str(N/"observe.py"),str(N/"k/b/ep.py")],env=env,capture_output=True,text=True)
assert r.returncode==0 and "REPLY_PASS" in r.stdout,(r.stdout,r.stderr)
rows=[json.loads(p.read_text()) for p in (N/"obs").glob('r_*.json')]
assert rows==[dict(size='7',crc32c='c',md5Hash='m',name='q',generation='g')],rows
(W/"reply.log").write_text(r.stdout+r.stderr)
result=dict(status='PASS',allow_list=True,subprocess_injection=True,original_class_identity=True,response_201_metadata=True,response_bytes_and_headers=True)
(W/"RESULT.json").write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
