import sys,ast,json,importlib.util
from pathlib import Path
D=Path(__file__).resolve().parent;T=D/'p_tree'
mods={}
for p in T.rglob('*.py'):
 parts=list(p.relative_to(T).with_suffix('').parts)
 if parts[-1]=='__init__':parts.pop()
 if parts:mods['.'.join(parts)]=p
full={'student_pilot.s1_routing','student_pilot.s1_pool_relocate','student_pilot.s1_pool','student_pilot.ground_rows','student_pilot.s1_exclusions','student_pilot.s1_scene_census','student_pilot.s1_route_policy','student_pilot.row_removals'}
roots=sorted(full|{'student_pilot.carrier_c1_run','student_pilot.ground_tokens','student_pilot.mdg_decode_tokens'})
seen={};external={};queue=roots[:];tops={k.split('.')[0] for k in mods}
def imports(n,all_functions):
 if not all_functions and isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):return
 if isinstance(n,(ast.Import,ast.ImportFrom)):yield n
 for c in ast.iter_child_nodes(n):yield from imports(c,all_functions)
while queue:
 m=queue.pop()
 if m in seen or m not in mods:continue
 p=mods[m];a=ast.parse(p.read_bytes());seen[m]=str(p.relative_to(T));pkg=m if p.name=='__init__.py' else m.rpartition('.')[0]
 for n in imports(a,m in full or (m.startswith(('trace_format.','generator.derivgen_v7.derivgen.')) and not m.endswith('.ground_v312_io'))):
  if isinstance(n,ast.Import):names=[x.name for x in n.names]
  else:
   base=importlib.util.resolve_name('.'*n.level+(n.module or ''),pkg) if n.level else n.module or ''
   names=[base]+[base+'.'+x.name for x in n.names]
  for name in names:
   top=name.split('.')[0]
   if name in mods:queue.append(name)
   elif top not in sys.stdlib_module_names and top not in tops:external.setdefault(top,[]).append(dict(module=m,line=n.lineno,imported=name))
   prefix=name
   while '.' in prefix:
    prefix=prefix.rpartition('.')[0]
    if prefix in mods:queue.append(prefix)
external.setdefault('transformers',[]).append(dict(module='student_pilot.decoupled_v_run',line=50,imported='transformers.AutoProcessor'))
external.setdefault('tokenizers',[])
# Lazy render and token paths called by s1_routing.build.
extra=['trace_format.ground_v312','trace_format.room_v314','generator.derivgen_v7.derivgen.ground_v313_tokens','student_pilot.carrier_c1_routing','student_pilot.ground_tokens','student_pilot.mdg_decode_tokens']
result=dict(modules=seen,external=external,probe=sorted(set(seen)|set(external)|set(extra)|{'scipy.spatial.distance','scipy.spatial.transform'}))
(D/'IMPORT_CLOSURE.json').write_text(json.dumps(result,indent=2)+'\n')
print('MODULES',len(seen),'EXTERNAL',sorted(external))
