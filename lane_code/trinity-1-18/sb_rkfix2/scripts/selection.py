"""K1-train-only frame-budget registration and selection; no R0 item reads."""
from common import *
RULE = 'The R0-dev arm is da3_f32 unless the K1 dense-64 input beats it on K1 train with a paired 95% lower bound above 0; then it is da3_u94.'
K1_PRED = Path('/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3')

def training_set():
 refpath=W/'evidence/K1_RULE_VARIANTS.json'
 rows=[r for r in read(refpath)['rows'] if r['split']=='train']
 caps={c['canonical']:c for c in read(K1)['captures']}
 assert len(rows)==110 and len({r['capture'] for r in rows})==110
 for r in rows:
  c=caps[r['capture']]
  assert c['k1_split']=='train' and len(c['anchor_indices'])==32
 return rows,caps,{str(refpath):sha(refpath),str(K1):sha(K1)}

def register(root,code):
 rows,caps,ins=training_set();p=root/'S1C_REGISTRATION.json'
 record=dict(rule=RULE,rule_name='R0',scope='K1 train only',captures=[r['capture'] for r in rows],code_sha256=digest(code))
 if p.exists():
  old=read(p)
  if any(old.get(k)!=v for k,v in record.items()) or old['input_sha256']!={**ins,**code}:raise ValueError('stale S1c registration')
 else: write(p,record,{**ins,**code})
 return rows,caps,ins

def choose(lower): return 'da3_u94' if lower>0 else 'da3_f32'

def select(root):
 if (root/'SELECTION.json').exists():raise RuntimeError('SELECTION.json already exists; selection is frozen')
 from kernel import pipeline,input_code,arrays
 from gates import run_code_hashes,verify_inputs,merge_inputs
 import ast,random
 code=run_code_hashes();rows,caps,ins=register(root,code);ins.update(input_code())
 ins[str(root/'S1C_REGISTRATION.json')]=sha(root/'S1C_REGISTRATION.json')
 stats_path=W/'evidence/k1_rule_variants.py';ins[str(stats_path)]=sha(stats_path)
 nodes=[n for n in ast.parse(stats_path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('mra','boot')]
 ns={'random':random};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(stats_path),'exec'),ns)
 output=[];verified={}
 for r in rows:
  c=caps[r['capture']];p=root/'pred/k1_f32'/r['capture'].replace('/','__')/'pred.npz';d=p.parent/'DONE.json'
  dense=K1_PRED/digest(c)[:16]/'pred.npz';dd=dense.parent/'DONE.json'
  for pred,done in [(p,d),(dense,dd)]:
   if not done.is_file() or not pred.is_file():raise FileNotFoundError('MISSING '+str(pred))
   receipt=read(done)
   if receipt['pred_sha256']!=sha(pred):raise ValueError('corrupt prediction '+str(pred))
   ins[str(pred)]=sha(pred);ins[str(done)]=sha(done)
  b=read(d)['binding'];expected=list(c['anchor_indices'])
  if b['frames']!=expected or b['item_slots']!=list(range(32)) or b['code_sha256']!=code:raise ValueError('stale S1c binding')
  dependencies=read(d)['input_sha256']
  merge_inputs(ins,dependencies)
  verify_inputs({p:h for p,h in dependencies.items() if p not in verified}) if any(p not in verified for p in dependencies) else None
  verified.update(dependencies)
  a=arrays(p);z=arrays(dense)
  assert a['frame_indices'].tolist()==expected and z['frame_indices'].tolist()==[int(f['index']) for f in c['dense_frames']]
  assert z['frame_indices'][z['item_slots'].astype(int)].tolist()==expected
  f32=pipeline(p,root/'geom/k1_f32'/(r['capture'].replace('/','__')+'.npz'),'R0')
  f64=pipeline(dense,root/'geom/k1_dense64'/(r['capture'].replace('/','__')+'.npz'),'R0')
  # Dense and f32 predictions use the same K1-frozen constants.
  output.append(dict(row_id=r['row_id'],capture=r['capture'],room=r['room'],split='train',gt=r['gt'],f32=f32,f64=f64,
                     delta=ns['mra'](f64['area_m2'],r['gt'])-ns['mra'](f32['area_m2'],r['gt'])))
 interval=ns['boot']([(r['room'],r['delta']) for r in output])
 dest=root/'SELECTION.json'
 if dest.exists():raise RuntimeError('SELECTION.json already exists; selection is frozen')
 write(dest,dict(status='COMPLETE',scope='K1 train only',rule=RULE,pricing_rule='R0',arm=choose(interval[1]),dense64_minus_f32=interval,rows=output,code_sha256=digest(code)),ins)
 return read(dest)

def load_selection(root,code):
 from gates import verify_inputs
 p=root/'SELECTION.json'
 if not p.is_file():raise FileNotFoundError('MISSING '+str(p))
 s=read(p)
 if s.get('status')!='COMPLETE' or s.get('scope')!='K1 train only' or s.get('rule')!=RULE or s.get('pricing_rule')!='R0':raise ValueError('invalid selection')
 if s.get('code_sha256')!=digest(code):raise ValueError('stale selection code')
 rows,caps,_=training_set()
 if [r['row_id'] for r in s['rows']]!=[r['row_id'] for r in rows] or any(r['split']!='train' for r in s['rows']):raise ValueError('selection must cover exactly 110 train rows')
 if s['arm']!=choose(s['dense64_minus_f32'][1]):raise ValueError('selection violates registered rule')
 required={str(root/'S1C_REGISTRATION.json'),str(W/'evidence/k1_rule_variants.py')}
 for r,actual in zip(rows,s['rows']):
  if any(actual.get(k)!=r.get(k) for k in ('capture','room','gt')):raise ValueError('selection row identity mismatch')
  f32=root/'pred/k1_f32'/r['capture'].replace('/','__')/'pred.npz'
  dense=K1_PRED/digest(caps[r['capture']])[:16]/'pred.npz'
  required.update(str(p) for p in (f32,f32.parent/'DONE.json',dense,dense.parent/'DONE.json'))
 if not required <= s['input_sha256'].keys():raise ValueError('selection missing S1c input evidence')
 import ast,random
 stats=W/'evidence/k1_rule_variants.py'
 nodes=[n for n in ast.parse(stats.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('mra','boot')]
 ns={'random':random};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(stats),'exec'),ns)
 deltas=[ns['mra'](r['f64']['area_m2'],r['gt'])-ns['mra'](r['f32']['area_m2'],r['gt']) for r in s['rows']]
 if any(r['delta']!=d for r,d in zip(s['rows'],deltas)):raise ValueError('selection delta mismatch')
 interval=ns['boot']([(r['room'],d) for r,d in zip(s['rows'],deltas)])
 if list(interval)!=s['dense64_minus_f32']:raise ValueError('selection bootstrap mismatch')
 verify_inputs(s['input_sha256'])
 return s
