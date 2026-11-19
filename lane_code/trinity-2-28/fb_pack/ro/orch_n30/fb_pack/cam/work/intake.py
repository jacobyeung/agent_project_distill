from common import *
import time,traceback
seen=start('intake.py')
from student_pilot.r1_persisted import scope
from student_pilot.r2_intake import intake
info=load(ROOT/'out/REBIND.json');R.MAPS.update(info['paths'])
for h,p in R.MAPS.items():pin(p,h)
read_paths=seen
# Execute fbp_route's execute/tree_reads functions unchanged, without its unrelated families or composition stages.
ref=ROOT/'work/intake_reference.py';parsed=ast.parse(ref.read_text())
nodes=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ['tree_reads','execute']]
assert len(nodes)==2
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(ref),'exec'),globals())
e=load(info['envelope']['path']);cov=load(info['coverage']['path'])
first=execute('camera_wording_first2000',info['envelope']['path'])
shards=[];chunk=[]
def shard(part,chunk):
 # fbp_route's shard algorithm, with gzip JSONL (supported by native read_rows) to respect the workspace cap.
 d=ROOT/f'out/shards/{part:03d}';d.mkdir(parents=True,exist_ok=True);rp=d/'rows.jsonl.gz'
 with rp.open('wb') as raw:
  with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as f:
   for line,r in chunk:f.write(line.encode())
 sp=pin(rp);qs={r['qid'] for _,r in chunk}
 cp=write(str((d/'coverage.json').relative_to(ROOT)),dict(rows_sha256=sp['sha256'],exclusions=e['exclusions'],rows={q:cov['rows'][q] for q in qs},source_coverage=info['coverage'],source_population=info['rows']))
 se={k:v for k,v in e.items() if k not in ('inputs','command')}
 se.update(rows=R.staged(sp),scene_coverage=R.staged(cp),count=len(chunk),row_bindings={q:e['row_bindings'][q] for q in qs})
 ep=write(str((d/'envelope.json').relative_to(ROOT)),se)
 check=execute(f'camera_wording_shard{part:03d}',ep['path'])
 print(part,check,flush=True)
 return dict(rows=sp,coverage=cp,envelope=ep,row_count=len(chunk),result=check)
for line,r in R.lines(info['rows']['path']):
 chunk.append((line,r))
 if len(chunk)==2000:shards.append(shard(len(shards),chunk));chunk=[]
if chunk:shards.append(shard(len(shards),chunk))
totals=Counter();reasons=Counter();refusals=[]
for sh in shards:
 result=sh['result'];reasons.update(result.get('reasons',{}))
 for k in ['seen','admitted','refused']:totals[k]+=result.get(k,0)
 rep=load(result['report']['path']);refusals.extend(rep.get('refusals',[]))
assert totals['seen']==5979 and len(refusals)==totals['refused']
assert set(reasons)<= {'excluded:eval_rooms'},reasons
assert set(r['qid'] for r in refusals)==set(r['qid'] for r in info['excluded'])
capture(seen)
write('out/INTAKE.json',dict(first2000=first,shards=shards,aggregate=totals,reasons=reasons,refusals=refusals,paths=R.MAPS,status='PASS_WITH_EVAL_EXCLUSIONS',scope='Unmodified real r2_intake.intake, limit=2000. Full envelope plus three disjoint shards covering every row. No grammar/tree edits, host spoofing, or exclusion bypass.'))
status(3,f'Real native intake saw all {totals["seen"]} rows: {totals["admitted"]} admitted and {totals["refused"]} excluded:eval_rooms. No grammar or other refusal remains. The full envelope also ran with limit=2000.')
