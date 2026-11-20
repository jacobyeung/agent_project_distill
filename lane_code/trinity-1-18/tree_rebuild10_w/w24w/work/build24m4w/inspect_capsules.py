from pathlib import Path
import tarfile,json,sys
L=Path.cwd();sys.path[:0]=[str(L/"out/kit_qd/b")];import z
v=z.load(L/"out/kit_qd/k/l.json")
for p in v["staged_inputs"].get("packages",[]):print(json.dumps({k:x for k,x in p.items() if k!="inventory"})[:2500])
with tarfile.open(L/"work/build24m4h/p.tar") as t:
 files=t.getmembers();print("p.tar members",len(files))
 print([(m.name,m.size) for m in files if m.size>100000][:30])
