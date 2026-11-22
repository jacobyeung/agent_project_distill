"""Operator dispatch: one item list read twice, in two orders, each order in its own worker process."""
import json,sys,time,hashlib,threading
from pathlib import Path

RULE='candidates_argmax'
# Canonical positions of the 150 chosen items in the package's routed list, in read-0 order.
IDX=[474, 482, 483, 487, 488, 489, 492, 497, 517, 518, 521, 522, 523, 543, 550, 551, 561, 564, 566, 570, 573, 575, 577, 580, 585, 586, 590, 594, 596, 599, 601, 602, 606, 620, 625, 628, 632, 633, 42, 73, 79, 84, 128, 134, 150, 189, 207, 209, 222, 229, 264, 265, 274, 275, 301, 312, 320, 324, 328, 337, 349, 363, 381, 387, 398, 404, 405, 406, 412, 417, 420, 423, 426, 432, 433, 8, 14, 47, 57, 64, 66, 81, 108, 119, 125, 148, 157, 173, 194, 202, 208, 218, 244, 258, 281, 287, 297, 316, 318, 319, 326, 335, 341, 345, 352, 376, 383, 388, 399, 415, 418, 446, 1, 16, 20, 51, 52, 55, 59, 68, 71, 80, 88, 135, 137, 149, 156, 170, 176, 192, 205, 214, 226, 227, 241, 249, 261, 283, 299, 304, 311, 322, 346, 378, 414, 424, 425, 427, 440, 442]
SOURCE_SET='7162af725a9ee3e25e6054ee7d0cffc210c99d10ad8b097c6d3fb5b3319f7910'
FORWARD_SHA='35cb48e2b49ad01cc4efa85dd7d92e4d514c09a0f5f9cfd3ee785691b743c725'
REVERSE_SHA='953fa8a94083e6715a150cf1a41d5a09aa4baddc7a4e433c03d0a1f4b75ec69a'
# Type positions in orchard_h10.common.ORDER; read 1 is read 0 reversed.
SEQUENCES=((3,0,1,2),(2,1,0,3))
# CPU check only: type 3's ground calls build a tower that allocates on CUDA by construction.
CPU_SKIPPED=(3,)
EXPECTED=150
WRAPPER='"""Private dispatch. Only this numeric entry and its numeric config reach argv.\nRead 1 takes each item list in reverse; read 0 keeps it."""\nimport json\nfrom pathlib import Path\nimport sys\n\ncfg=json.loads(Path(sys.argv[1]).read_text())\np=Path(cfg[\'package\'])\nsys.path[:0]=[str(p/\'b\'),str(p/\'tree\'),str(p)]\nfrom orchard_h10.common import install_process_guard\ninstall_process_guard(Path(sys.argv[1]).resolve().parent)\nif cfg[\'action\']!=2 or cfg[\'config\'][\'q\'] not in (0,1):raise ValueError(\'Invalid dispatch\')\nfrom orchard_h10.runner import worker_args\nfrom h1eval.h10 import launch\nif cfg[\'config\'][\'q\']==1:\n    kept=launch.selected\n    def selected(items, value):\n        return kept(items, value)[::-1]\n    launch.selected=selected\nraise SystemExit(launch.main(worker_args(cfg)))\n'


def ids_sha(ids):
 return hashlib.sha256(json.dumps(list(ids)).encode()).hexdigest()


def subset(package,path):
 """Write the 150-item list with the package's own builder; return the ids in read-0 order."""
 from h1eval.items import manifest,load_manifest,K
 source=Path(package)/'items/devs1_routed.json'
 full=json.loads(source.read_text())
 if full['item_set_sha256']!=SOURCE_SET or load_manifest(source)['item_set_sha256']!=SOURCE_SET:
  raise ValueError('Source list differs')
 rows=full['items']
 if len(set(IDX))!=EXPECTED:raise ValueError('Index list differs')
 forward=[rows[i]['id'] for i in IDX]
 if ids_sha(forward)!=FORWARD_SHA or ids_sha(forward[::-1])!=REVERSE_SHA:raise ValueError('Chosen order differs')
 value=manifest('devs1_routed',[rows[i] for i in sorted(IDX)],source)
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 text=json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n'
 if path.exists() and path.read_text()!=text:raise ValueError('Item list differs')
 path.write_text(text)
 loaded=load_manifest(path)
 if [r['id'] for r in loaded['items']]!=sorted(forward) or loaded['count']!=EXPECTED:raise ValueError('Item list differs')
 return forward


def planned(order,manifest_items,sequence):
 from orchard_h10.common import ORDER
 ids=[r['id'] for t in sequence for r in manifest_items if r['question_type']==ORDER[t]]
 return ids if order==0 else ids[::-1]


def descriptors():
 return [dict(arm='tower',modes=['none'],stage1_select_rule=RULE,save_own_depth=False,
              perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
              types=list(SEQUENCES[i]),q=i,expected=EXPECTED) for i in (0,1)]


def sealed_write(path,value):
 from orchard_h10.common import write
 if path.exists() and json.loads(path.read_text())!=value:raise ValueError('Read identity differs')
 write(path,value)


def prepare(config):
 from orchard_h10.common import ORDER,canonical
 from orchard_h10.runner import control
 base=Path(config['output']);settings=json.loads(Path(config['settings']).read_text())
 if config.get('optional'):raise ValueError('Unexpected optional input')
 from e2e_reader.perception_memo import settings as memo_settings
 memo_settings(settings,required=True)
 items=base/'metadata/q/0.json'
 forward=subset(config['package'],items)
 specs=descriptors();identity=dict(plan=config['plan_sha256'],inputs=config['inputs_sha256'],
   operator_sha256=config['operator_sha256'],cards=1,reads=specs,items_sha256=ids_sha(forward),
   items=EXPECTED,orders=['read 0 order','read 0 order reversed'])
 identity=json.loads(json.dumps(identity));sealed_write(base/'metadata/IDENTITY.json',identity)
 configs={}
 for i,spec in enumerate(specs):
  root=base/'metadata/reads'/str(i)
  chosen={**settings,'stage1_select_rule':spec['stage1_select_rule'],'save_own_depth':False,
          **{k:spec[k] for k in ('perception_memo','perception_memo_verify_ids','perception_memo_modules')}}
  path=root/'metadata/0.json';sealed_write(path,chosen)
  sealed_write(root/'metadata/READ_IDENTITY.json',dict(**identity,read=i,settings_sha256=canonical(chosen)))
  configs[i]={**config,'output':str(root),'settings':str(path),'items':str(items),'q':spec['q'],
      'cache_root':str(base/'cache'/str(i)), 'stop_file':str(base/'metadata/STOP'),
      'single_worker':True,'arms':['tower'],'modes':['none'],'types':[ORDER[t] for t in spec['types']],
      'stage1_select_rule':spec['stage1_select_rule'],
      'stop_margin':1800,'return_margin':1200,**memo_settings(chosen)}
  # The worker entry carries the read's order; runner.control keeps an existing entry.
  a=root/'metadata'/'a';a.mkdir(parents=True,exist_ok=True,mode=0o700);a.chmod(0o700)
  entry=a/'5.py'
  if entry.exists() and entry.read_text()!=WRAPPER:raise ValueError('Worker entry differs')
  entry.write_text(WRAPPER)
  if control(configs[i])!=a or entry.read_text()!=WRAPPER:raise ValueError('Worker entry differs')
 return configs,forward


class Watch(threading.Thread):
 """Write the shared stop marker once a path holds what the check waits for."""
 def __init__(self,path,marker,lines):
  super().__init__(daemon=True);self.path=Path(path);self.marker=Path(marker);self.lines=lines;self.fired=None
 def run(self):
  while self.fired is None:
   try:
    ready=self.path.exists() and (self.lines==0 or sum(l.endswith('\n') for l in self.path.open())>=self.lines)
   except OSError:ready=False
   if ready:
    self.marker.write_text('rehearsal\n');self.fired=time.time();return
   time.sleep(0.5)


def tail(path,n=4096):
 import base64,gzip
 p=Path(path)
 if not p.is_file():return None
 raw=p.read_bytes()
 return dict(bytes=len(raw),gz64=base64.b64encode(gzip.compress(raw[:n]+b'\n...\n'+raw[-n:] if len(raw)>2*n else raw,mtime=0)).decode())


def evidence(cfg):
 out=Path(cfg['output']);found={}
 for p in sorted([out/'STEPS.jsonl',*out.glob('logs/*.log'),*out.glob('metadata/journals/*/0/worker.log'),
                  *out.glob('metadata/journals/*/0/STEPS.jsonl'),*out.glob('metadata/journals/*/0/progress.json')]):
  found[str(p.relative_to(out))]=tail(p)
 return found


def rehearsal(config,end):
 """CPU check: each read through the job's own launcher line on CPU. Read 1 stops before its first
 item once its worker has bound the order; read 0 runs its first item outside CPU_SKIPPED and stops.
 The GPU job never calls this function and keeps every type in both reads."""
 from orchard_h10.runner import worker_args,run as execute
 from orchard_h10.common import ORDER
 # prepare() imports the reader first, as run() does; h1eval would put its own copy on the path.
 configs,forward=prepare(config);result=dict(reads=[],items_sha256=ids_sha(forward))
 from h1eval.items import load_manifest
 items=load_manifest(Path(configs[0]['items']))['items']
 marker=Path(configs[0]['stop_file'])
 for i in (1,0):
  cfg=configs[i]
  if i==0:
   assert cfg['types']==[ORDER[k] for k in SEQUENCES[0]]
   cfg={**cfg,'types':[ORDER[k] for k in SEQUENCES[0] if k not in CPU_SKIPPED]}
  t=ORDER.index(cfg['types'][0])
  args=worker_args(dict(config=cfg,type=t,index=0,cards=1,stop_at=1,finish_by=2))
  assert args[args.index('--arms')+1]=='tower' and args[args.index('--modes')+1]=='none'
  assert args[args.index('--types')+1]==','.join(cfg['types'])
  assert json.loads(Path(args[args.index('--settings')+1]).read_text())['stage1_select_rule']==RULE
  chosen=json.loads(Path(args[args.index('--settings')+1]).read_text())
  assert chosen['perception_memo']=='on' and chosen['perception_memo_verify_ids']==[] and chosen['perception_memo_modules']==['g3t']
  expected=planned(i,items,SEQUENCES[0])
  assert expected==(forward if i==0 else forward[::-1])
  if i==0:
   kinds={r['id']:r['question_type'] for r in items}
   expected=[x for x in expected if kinds[x] in cfg['types']]
   assert expected and expected==forward[-len(expected):]
  first=Path(cfg['output'])/'metadata/journals'/str(t)/'0'
  marker.unlink(missing_ok=True)
  watch=Watch(first/('items.jsonl' if i==0 else 'environment.json'),marker,1 if i==0 else 0);watch.start()
  started=time.time();record=dict(read=i,types=[ORDER.index(k) for k in cfg['types']],args_sha256=ids_sha(args))
  if i==0:record['cpu_skipped_types']=list(CPU_SKIPPED)
  try:
   summary=execute(cfg,[''],end,prefix=cfg['prefix'])
  except BaseException as error:
   watch.fired=watch.fired or -1
   record.update(error=type(error).__name__,evidence=evidence(cfg));print(json.dumps(record),flush=True)
   raise ValueError('E71 read %d launch raised'%i)
  watch.fired=watch.fired or -1
  record.update(seconds=time.time()-started,summary=summary,stopped_by_check=watch.fired)
  env=first/'environment.json'
  bound=json.loads(env.read_text())['binding'] if env.exists() else None
  rows=[json.loads(l) for l in (first/'items.jsonl').open()] if (first/'items.jsonl').exists() else []
  head=[x for x in expected if x in set(bound['ids'])] if bound else None
  record.update(bound_n=len(bound['ids']) if bound else None,bound_sha256=ids_sha(bound['ids']) if bound else None,
                bound_exact=bool(bound) and bound['ids']==expected[:len(bound['ids'])],records=len(rows))
  ok=(summary['failure'] is None and bound is not None and bound['ids']==expected[:len(bound['ids'])]
      and head==bound['ids'] and bound['stage1_select_rule']==RULE and bound['perception_memo']=='on'
      and bound['perception_memo_verify_ids']==[] and bound['perception_memo_modules']==['g3t'])
  if i==1:ok=ok and rows==[]
  else:
   r=rows[0] if len(rows)==1 else None
   ok=ok and r is not None and r['id']==expected[0] and r['complete'] is True and 'text' in r['output'] and 'finish' in r['output']
   if r is not None:
    o=r['output']
    memo=o.get('perception_memo') or {}
    record.update(first=dict(position=forward.index(r['id']),exact=r['id']==expected[0],finish=o['finish'],seconds=r['seconds'],
                  timings=o.get('timings'),scores=o.get('scores'),calls=len(o.get('calls',{}).get('records',[])),
                  memo={k:memo.get(k) for k in ('requested','effective','hits','misses')},steps=(o.get('entries') or {}).get('steps')))
  record['passed']=bool(ok)
  if not ok:record['evidence']=evidence(cfg)
  result['reads'].append(record);print(json.dumps(record),flush=True)
  marker.unlink(missing_ok=True)
  if not ok:raise ValueError('E72 read %d check failed'%i)
 result['passed']=True
 return result


def run(config,end,cards,runner=None,clock=time.time):
 from orchard_h10.runner import run as execute
 from orchard_h10.common import write
 if len(cards)!=1 or not cards[0]:raise ValueError('Require exactly one assigned card')
 configs,forward=prepare(config);results=[];failure=None
 for i in (0,1):
  if clock()>=end-1800 or (Path(config['output'])/'metadata/STOP').exists():break
  cfg=configs[i]
  result=(runner or execute)(cfg,cards,end,prefix=cfg['prefix'])
  results.append(dict(read=i,types=cfg['types'],**result))
  if result['failure'] or not result['complete']:
   failure=result['failure'];break
 reads=[]
 for i in (0,1):
  rows=[r for r in results if r['read']==i]
  completed=sum(r['completed'] for r in rows)
  reads.append(dict(read=i,completed=completed,expected=EXPECTED,complete=completed==EXPECTED))
 summary=dict(completed=sum(r['completed'] for r in reads),expected=2*EXPECTED,
              complete=all(r['complete'] for r in reads),failure=failure,reads=reads,segments=results)
 write(Path(config['output'])/'SUMMARY.json',summary)
 return summary


def memory_bound(*, captures=(58,58), allocation_bytes=200*1024**3):
 # Fixed G3T contract: at most 64 pose rows and 32 anchor grids. Eight bytes
 # per scalar covers both float64 poses and the fresh float32 grid outputs.
 g3t=(64*9+64+32+32*51*51*5+51+2)*8
 per_capture=g3t+1024**2
 runtime_allowance=64*1024**3
 reads=[dict(read=i,captures=n,memo_bytes=n*per_capture,
             memo_plus_transient_bytes=(n+3)*per_capture,
             host_budget_bytes=(n+3)*per_capture+runtime_allowance) for i,n in enumerate(captures)]
 return dict(basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],
             sam_memo_bytes=0,sam_measurement_required=False,g3t_capture_bytes_upper=g3t,
             python_overhead_bytes_per_capture=1024**2,transient_capture_copies=3,
             runtime_allowance_bytes=runtime_allowance,job_host_bytes=allocation_bytes,reads=reads,
             fits=all(r['host_budget_bytes']<=allocation_bytes for r in reads))


def memory_probe(config):
 """Check the retained G3T bound without loading or measuring SAM."""
 from orchard_h10.common import write
 settings=json.loads(Path(config['settings']).read_text())
 if settings['perception_memo_modules']!=['g3t']:raise ValueError('Unsupported operator memo modules')
 result=memory_bound()
 write(Path(config['output'])/'metadata/MEMORY.json',result)
 if not result['fits']:raise ValueError('Perception memo exceeds host memory plan')
 return result


def main():
 cfg=json.loads(Path(sys.argv[1]).read_text());p=Path(cfg['package'])
 sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
 from orchard_h10.common import install_process_guard
 install_process_guard(Path(sys.argv[1]).resolve().parent)
 if cfg.get('rehearsal'):
  from orchard_h10.common import write
  try:
   if cfg['config'].get('measure_memory'):memory_probe(cfg['config'])
   write(Path(cfg['config']['output'])/'REHEARSAL.json',rehearsal(cfg['config'],cfg['end']))
  except BaseException as error:
   # The cause leaves the job encoded; this log lives on the shared filesystem.
   import traceback,base64,gzip
   text=traceback.format_exc().encode()
   print(json.dumps(dict(code='E70',kind=type(error).__name__,gz64=base64.b64encode(gzip.compress(text,mtime=0)).decode())),flush=True)
   raise SystemExit(3)
  return
 import os
 result=run(cfg['config'],cfg['end'],os.environ['CUDA_VISIBLE_DEVICES'].split(','))
 raise SystemExit(1 if result['failure'] else 0)

if __name__=='__main__':main()
