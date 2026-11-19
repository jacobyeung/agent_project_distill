import sys,json
sys.dont_write_bytecode=True
SRC='/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src'
sys.path.insert(0,SRC)
from collections import Counter,defaultdict
from h1eval.items import load_manifest
from h1eval import scorers
m=load_manifest('/scratch/jjyeung/orch_n30/sb_rowA/out/HELDOUT_CAMERA_ITEMS.json')
res=Counter()
for x in m['items']:
  i,j=x['display_frame_pair'];name='turn' if x['question_type']=='camera_rotation' else 'move'
  call=f'<{name} from={i} to={j}>'
  resp='turn = +10 deg' if name=='turn' else 'dx = +1.00 m, dy = +0.00 m, dz = +0.10 m, distance = 1.00 m'
  out=dict(text=f'<think>{call}</think><answer>{x["answer"]}</answer>',finish='eos',calls=[dict(call=call,response=resp,at_token=5,served=True)],tokens=[])
  rew='-sbca-' in x['id']
  try:
    a=scorers.accuracy(out,x);b=scorers.benchmark(out,x)
    uf=scorers.unit_factor(x['question']) if x['question_type']=='camera_displacement' else None
    res[(rew,x['question_type'],'acc',a['task_accuracy'],'M4',b['score'],'unit',uf,'unscored',any('unscored_reason' in c for c in a['calls']))]+=1
  except Exception as e:res[(rew,x['question_type'],type(e).__name__,str(e)[:60])]+=1
for k,v in sorted(res.items(),key=str):print(k,v)
tw=json.load(open('/scratch/jjyeung/orch_n30/sb_rowA/out/HELDOUT_CAMERA_TWINS.json'))
it={x['id']:x for x in m['items']}
ct=defaultdict(Counter);ds=defaultdict(Counter)
for p in tw['twins']:
  o=it[p['original_id']]
  if p['type']=='camera_movement_direction':ct[p['wording_id']][o['answer']]+=1
  ds[(p['type'][7:10],p['wording_id'])][o['dataset']]+=1
for w in sorted(ct):print('dir',w,dict(sorted(ct[w].items())))
for k in sorted(ds):print('ds',k,dict(ds[k]))
