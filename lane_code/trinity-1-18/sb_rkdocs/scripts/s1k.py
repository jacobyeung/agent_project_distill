"""CPU-only, preregistered kernel selection on exactly 110 K1 train captures."""
from adapter import *
import itertools,time,resource,random
import room_kernel as candidate
from selection import training_set,K1_PRED

OLD=dict(height_margin_m=.10,cell_m=.05,min_votes=2,closing_m=.20)
def main():
 start=time.monotonic();cpu=time.process_time()
 resource.setrlimit(resource.RLIMIT_AS,(39<<30,39<<30))
 rows,caps,ins=training_set();ins.update(input_code())
 ins[str(W/'vendor/room_kernel.py')]=sha(W/'vendor/room_kernel.py')
 stats=W/'evidence/k1_rule_variants.py';ins[str(stats)]=sha(stats)
 nodes=[n for n in ast.parse(stats.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='mra']
 ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(stats),'exec'),ns)
 grid=[dict(zip(OLD,values)) for values in itertools.product([.05,.10],[.05,.10],[1,2],[.10,.20])]
 registration=dict(stage='S1k',selection_scope='K1 train only',captures=[r['capture'] for r in rows],grid=grid,
  objective='maximum arithmetic mean per-row K1-train MRA; refusal=0; area rounded to 0.01 m2 by kit formatter/parser',
  tie_break='first candidate in listed grid order',old_values=OLD,threads=8,max_cpu_seconds=7200,
  command='bash scripts/cpu.sh scripts/s1k.py',authorized_by='pending orchestrator')
 reg=W/'out/S1K_REGISTRATION.json'
 if reg.exists():raise RuntimeError('S1k registration exists; do not change or rerun selection')
 write(reg,registration,ins);ins[str(reg)]=sha(reg)
 status('S1k is preregistered on exactly 110 K1 training captures, with 16 fixed candidates. Stored predictions supply all geometry; no tower forward or benchmark score is used.')
 results=[dict(constants=g,rows=[]) for g in grid]
 for index,r in enumerate(rows):
  c=caps[r['capture']];p=K1_PRED/digest(c)[:16]/'pred.npz';done=p.parent/'DONE.json'
  if not p.is_file() or not done.is_file():raise FileNotFoundError('MISSING '+str(p))
  ins[str(p)]=sha(p);ins[str(done)]=sha(done)
  if read(done)['pred_sha256']!=ins[str(p)]:raise ValueError('prediction hash mismatch')
  a=arrays(p)
  assert a['frame_indices'].tolist()==[int(f['index']) for f in c['dense_frames']]
  assert a['frame_indices'][a['item_slots'].astype(int)].tolist()==c['anchor_indices']
  try:sample=room.sample(convert(p,W/'out/s1k_geom.npz'),'predicted');refusal=None
  except ValueError as e:
   if str(e)!='reference_camera_up_opposes_gravity':raise
   sample=None;refusal=str(e)
  for result in results:
   candidate.configure(result['constants']);area=None;why=refusal
   if sample is not None:
    try:area=candidate.parse_response(candidate.format_result(candidate.from_points(**sample)))['area_m2']
    except (ValueError,KeyError,FloatingPointError,np.linalg.LinAlgError) as e:why=getattr(e,'code',str(e))
   if result['constants']==OLD:assert area==r['R0'],(r['capture'],area,r['R0'])
   result['rows'].append(dict(row_id=r['row_id'],capture=r['capture'],room=r['room'],split='train',gt=r['gt'],area_m2=area,refusal=why,mra=100*ns['mra'](area,r['gt'])))
  elapsed=time.process_time()-cpu
  print(index+1,r['capture'],'cpu_seconds',round(elapsed,2),flush=True)
  if index==0:
   estimate=elapsed*110
   write(W/'out/S1K_ESTIMATE.json',dict(estimated_cpu_seconds=estimate,measured_first_capture_cpu_seconds=elapsed,within_two_cpu_hours=estimate<=7200,threads=8),ins)
   if estimate>7200:
    status('S1k is scripted and preregistered; its first-capture timing exceeds the two CPU-hour allowance. No winner is frozen. See out/S1K_ESTIMATE.json.')
    return
  if elapsed>7000:raise RuntimeError('S1k CPU budget nearly exhausted; no winner frozen')
 for result in results:result.update(mra=sum(r['mra'] for r in result['rows'])/len(rows),n=len(rows))
 winner=max(range(len(results)),key=lambda i:results[i]['mra'])
 write(W/'out/S1K_RESULTS.json',dict(status='COMPLETE',grid=grid,result_table=results,winner_index=winner,winner=grid[winner],cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-start,command=registration['command']),ins)
 freeze=W/'configs/KERNEL_FROZEN.json'
 write(freeze,dict(status='FROZEN',selection_scope='K1 train only',benchmark_selected=False,constants=grid[winner],kernel_sha256=sha(W/'vendor/room_kernel.py'),authorized_by='pending orchestrator'),{str(W/'out/S1K_RESULTS.json'):sha(W/'out/S1K_RESULTS.json'),str(reg):sha(reg),str(W/'vendor/room_kernel.py'):sha(W/'vendor/room_kernel.py')})
 status('S1k completed on 110 K1 training captures. The winning constants are frozen in configs/KERNEL_FROZEN.json. Kernel authorization remains pending orchestrator; no GPU or R0-dev pricing has run.')
 print('WINNER',grid[winner],results[winner]['mra'],flush=True)
if __name__=='__main__':main()
