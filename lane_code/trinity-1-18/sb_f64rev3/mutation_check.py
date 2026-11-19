"""Synthetic gate controls derived from the reviewer's retained audit schema; no production claims."""
import copy, hashlib, json, os, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parent
KIT=ROOT.parent/'sb_f64fix2/kit'; CFG=KIT/'configs/r1_config_f64.json'
sys.path[:0]=[str(KIT/'scripts'),os.environ['F64_TREE']]
import token_audit as T
import mem_pilot as P
inputs={}
def pin(p):
    p=Path(p); inputs[str(p)]=T.file_sha256(p)
    return p
for p in (Path(__file__),ROOT/'run_cpu.sh',CFG,KIT/'scripts/token_audit.py',KIT/'scripts/mem_pilot.py',
          Path(os.environ['F64_TREE'])/'student_pilot/carrier_c1_run.py'):
    pin(p)
fixture=pin(ROOT.parent/'sb_f64rev2/tmp/dryrun/token_audit_8m70opiy/complete_0.jsonl')
lines=[json.loads(s) for s in fixture.read_text().splitlines()]
base=next(r for r in lines[1:-1] if r['stream']=='pose')
identity=lines[0]['identity']
cases={}
for name,n,bad,trip in [('passing',300,None,False),('tripwire',300,None,True),
                       ('failed_beyond_longest',301,'failed',False),
                       ('failed_beyond_flagged',301,'failed',True),
                       ('failed_maximum',301,'maximum',False),
                       ('ceiling_flag_only',300,'ceiling',False)]:
    folder=ROOT/'tmp'/name;folder.mkdir(exist_ok=False)
    rows=[dict(base,index=i,tokens=9300,check_row='ok',over_ceiling=False,over_tripwire=trip) for i in range(n)]
    if bad in ('failed','maximum'):
        rows[-1].update(check_row='ValueError: explicit synthetic failure',tokens=9400 if bad=='maximum' else 9000,over_tripwire=False)
    if bad=='ceiling': rows[-1]['over_ceiling']=True
    items=[((r['stream'],r['index']),(r['first_step'],r['rank'])) for r in rows]
    ident=copy.deepcopy(identity)
    ident['shards']=1;ident['plan']=dict(rows=n,sha256=T.digest(T.keys(items)))
    ident['limits']['tripwire_tokens']=9200 if trip else 16000
    shard=folder/'audit.jsonl'
    T.write_shard(shard,ident,0,items,lambda part,sink:[sink(r) for r in rows])
    summary=T.summarize([str(shard)],T.file_sha256(CFG))
    assert not summary['errors'],summary['errors']
    summary['input_sha256']={str(shard):T.file_sha256(shard),str(CFG):T.file_sha256(CFG),str(KIT/'scripts/token_audit.py'):T.file_sha256(KIT/'scripts/token_audit.py')}
    path=folder/'summary.json';path.write_text(json.dumps(summary,indent=2)+'\n')
    cases[name]=dict(path=str(path),expected_accept=bad is None,summary=summary)
    pin(shard);pin(path)
def outcomes(module):
    result={}
    for name,c in cases.items():
        try: module.check_audit(c['path'],CFG); accepted=True;error=None
        except ValueError as exc: accepted=False;error=str(exc)
        result[name]=dict(accepted=accepted,expected_accept=c['expected_accept'],met=accepted==c['expected_accept'],error=error)
    return result
baseline=outcomes(P);assert all(v['met'] for v in baseline.values())
source=(KIT/'scripts/mem_pilot.py').read_text()
mutations={
    'drop_failed_count':("entry['failed'] or entry['over_ceiling']", "entry['over_ceiling']"),
    'drop_ceiling_count':("entry['failed'] or entry['over_ceiling']", "entry['failed']"),
    'reject_tripwire':("if entry['failed'] or", "if entry['over_tripwire'] or entry['failed'] or"),
    'disable_refusal':('if refused:', 'if False and refused:'),
    'trust_cached_counts':("for stream, entry in sorted(again['streams'].items()):", "for stream, entry in sorted(summary['streams'].items()):"),
}
# A cached summary may lie about counts; the gate must use counts re-derived from shards.
c=cases['failed_beyond_longest'];s=copy.deepcopy(c['summary']);s['streams']['pose']['failed']=0
q=Path(c['path']).with_name('forged_cached_counts.json');q.write_text(json.dumps(s,indent=2)+'\n');pin(q)
cases['forged_cached_counts']=dict(path=str(q),expected_accept=False,summary=s)
baseline=outcomes(P);assert all(v['met'] for v in baseline.values())
results={}
for name,(old,new) in mutations.items():
    assert source.count(old)==1,(name,source.count(old))
    altered=source.replace(old,new)
    path=ROOT/'tmp'/f'{name}.py';path.write_text(altered);pin(path)
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(altered,str(path),'exec'),module.__dict__)
    actual=outcomes(module);kills=[k for k,v in actual.items() if not v['met']]
    results[name]=dict(replacement=dict(old=old,new=new),killed=bool(kills),killing_cases=kills,outcomes=actual)
assert all(v['killed'] for v in results.values())
# The auditor and real check_row share the ceiling; exercise every supported stream before any other check.
import torch
torch.set_num_threads(8)
from student_pilot.carrier_c1_run import MAX_TOKENS
class Rows:
    def __init__(self,n):self.n=n
    def get(self,stream,index):return dict(input_ids=torch.zeros((1,self.n),dtype=torch.long)),None,{}
reachability=[]
for recipe in ({},{'max_row_tokens':9000}):
    limit=recipe.get('max_row_tokens',MAX_TOKENS)
    for stream in ('pose','vqa','routing','pointing'):
        records=[]
        T.audit(Rows(limit+1),recipe,{},[((stream,0),(0,0))],records.append)
        row=records[0]
        assert row['over_ceiling'] and row['check_row']!='ok',row
        reachability.append(dict(recipe=recipe,record=row))
result=dict(command='bash run_cpu.sh mutation_check.py',scope=__doc__,input_sha256=inputs,
            controls={name:dict(rows=c['summary']['coverage']['audited'],longest=len(c['summary']['longest']['pose']),
                               flagged=len(c['summary']['flagged']),failed=c['summary']['streams']['pose']['failed'],
                               maximum=c['summary']['streams']['pose']['max_tokens']) for name,c in cases.items()},
            baseline=baseline,mutations=results,mutants=len(results),kills=sum(v['killed'] for v in results.values()),
            ceiling_reachability=reachability)
(ROOT/'out/mutation_review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(baseline=baseline,kills={k:v['killing_cases'] for k,v in results.items()},real_audit_ceiling_cases=len(reachability)),indent=2))
