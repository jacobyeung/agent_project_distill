from pathlib import Path
import sys,json,ast,hashlib,shutil
L=Path.cwd();D=L/"work/build24m4y";T=L/"work/tree_r1c"
sys.path.insert(0,str(T))
from student_pilot.r2_exclusions import SEALED
# The supplied 24m4v tree_tests.py names this retained fixture root.
source=Path("/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/fixtures")
module=ast.parse((T/"tests/test_r2_data_path.py").read_text())
call=next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="SOURCES" for t in n.targets))
paths={k.arg:ast.literal_eval(k.value) for k in call.keywords}
records={"work/build6/INIT_INPUT.json":None,**{"work/records/"+n:SEALED[k] for k,n in paths.items()}}
size=sum((source/n).stat().st_size for n in records);assert size<5_000_000,size
checks={}
for n,expected in records.items():
 raw=(source/n).read_bytes();h=hashlib.sha256(raw).hexdigest()
 if expected:assert h==expected,n
 p=D/"tmp/fixtures"/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 checks[n]=dict(source=str(source/n),sha256=h,bytes=len(raw))
(D/"TEST_INPUTS.json").write_text(json.dumps(dict(status="PASS",bytes=size,files=checks,source_authority="Fixture paths named by supplied 24m4v tree_tests.py and unchanged tree test sources; read only"),indent=2)+"\n")
print("Restored exact retained fixtures",len(checks),size)
