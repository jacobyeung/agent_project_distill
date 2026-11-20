import sys,json,traceback,subprocess,base64
from pathlib import Path
from unittest.mock import patch
L=Path.cwd();D=L/"work/build24m4z8";S=Path("/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912")
sys.path[:0]=[str(L/"out/kit_qdp/b"),str(L/"work/tree_r1c")];import pl,z
from launch_r1.build import verify
r=json.loads((S/"k_r.json").read_bytes())["_resolved"]
pool=D/"offline/x";h="a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73"
X="/project/community/jjyeung/okh7/x_22c714e1"
def path(*a,**kw):
 p=Path(*a,**kw)
 return pool/p.relative_to(X) if p.is_relative_to(X) else p
results=[]
for n in ("qd","qdp"):
 k=L/("out/kit_"+n);r["kit_sha256"]=z.seal(k);assert verify(k)==r["kit_sha256"]
 root=D/("offline/"+n);root.mkdir(exist_ok=True)
 try:
  with patch.object(pl,"Path",path):pl.plan_payload(k,r,root,regeneration=False)
 except Exception as e:
  raw=traceback.format_exc();(D/(n+"_plan.log")).write_text(raw)
  results.append(dict(kit=n,seal=r["kit_sha256"],error=str(e),log=str(D/(n+"_plan.log"))))
  assert str(e)==("R1_ROUTING_SELECTION_PIN_MISSING" if n=="qd" else "E10:"+r["archive"]["path"])
 else:raise AssertionError("Unexpected complete offline plan")
with patch.object(pl,"Path",path):pin,source=pl.selection_pin(L/"out/kit_qdp")
assert z.sha(source)==h
p=subprocess.run([sys.executable,"-I","-s","-B",str(L/"out/kit_qdp/b/a.py"),"t",str(D/"never_created")],capture_output=True,text=True)
assert p.returncode!=0 and "ValueError: E03" in p.stderr and not (D/"never_created").exists(),p.stderr
(D/"training_refused.log").write_text(p.stdout+p.stderr)
(D/"REAL_PATH_TESTS.json").write_text(json.dumps(dict(status="OK",cases=results,selection_pin_authenticated=True,training_exit=p.returncode,training_refusal="E03",scope="Unchanged planner and seal/hash checks; only pl.Path maps the Orchard x directory to a local stand-in holding the exact selection. Real resolved record from 173912. No archive or payload substitution."),indent=2)+"\n")
source=base64.b64decode(json.loads((L/"out/kit_qdp/k/j.json").read_bytes())["payload"]).decode()
(D/"j_decoded.sh").write_text(source)
print(json.dumps(results));print("Training refused with E03")
