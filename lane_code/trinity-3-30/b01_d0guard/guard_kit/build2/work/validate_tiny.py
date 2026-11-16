from pathlib import Path
import importlib.util,json,sys
B=Path(__file__).resolve().parents[1];K=B/'out/guard_kit';sys.path[:0]=[str(K/'reviewed/checker'),str(K)]
import export_check as E
import common
from guard_core import read,write,sha
F=B/'out/rehearsal/whole/sandbox/fixture';prep=read(F/'PREPARATION.json')
results=[]
for role,step,run in [('proof',544,'469ddece'),('candidate',50,'359fcc3c')]:
 actual=F/role/('m'+str(step))
 logical='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/'+run+'/m'+str(step)
 def local(p):
  p=str(p)
  return (actual/p[len(logical)+1:]).resolve() if p.startswith(logical+'/') else Path(p).resolve()
 common.local=E.local=local
 entry=prep['assets'][role]
 value=E.check_export(actual/'artifact.json',entry['artifact']['sha256'],entry['base'],step)
 results.append(dict(role=role,result=value))
write(B/'out/rehearsal/whole/TENSOR_CHECKS.json',dict(status='PASS',fixture=True,checks=results,
    boundary='Path transport only; unchanged full safetensors checker executed; no model weights loaded'))
print('PASS')
