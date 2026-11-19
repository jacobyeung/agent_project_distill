from pathlib import Path
import sys,json,subprocess,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";OLD=L/"work/build24d";sys.path.insert(0,str(L/"work/build24"));import joblib as J
root=D/"go";root.mkdir(exist_ok=True);ns="/tmp/q_22c714e1"
for fn in ("boundary.py","fixture_gates.py","cpu_python","go_train.py","go_result.py"):
 s=(OLD/fn).read_text().replace("work/build24d","work/build24e")
 if fn=="boundary.py":
  s=s.replace("D/\x27go/p/q/c.json\x27","L/\x27work/build24d/go/p/q/c.json\x27").replace("D/\x27go/p/q/p\x27","L/\x27work/build24d/go/p/q/p\x27")
  s=s.replace("if stream not in (\x27vqa\x27,\x27pointing\x27)","if stream not in (\x27vqa\x27,\x27pointing\x27)")
 (D/fn).write_text(s)
(D/"cpu_python").chmod(0o755)
cfg=J.load(OLD/"go/input2.json");pin=J.write(root/"input2.json",cfg);request=J.load(OLD/"go/r2.json");request["config"]=pin;request["staged_pins"]=[pin]
J.write(root/"r2.json",request);J.write(root/"n.json",J.load(OLD/"go/n.json"))
args=J.load(OLD/"GO_VIEW.json")+ ["--bind",str(root),str(root),"--bind",str(root),ns,"--ro-bind",str(OLD/"go/p"),ns+"/p"]
J.write(D/"GO_VIEW.json",args)
k=L/"out/kit_n_go";cmd=args+[sys.executable,"-B",str(D/"boundary.py"),str(k/"b/a.py"),"q",ns+"/p2",ns+"/r2.json"]
with (root/"canary.log").open("w") as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
result=J.load(root/"p2/q/RESULT.json") if (root/"p2/q/RESULT.json").exists() else {}
J.write(D/"GO_CANARY_FINAL.json",dict(returncode=r.returncode,status=result.get("status"),refusal=result.get("refusal"),result_path=str(root/"p2/q/RESULT.json"),final_kit_seal=J.seal(k)))
print("canary",r.returncode,result.get("status"),result.get("refusal"),flush=True)
if r.returncode==0:subprocess.run([sys.executable,"-B",str(D/"go_train.py")],check=False)
subprocess.run([sys.executable,"-B",str(D/"go_result.py")],check=True)
