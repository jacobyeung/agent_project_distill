from pathlib import Path
import sys,tarfile,hashlib,ast,json,importlib.util
L=Path(__file__).resolve().parents[2];D=L/"work/build24m4k"
sys.path[:0]=[str(L/"out/kit_qd/b"),str(L/"work/tree_r1")]
import z
src=L/"work/build24m4h/p.tar"
print("Local archive",z.sha(src),"; authenticate extracted file inventory against P seal")
T=D/"p_tree"
with tarfile.open(src) as t:t.extractall(T,filter="data")
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
assert digest(inventory(T)).startswith("b83a8a35")
mods={}
for p in T.rglob("*.py"):
 rel=p.relative_to(T).with_suffix("");parts=list(rel.parts)
 if parts[-1]=="__init__":parts.pop()
 if parts:mods[".".join(parts)]=p
roots=["student_pilot.s1_routing","student_pilot.s1_pool_relocate"]
seen={};external={};dynamic=[];queue=roots[:];tops={k.split(".")[0] for k in mods}
while queue:
 m=queue.pop()
 if m in seen or m not in mods:continue
 p=mods[m];a=ast.parse(p.read_bytes());seen[m]=str(p.relative_to(T));pkg=m if p.name=="__init__.py" else m.rpartition(".")[0]
 for n in ast.walk(a):
  names=[]
  if isinstance(n,ast.Import):names=[x.name for x in n.names]
  if isinstance(n,ast.ImportFrom):
   base=importlib.util.resolve_name("."*n.level+(n.module or ""),pkg) if n.level else n.module or ""
   names=[base]+[base+"."+x.name for x in n.names]
  if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id=="__import__") or (isinstance(n.func,ast.Attribute) and n.func.attr in ("import_module","spec_from_file_location"))):dynamic.append(dict(module=m,line=n.lineno,code=ast.unparse(n)))
  for name in names:
   top=name.split(".")[0]
   if name in mods:queue.append(name)
   elif top not in sys.stdlib_module_names and top not in tops:
    external.setdefault(top,[]).append(dict(module=m,line=n.lineno,imported=name))
   prefix=name
   while "." in prefix:
    prefix=prefix.rpartition(".")[0]
    if prefix in mods:queue.append(prefix)
z.write(D/"IMPORT_WALK.json",dict(roots=roots,modules=seen,external=external,dynamic=dynamic,scope="All AST imports including every function body; conservative superset, not all functions execute during build"))
print("P modules",len(seen),"external",sorted(external),"dynamic",dynamic)
s=(L/"work/build24m4i/common.py").read_text().replace("build24m4i","build24m4j")
s=s[:s.index("def input_file")]+'''def input_file(h):
 for base in (D/"inputs",L/"work/build24m4i/inputs",L/"work/build24m4h/inputs",L/"work/build24m4e/inputs",L/"work/build24m4d/inputs",L/"work/build24m4d/upload/u"):
  p=base/h
  if p.is_file() and J.sha(p)==h:return p
 raise ValueError("LOCAL_INPUT_MISSING:"+h)
'''
(D/"common.py").write_text(s)
(D/"bootstrap.py").write_text((L/"work/build24m4i/bootstrap.py").read_text())
(D/"run.sh").write_text('''#!/bin/bash
set -euo pipefail
J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24k
ulimit -v 16777216
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME="$J/work/build24m4k/cache" TMPDIR="$J/work/build24m4k/tmp"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
exec nice -n 10 bwrap --ro-bind / / --bind "$J" "$J" --dev-bind /dev /dev --proc /proc --unshare-net --chdir "$J" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$J/work/build24m4k/bootstrap.py" "$@"
''')
