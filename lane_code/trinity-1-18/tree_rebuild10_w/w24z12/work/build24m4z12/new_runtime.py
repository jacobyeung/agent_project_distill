import sys,os,runpy,subprocess,time,types,http.client,json
from pathlib import Path
W=Path(os.environ['TEST_W']);K=W/'kit';D=Path(__file__).parent
sys.path.insert(0,str(D));from strict_sink import Connection
__import__("strict_sink").install()
sys.path.insert(0,str(K/'b'))
import z
original=z.load
def mapped(p):
 v=original(p)
 if Path(p).name=='p.json':v['n_root']=os.environ['TEST_X']
 return v
z.load=mapped
a=sys.argv[1:]
while a and a[0].startswith('-'):a.pop(0)
script=Path(a[0]);sys.argv=a
original_run=subprocess.run
def run(argv,*args,**kw):
 if isinstance(argv,list) and any(str(K/'b'/v) in argv for v in ('pc.py','o.py','gc.py')):
  i=min(argv.index(str(K/'b'/v)) for v in ('pc.py','o.py','gc.py') if str(K/'b'/v) in argv)
  argv=argv[:i]+[str(D/'new_runtime.py')]+argv[i:]
 return original_run(argv,*args,**kw)
subprocess.run=run
os.environ['STRICT_SINK']=os.environ.get('FAKE_SINK',str(W/'sink'))
if script.name=='pc.py':
 d=runpy.run_path(str(script),run_name='case_pc');g=d['main'].__globals__;old=g['read']
 def read(p):
  v=old(p)
  if Path(p).name=='p.json':v['n_root']=os.environ['TEST_X']
  return v
 g['read']=read
 g['time']=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.003,sleep=lambda s:time.sleep(s*.003))
 g['deadline']=lambda:time.time()+8
 g['ARCHIVE_SECONDS']=9 if os.environ.get('NEW_MODE')=='reserve' else 1
 if '--writer' in a:
  args=a[a.index('--writer')+1:];os.environ['STRICT_SESSIONS']=args[2]
  if os.environ.get('NEW_MODE')=='resume' and '_ck00.' in args[3]:
   flag=W/'partial_started'
   os.environ['STRICT_FAIL']='' if flag.exists() else 'partial';os.environ['STRICT_SELECT']='_ck00.'
   flag.write_text('1')
  raise SystemExit(d['writer_main'](args))
 if '--seconds' in a:print(10)
 elif os.environ.get('NEW_MODE')=='live_probe':
  c=d['Copier'](K,W/'n','41');c.upload_until=time.time()+5
  assert d['priority_settled'](c.train,c.state,c.nominal_stop())
  ledger=c.spool/'private/sess.json.receipts.jsonl'
  ledger_prior=ledger.read_bytes();ledger.rename(ledger.with_suffix('.held'))
  ledger.write_bytes(b'\n'.join(line for line in ledger_prior.splitlines() if b'_ck00.' not in line and b'_ck01.' not in line)+b'\n')
  for step in (10,2):
   done=c.state/('gcs_checkpoint_'+str(step)+'.done');done.rename(done.with_suffix('.held'))
  c.pass_once(final=False,small=False)
  assert all((c.state/('gcs_checkpoint_'+str(step)+'.done')).exists() for step in (10,2))
 else:d['main']()
elif script.name=='gc.py':
 import concurrent.futures
 os.environ['STRICT_SESSIONS']=a[2]
 d=runpy.run_path(str(script),run_name='gc_runtime');d['main'].__globals__['ProcessPoolExecutor']=concurrent.futures.ThreadPoolExecutor
 raise SystemExit(d['main'](a[1:]))
else:runpy.run_path(str(script),run_name='__main__')
