from pathlib import Path
import hashlib,json,math,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths2 import D,R
def read(p,default=None):
    return json.loads(p.read_text()) if p.exists() else default
stages=read(R/'STAGES.json',[])
refusal=read(R/'RUN_REFUSAL.json',{})
furthest=stages[-1]['stage'] if stages else refusal.get('error','NOT RUN')
probe=read(R/'PROBE_RESULT.json',{})
if probe:furthest=probe['furthest']+'; retained bytes='+str(probe['bytes_after_stop'])
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
native=read(R/'p2/q/RESULT.json',{}).get('host_receipt',{})
host=R/'p2/q/host.json'
emit('native host receipt',host.is_file() and native.get('sha256')==hashlib.sha256(host.read_bytes()).hexdigest() and read(R/'gates.json',{}).get('host_written_by')=='launch_r1.production_proof','p2/q/RESULT.json.host_receipt')
emit('handover passes with localised pins',read(R/'p2/q/RESULT.json',{}).get('status')=='ADMIT' and 'persisted_handover' in read(R/'p2/q/RESULT.json',{}).get('steps',[]) and read(R/'AUTH_fresh.json',{}).get('native_admit') is True,'native q persisted_handover and AUTH_fresh.json')
emit('clock inheritance',batch is not None and all(v.get('TK_JOB_START')==batch for v in fresh),furthest)
emit('fresh optimizer / counter zero',all(v.get('start_step')==0 and v.get('optimizer_state_entries_at_start')==0 for v in fresh),furthest)
finite=lambda values:all(v.get('events') and all(all(math.isfinite(x) for x in e['info']['stream_means'].values()) for e in v['events']) for v in values)
emit('finite losses on four ranks',finite(fresh) and finite(budget) and finite(resume),furthest)
emit('step-1 checkpoint through milestone',any(v['kind']=='checkpoint' and v['step']==1 and v['passed'] for v in states),furthest)
emit('timed checkpoint',any(v['kind']=='checkpoint' and v['step']==2 and v['passed'] for v in states),furthest)
done=R/'target/o/rehearsal/live/gcs_m2.done'
marker=R/'p2/q/r/m2/artifact.json'
local=False
source=read(R/'COPIER_SOURCE.json',{});prepared=read(R/'PREPARED.json',{})
shipped=bool(prepared.get('kit')) and source.get('kit_seal')==prepared.get('kit') and source.get('kit')==prepared.get('kit_dir') and source.get('directory_mode')=='0700' and source.get('file_mode')=='0600'
if shipped:
    shipped=hashlib.sha256(Path(source['module']).read_bytes()).hexdigest()==source['module_sha256']
if marker.exists():
    digest=hashlib.sha256(marker.read_bytes()).hexdigest()
    receipt=read(R/'p2/q/r/persist'/(digest+'.local.json'),{})
    sent=read(done,{})
    local=(receipt.get('source',{}).get('sha256')==digest
           and receipt.get('durable') is False and receipt.get('parts')==[]
           and sent.get('marker_sha256')==digest
           and sent.get('sha256')==receipt.get('archive',{}).get('sha256')
           and sent.get('bytes',0)>0)
    if local:
        objects=R/'target/n_s/objects'
        pieces=[objects/(sent['object']+f'.part{i:02d}-of-04').replace('/','_') for i in range(4)]
        if not all(p.is_file() for p in pieces): local=False
        else:
            joined=hashlib.sha256();size=0
            for part in pieces:
                with part.open('rb') as stream:
                    for block in iter(lambda:stream.read(1<<20),b''): joined.update(block);size+=len(block)
            local=joined.hexdigest()==sent['sha256'] and size==sent['bytes']
emit('milestone export / local receipt / kit copier',any(v['kind']=='export' and v['step']==2 for v in states) and local and shipped,str(done) if done.exists() else furthest)
emit('TK_JOB_START budget self-stop',all(v.get('last_step')==4 and v.get('stop_reason')=='budget_or_signal' and v.get('elapsed_seconds',0)>=89900 for v in budget) and {v['kind'] for v in bstates if v['step']==4}=={'checkpoint','export'},furthest)
emit('resume_pin latest / one further step',all(v.get('resume_pin')=='latest' and v.get('start_step')==4 and v.get('last_step')==5 and v.get('optimizer_state_entries_at_start',0)>0 for v in resume),furthest)
if R.exists():(R/'CHECK.json').write_text(json.dumps(rows,indent=2)+'\n')
raise SystemExit(0 if all(v['passed'] for v in rows) else 1)
