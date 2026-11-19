from pathlib import Path
import hashlib,json,math,sys
D=Path(__file__).resolve().parent;R=D/'rehearsal2'
def read(p,default=None):
    return json.loads(p.read_text()) if p.exists() else default
stages=read(R/'STAGES.json',[])
furthest=stages[-1]['stage'] if stages else 'NOT RUN (requires external localhost TCP)'
rows=[]
def emit(name,passed,detail):
    rows.append(dict(path=name,passed=bool(passed),furthest=detail))
    print(name+': '+('PASS' if passed else 'NOT PROVED')+' — '+detail)
tied=read(R/'repro_tied.json',[]);untied=read(R/'repro_untied.json',[])
reproduced=(len(tied)==len(untied)==4
    and {v.get('rank') for v in tied}=={0,1,2,3}
    and {v.get('rank') for v in untied}=={0,1,2,3}
    and all(v.get('error') and any(len(s)==1 for s in v.get('head_shapes',[])) for v in tied)
    and all(v.get('error') is None and v.get('finite') and v.get('backward_finite') and [248064,4] in v.get('head_shapes',[]) for v in untied))
emit('embedding ownership / native FSDP reproduction',reproduced,'repro_tied.json and repro_untied.json' if reproduced else 'Awaiting external four-rank reproduction')
fresh=[read(R/f'fresh_rank{i}.json',{}) for i in range(4)]
budget=[read(R/f'budget_rank{i}.json',{}) for i in range(4)]
resume=[read(R/f'resume_rank{i}.json',{}) for i in range(4)]
states=read(R/'states_fresh.json',[]);bstates=read(R/'states_budget.json',[])
batch=next((v.get('TK_JOB_START') for v in stages if v['stage']=='train_fresh'),None)
emit('clock inheritance',batch is not None and all(v.get('TK_JOB_START')==batch for v in fresh),furthest)
emit('fresh optimizer / counter zero',all(v.get('start_step')==0 and v.get('optimizer_state_entries_at_start')==0 for v in fresh),furthest)
finite=lambda values:all(v.get('events') and all(all(math.isfinite(x) for x in e['info']['stream_means'].values()) for e in v['events']) for v in values)
emit('finite losses on four ranks',finite(fresh) and finite(budget) and finite(resume),furthest)
emit('step-1 checkpoint through milestone',any(v['kind']=='checkpoint' and v['step']==1 and v['passed'] for v in states),furthest)
emit('timed checkpoint',any(v['kind']=='checkpoint' and v['step']==2 and v['passed'] for v in states),furthest)
done=R/'target/o/rehearsal/live/gcs_m2.done'
marker=R/'train/m2/artifact.json'
local=False
if marker.exists():
    digest=hashlib.sha256(marker.read_bytes()).hexdigest()
    receipt=read(R/'train/persist'/(digest+'.local.json'),{})
    sent=read(done,{})
    local=(receipt.get('source',{}).get('sha256')==digest
           and receipt.get('durable') is False and receipt.get('parts')==[]
           and sent.get('marker_sha256')==digest
           and sent.get('sha256')==receipt.get('archive',{}).get('sha256')
           and sent.get('bytes',0)>0)
emit('milestone export / local receipt / kit copier',any(v['kind']=='export' and v['step']==2 for v in states) and local,str(done) if done.exists() else furthest)
emit('TK_JOB_START budget self-stop',all(v.get('last_step')==4 and v.get('stop_reason')=='budget_or_signal' and v.get('elapsed_seconds',0)>=89900 for v in budget) and {v['kind'] for v in bstates if v['step']==4}=={'checkpoint','export'},furthest)
emit('resume_pin latest / one further step',all(v.get('start_step')==4 and v.get('last_step')==5 and v.get('optimizer_state_entries_at_start',0)>0 for v in resume),furthest)
if R.exists():(R/'CHECK.json').write_text(json.dumps(rows,indent=2)+'\n')
raise SystemExit(0 if all(v['passed'] for v in rows) else 1)
