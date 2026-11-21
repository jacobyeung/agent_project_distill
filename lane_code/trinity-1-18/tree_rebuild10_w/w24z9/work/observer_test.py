import json,os,subprocess,sys,shutil
from pathlib import Path
J=Path.cwd();W=J/"work/observer_v2";W.mkdir();results={}
for name,src in (("before",J/"inputs/e3/observe.py"),("after",J/"out/e3/observe.py")):
 n=W/name;(n/"k/b").mkdir(parents=True);(n/"obs").mkdir()
 p=n/"k/b/gc.py";p.write_text("import http.client\nc=http.client.HTTPSConnection('example.invalid',443,timeout=1)\nassert type(c) is http.client.HTTPSConnection\nassert type(c).__name__=='HTTPSConnection'\nprint('CONSTRUCTION_PASS')\n")
 shutil.copyfile(src,n/"observe.py")
 r=subprocess.run([sys.executable,"-I","-s","-B",str(n/"observe.py"),str(p)],env={**os.environ,"E3_N":str(n)},capture_output=True,text=True)
 (n/"stdout").write_text(r.stdout);(n/"stderr").write_text(r.stderr)
 results[name]=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
assert results["before"]["returncode"]==1 and "TypeError" in results["before"]["stderr"],results
assert results["after"]["returncode"]==0 and "CONSTRUCTION_PASS" in results["after"]["stdout"],results
results["python"]=sys.version;results["status"]="PASS"
(W/"RESULT.json").write_text(json.dumps(results,indent=2)+"\n")
print(json.dumps(results,indent=2))
