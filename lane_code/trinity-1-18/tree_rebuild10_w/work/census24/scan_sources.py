import ast, json, collections, resource, re
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(15<<30,15<<30))
BASE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); T=BASE/'w24j/work/tree_r1'; P=BASE/'w24j/work/build24m4j/p_tree'; K=BASE/'w24j/out/kit_n_go'
CFG=json.loads(Path('n_go_c.json').read_text())
mods={};symbols={};classes={};files={}
# Source only; no source module is imported or executed by this scanner.
for p in T.rglob('*.py'):
 rel=p.relative_to(T)
 if any(x in rel.parts for x in ('tests','__pycache__','.git')) or p.name.startswith('test_'): continue
 m='.'.join(rel.with_suffix('').parts);m=m.removesuffix('.__init__');mods[m]=p
for p in (K/'b').glob('*.py'):mods['kit.'+p.stem]=p

def imports(nodes,m):
 d={}
 for n in nodes:
  if isinstance(n,ast.ImportFrom):
   base='.'.join(m.split('.')[:-n.level]) if n.level else ''
   base='.'.join(x for x in (base,n.module) if x)
   if not n.level and base not in mods and 'kit.'+base in mods:base='kit.'+base
   for a in n.names:
    name='.'.join(x for x in (base,a.name) if x);d[a.asname or a.name]=name
  if isinstance(n,ast.Import):
   for a in n.names:d[a.asname or a.name.split('.')[0]]=a.name if a.asname else a.name.split('.')[0]
 return d

def nodes(n):
 def visit(x,root=False):
  for ch in ast.iter_child_nodes(x):
   if isinstance(ch,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    if isinstance(n,ast.Module) or isinstance(ch,ast.ClassDef):continue
   if isinstance(ch,ast.If):
    test=ast.unparse(ch.test)
    if '__name__' in test and isinstance(n,ast.Module):continue
    if 'cfg' in test:
     try:
      val=eval(compile(ast.Expression(ch.test),'<condition>','eval'),{'__builtins__':{'bool':bool,'set':set,'type':type,'int':int,'len':len,'str':str}}, {'cfg':CFG})
      chosen=ch.body if val else ch.orelse
      for item in chosen:
       yield item;yield from visit(item)
      continue
     except Exception:pass
   yield ch;yield from visit(ch)
 yield from visit(n)
for m,p in mods.items():
 a=ast.parse(p.read_text());im=imports(nodes(a),m);files[m]=(a,im)
 symbols[m+'.<module>']=(m,a,None)
 def add(n,q=''):
  for ch in ast.iter_child_nodes(n):
   if isinstance(ch,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    name=(q+'.' if q else '')+ch.name;symbols[m+'.'+name]=(m,ch,q or None)
    if isinstance(ch,ast.ClassDef):classes[m+'.'+name]=[m+'.'+name+'.'+f.name for f in ch.body if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef))]
    add(ch,name)
 add(a)

blocked_prefixes=('student_pilot.gf1','student_pilot.gx_','student_pilot.g3t_','student_pilot.e2e_','student_pilot.stageb_','student_pilot.mdg_','student_pilot.r2_schedule','student_pilot.r2_training','student_pilot.r2_resume','student_pilot.c1r_align')
allow_blocked={'student_pilot.mdg_parent.model_pin'}
# Explicit phase roots and dynamically dispatched model/data methods.
roots={
 'routing':['kit.rg.regenerate','kit.rb.routing_status','kit.rb.reconstruct','kit.pl.plan_payload','student_pilot.s1_routing.build'],
 'q_prepare':['launch_r1.production_proof.forward','student_pilot.carrier_c1_run.first_batch_check','launch_r1.production_proof.run','launch_r1.entry.frame_host','student_pilot.s1_admission.admit','student_pilot.carrier_c1_run.prepare','student_pilot.r1_population.bind_prepared','student_pilot.r1_loader.production_audit'],
 'admission':['launch_r1.entry.admit','kit.h.<module>','kit.u.<module>'],
 'census_review':['kit.cs.publish','kit.cs.verify','kit.rv.run','kit.z.room_report'],
 'handover':['launch_r1.production_proof.bind_handover','student_pilot.r1_handover.verify_trainable_groups'],
 'train_step':['student_pilot.carrier_c1_run.train','student_pilot.carrier_c1_run.optimize_step','student_pilot.carrier_c1_run.Rows','student_pilot.carrier_c1.CarrierC1','student_pilot.s1_first_step.report','student_pilot.carrier_c1_data.encode_layout_row'],
 'checkpoint':['student_pilot.carrier_c1_run.checkpoint'],
 'export':['student_pilot.carrier_c1_run.export'],
 'stop':['student_pilot.stop_control.requested','kit.o.<module>','kit.pc.Publisher','kit.sr.main'],
 'kit':['kit.a.<module>','kit.t.<module>','kit.g.<module>','kit.d.<module>','kit.rd.publish','kit.ep.publish','kit.pc.main','kit.x.<module>','kit.m.<module>','kit.s.<module>','kit.l.<module>','kit.w.<module>','kit.v.<module>','kit.gc.main','kit.gc.upload']}
# Functions that belong only to other modes/inference/resume or to disabled N features.
excluded={'student_pilot.carrier_c1_run.main','student_pilot.carrier_c1_run.evaluate','student_pilot.carrier_c1_run.inference','student_pilot.carrier_c1_run.probe','student_pilot.carrier_c1_run.load_artifact','student_pilot.carrier_c1_run.restore','student_pilot.carrier_c1_run.dryrun','student_pilot.carrier_c1_run.validation_read','student_pilot.carrier_c1_run.validation_summary','student_pilot.carrier_c1_run.update_best','student_pilot.carrier_c1_run.gx_reference','student_pilot.carrier_c1_run.gx_resume_verdicts','student_pilot.carrier_c1_run.gx_validate_history','student_pilot.carrier_c1_run.gx_step_history','student_pilot.carrier_c1_run.gx_fail_fast','student_pilot.carrier_c1_run.own_values','student_pilot.carrier_c1_run.prepare_validation','student_pilot.carrier_c1_run.milestone_gate','student_pilot.r1_routing.compose_native','kit.z.resolve600','kit.z.checkpoint600','kit.z.receipt600','kit.z.resolve','kit.z.bootstrap','kit.z.launch_shell','kit.rb.child','kit.rb.load_modules','kit.rb.import_probe','kit.rb.probe_modules'}
excluded.difference_update({'kit.z.bootstrap','kit.z.launch_shell','kit.z.resolve'})
roots['kit'].append('kit.resolve.<module>')
seen={};edges={};unresolved=collections.Counter()

def allowed(s):return s not in excluded and (not s.startswith(blocked_prefixes) or s in allow_blocked)
def resolve_attr(n,env,m,scope):
 if isinstance(n,ast.Name):
  if n.id=='self' and scope:return m+'.'+scope
  if n.id in env:return env[n.id]
  if m+'.'+n.id in symbols:return m+'.'+n.id
  if n.id in mods:return n.id
  return n.id
 if isinstance(n,ast.Attribute):return resolve_attr(n.value,env,m,scope)+'.'+n.attr
 return ''
for phase,rr in roots.items():
 queue=list(rr)
 while queue:
  s=queue.pop()
  if not allowed(s) or s not in symbols:continue
  if phase in seen.get(s,set()):continue
  seen.setdefault(s,set()).add(phase)
  m,n,scope=symbols[s];im=dict(files[m][1]);im.update(imports(nodes(n),m));env=im
  # local class instantiations and aliases
  for ch in nodes(n):
   if isinstance(ch,ast.Assign) and isinstance(ch.value,(ast.Call,ast.Name,ast.Attribute)):
    v=resolve_attr(ch.value.func if isinstance(ch.value,ast.Call) else ch.value,env,m,scope)
    if v in classes or v in mods:
     for target in ch.targets:
      if isinstance(target,ast.Name):env[target.id]=v
  refs=set()
  for ch in nodes(n):
   if isinstance(ch,(ast.Name,ast.Attribute)) and isinstance(ch.ctx,ast.Load):
    v=resolve_attr(ch,env,m,scope)
    if v in symbols:refs.add(v)
   if isinstance(ch,ast.Call):
    v=resolve_attr(ch.func,env,m,scope)
    if v in symbols:refs.add(v)
    elif v:unresolved[v]+=1
  if s in classes:refs.update(classes[s])
  # module import-time constants can invoke local checks; include without importing all its functions.
  if not s.endswith('.<module>'):refs.add(m+'.<module>')
  edges[s]=sorted(refs)
  queue.extend(refs)
# Add implicit class dispatch for known core names from direct imports.
records=[]
def walk(n,scope='',guards=(),tries=()):
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):scope=scope+'.'+n.name if scope else n.name
 if isinstance(n,ast.Raise):
  records.append(dict(line=n.lineno,function=scope,exception=ast.unparse(n.exc) if n.exc else 'reraise',guards=list(guards),except_context=list(tries)))
 if isinstance(n,ast.If):
  for ch in n.body:walk(ch,scope,guards+(ast.unparse(n.test),),tries)
  for ch in n.orelse:walk(ch,scope,guards+('NOT ('+ast.unparse(n.test)+')',),tries)
 elif isinstance(n,ast.ExceptHandler):
  for ch in n.body:walk(ch,scope,guards,tries+(ast.unparse(n.type) if n.type else 'BaseException',))
 else:
  for ch in ast.iter_child_nodes(n):walk(ch,scope,guards,tries)
allrows=[]; pr={}
for m,(a,_) in files.items():
 records=[];walk(a)
 rel='b/'+mods[m].name if m.startswith('kit.') else str(mods[m].relative_to(T))
 pp=P/rel;prr=[]
 if pp.is_file():
  keep=records;records=[];walk(ast.parse(pp.read_text()));prr=records;records=keep
 for r in records:
  sym=m+'.'+(r['function'] or '<module>'); phases=seen.get(sym)
  # nested functions execute through their included enclosing function.
  while not phases and '.' in sym.removeprefix(m+'.'):
   sym=sym.rsplit('.',1)[0];phases=seen.get(sym)
  if not phases:continue
  cand=[p for p in prr if p['exception']==r['exception'] and p['function']==r['function']]
  if not cand:cand=[p for p in prr if p['exception']==r['exception']]
  exact=next((p for p in cand if p['guards']==r['guards']),None)
  mark='SAME' if exact else 'STRICTER' if cand else 'NEW'
  allrows.append(dict(file=rel,**r,mark=mark,p_sites=[dict(line=p['line'],function=p['function'],guards=p['guards']) for p in cand],phases=sorted(phases)))
Path('reachable_raw.json').write_text(json.dumps(allrows,indent=2)+'\n')
Path('call_graph.json').write_text(json.dumps(dict(roots=roots,excluded=sorted(excluded),reachable={k:sorted(v) for k,v in seen.items()},edges=edges,unresolved=unresolved),indent=2)+'\n')
counts=collections.Counter(r['file'] for r in allrows)
print('Reachable symbols',len(seen),'raise sites',len(allrows),'marks',collections.Counter(r['mark'] for r in allrows))
print('\n'.join(f'{k}: {v}' for k,v in sorted(counts.items())))
