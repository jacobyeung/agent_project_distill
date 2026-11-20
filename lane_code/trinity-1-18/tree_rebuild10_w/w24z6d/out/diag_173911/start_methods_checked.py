from pathlib import Path
import os,sys,json,subprocess,shutil
H=Path(__file__).resolve().parent;J=Path.cwd();summary=[]
for method in ("fork","spawn"):
 n=H/("mp_checked_"+method);(n/"k/b").mkdir(parents=True);(n/"obs").mkdir();(n/"sink").mkdir()
 # Test-only prelude survives spawn; no sockets in any child.
 prelude="import sys, http.client\nsys.path.insert(0,"+repr(str(H))+")\nfrom strict_sink import Connection\nif http.client.HTTPSConnection.__module__ == 'http.client': http.client.HTTPSConnection=Connection\n"
 (n/"k/b/gc.py").write_text(prelude+(J/"out/kit_n/b/gc.py").read_text())
 shutil.copyfile(J/"out/e2/observe.py",n/"observe.py")
 runner=n/"runner.py"
 runner.write_text(prelude+"import multiprocessing,runpy\nif __name__ == \"__main__\":\n multiprocessing.set_start_method("+repr(method)+")\n runpy.run_path("+repr(str(n/"observe.py"))+",run_name=\"__main__\")\n")
 names=["object.part%02d-of-04"%i for i in range(4)]
 (n/"sessions.json").write_text(json.dumps({name:"https://local.invalid/"+name for name in names}))
 (n/"payload").write_bytes(b"q"*64)
 env={**os.environ,"E2_N":str(n),"STRICT_SINK":str(n/"sink"),"REQUIRE_RANGE":"0","TMPDIR":str(n)}
 p=subprocess.run([sys.executable,"-I","-s","-B",str(runner),str(n/"k/b/gc.py"),"split",str(n/"sessions.json"),"object",str(n/"payload"),"4","4"],env=env,capture_output=True,text=True,timeout=30)
 (n/"output.log").write_text(p.stdout+p.stderr)
 receipt=n/"sessions.json.receipts.jsonl"
 summary.append(dict(method=method,returncode=p.returncode,receipts=len(receipt.read_text().splitlines()) if receipt.exists() else 0,observations=len(list((n/"obs").glob("r_*.json")))))
(H/"start_methods_checked.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary))
