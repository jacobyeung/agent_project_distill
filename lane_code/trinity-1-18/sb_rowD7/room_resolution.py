"""Measure strict Rooms and N's actual direct-VQA predicates without changing either."""
import ast,collections as C,hashlib,json,sqlite3,sys,types
from pathlib import Path
import cpu_native
from survey import d,authority
B=Path(__file__).resolve().parent;O=B/'out'
rooms,excluded,cfg,removal_pins,division=authority()
d.pin(d.DB,d.DB_SHA)
for dependency in [B/'survey.py',Path(d.__file__)]:d.pin(dependency)
from student_pilot import r1_rooms,carrier_c1_routing as routing
from student_pilot.p3_provenance import load,pinned
from student_pilot.r1_routing import Filters
# Extract exact sealed functions, avoiding trainer/model class imports. No predicate is replaced.
p=d.TREE/'student_pilot/carrier_c1_run.py';tree=ast.parse(p.read_text())
funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('held_row','routed_type','excluded_row','row_source')]
mod=types.ModuleType('student_pilot.carrier_c1_run');mod.__package__='student_pilot';mod.__dict__.update(routing=routing,json=json)
exec(compile(ast.Module(body=funcs,type_ignores=[]),str(p),'exec'),mod.__dict__);sys.modules[mod.__name__]=mod
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Rows')
rowfn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='row')
exec(compile(ast.Module(body=[rowfn],type_ignores=[]),str(p),'exec'),mod.__dict__)
filters=Filters(cfg,cfg['scene_division']);native=r1_rooms.Rooms(cfg['r1_training']['room_authority'])
assert not cfg.get('r2_membership'),'Implement configured R2 membership before continuing'
# These attributes select the exact direct VQA row branch configured by W20.
mem=sqlite3.connect(':memory:');mem.execute('create table rows(i integer primary key,row text,target text)')
reader=types.SimpleNamespace(indices={},mixes={},connections={'vqa':mem},r1_training=cfg['r1_training'],b7_inputs=cfg.get('b7_inputs'),r2_admission=None)
rows=[json.loads(l) for l in (O/'NEW_ROWS.jsonl').read_text().splitlines()];maps=[json.loads(l) for l in (O/'SOURCE_MAP.jsonl').read_text().splitlines()]
con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
counts=C.Counter();examples=[];tierhits=C.Counter();lineage_hits=0
rem=d.row_removals.Removals(removal_pins)
for j,(r,m) in enumerate(zip(rows,maps,strict=True)):
 raw,target=con.execute('select row,target from rows where i=?',(m['source_i'],)).fetchone();s=json.loads(raw)
 assert hashlib.sha256(raw.encode()).hexdigest()==m['source_row_sha256']
 for label,item in [('source',s),('new',r)]:
  status,canonical,how=native.status(item);counts[label+'|Rooms.status|'+status]+=1
  try:native.admit(item);admit='PASS'
  except ValueError as e:admit=str(e)
  counts[label+'|Rooms.admit|'+admit]+=1
  reason=filters.reason(item,'vqa');counts[label+'|Filters.reason|'+str(reason)]+=1
  assert reason is None,(item['qid'],reason)
  i=j*2+(label=='new');mem.execute('insert into rows values(?,?,?)',(i,json.dumps(item),target))
  got,_=mod.row(reader,'vqa',i);assert got==item;counts[label+'|Rows.row|PASS']+=1
  canon,tierhow=rooms.canonical(item);room=rooms.room(canon);assert room==m['room']
  rooms.admit(item)
  for name,ex in excluded.items():tierhits[name]+=int(room in ex)
  assert not any(room in ex for ex in excluded.values()) and not rem.match(item)
  counts[label+'|tiered_alias|PASS']+=1
  lineage_hits+=any(any(key in keys for keys in rem.keys) for key in item.get('label_row_keys',[]))
 if status=='unresolved' and len(examples)<6:
  examples.append(dict(source_qid=s['qid'],new_qid=r['qid'],dataset=s['dataset'],scene=s['scene'],native_canonical=canonical,
   native_resolution=how,strict_admit=admit,tiered_canonical=canon,tiered_room=room,source_and_twin_Filters_reason=None,source_and_twin_Rows_row='PASS'))
assert lineage_hits==0
seal=d.load(d.TREE.parents[1]/'out/TREE_SEAL.json')
for module in list(sys.modules.values()):
 f=getattr(module,'__file__',None)
 if f and str(f).startswith(str(d.TREE)) and str(f).endswith('.py'):
  rel=str(Path(f).relative_to(d.TREE));d.pin(f,seal['files'][rel])
d.pin(p,seal['files'][str(p.relative_to(d.TREE))])
audit=d.load(cfg['r1_training']['room_audit']['path'],cfg['r1_training']['room_audit']['sha256'])
receipt=d.load(cfg['streams']['vqa']['path'],cfg['streams']['vqa']['sha256'])
assert receipt['database']['sha256']==d.DB_SHA
for f in [Path(__file__),B/'cpu_native.py',O/'NEW_ROWS.jsonl',O/'SOURCE_MAP.jsonl',O/'INPUT_AUDIT.json']:d.pin(f)
u=next(i for i,p in enumerate(removal_pins) if p['path'].endswith('/build18/inputs/u.json'))
value=dict(command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python room_resolution.py',input_sha256=d.PINS,
 status='PASS_WITH_NATIVE_ROOM_LIMITATION',tree_sha256=seal['tree_sha256'],config=d.pin(d.KIT/'w20/work/build20/inputs/config.json'),counts=dict(counts),examples=examples,
 native_room_authority=cfg['r1_training']['room_authority'],tiered_alias_map=d.pin(d.BASE/'alias_inputs/out/TIERED_ALIAS_MAP.json'),tiered_exclusion_hits=dict(tierhits),lineage_removal_hits=lineage_hits,
 removal_inputs=removal_pins,u_json_keys=len(rem.keys[u]),u_union_keys=len(rem.keys[-1]),u_json_not_in_union=len(rem.keys[u]-rem.keys[-1]),
 existing_v7_audit=dict(scope=audit['store']['scope'],unresolved=audit['store']['unresolved'],certifies=audit['certifies']),
 exact_path=dict(source='Filters.reason(row, vqa) plus carrier_c1_run.Rows.row(vqa, index)',twins='Same sealed predicates and native row-reader method, with original dataset/scene/frames/options; added provenance names tiered physical-room resolution.',
  test='Unmodified sealed AST function bodies; in-memory SQLite rows; auxiliary target copied verbatim from each source; inert torch module raises on any tensor operation.'),
 evidence=[dict(file='student_pilot/r1_rooms.py',lines='80-83',meaning='Strict Rooms.admit refuses unresolved source rows and twins equally.'),
  dict(file='student_pilot/r1_rooms.py',lines='108-125,176-177',meaning='Exact v7 store pin retains unresolved legacy rows; a different database hash with unresolved rows is refused.'),
  dict(file='student_pilot/r1_routing.py',lines='33-50,89-90',meaning='Direct VQA Filters use original tokens and exclusion aliases; Rooms.admit is called for composed routing slices.'),
  dict(file='student_pilot/carrier_c1_run.py',lines='1104-1134',meaning='Native direct reader applies text, extent, R1 and reserve checks, without calling Rooms.admit.')],
 binding_ready=False,binding_limitation='This delivery does not forge or extend the pinned-v7 store exception. A bound augmented store needs N-side room certification carrying the named tiered alias map; strict native Rooms does not resolve these opaque source tokens.')
(O/'ROOM_RESOLUTION.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
(B/'STATUS.md').write_text('Room verification is complete. Sources and twins pass the same native direct-VQA filters and reader checks. Strict Rooms refuses unresolved opaque source tokens equally for both; the separately pinned tiered map resolves them and passes all five exclusion lists. The delivery does not extend the v7 store exception or claim N binding.\n')
print(json.dumps({k:v for k,v in value.items() if k in ('counts','u_json_keys','u_union_keys','u_json_not_in_union','tiered_exclusion_hits','binding_ready')},indent=1))
