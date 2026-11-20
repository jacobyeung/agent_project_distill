from pathlib import Path
import sys,json
L=Path.cwd();sys.path[:0]=[str(L/"out/kit_qd/b"),str(L/"work/tree_r1c")]
import z
from student_pilot.r2_exclusions import SEALED
wanted=set(SEALED.values())
def scan(v,path):
 if isinstance(v,dict):
  if any(isinstance(x,str) and x in wanted for x in v.values()):print(path,json.dumps(v)[:1800])
  for k,x in v.items():scan(x,path+"/"+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):scan(x,path+"/"+str(i))
for n in ("k/l.json","k/p.json","k/n.json","k/j.json"):
 scan(z.load(L/"out/kit_qd"/n),n)
