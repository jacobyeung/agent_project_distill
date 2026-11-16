import json, tarfile, io, sys, hashlib, os
B='/scratch/jjyeung/orch_n30/native_r2'
W=B+'/work'
small=[W+'/full_c8r/x/native/paired/IN_JOB_ADMISSION.json', W+'/full_c8r/x/native/R1.json.pin.json',
 W+'/parent/r5/merge_results/B2048.json', W+'/parent/r5/merge_results/B2048_kit_summary.json',
 W+'/parent/r5/merge_results/MERGE_INPUTS.json', W+'/parent/r5/merge_results/MERGE_COMPLETE.json',
 W+'/parent/r5/SCORING_DEV.md', W+'/parent/r5/dev_scoring.py', W+'/parent/r3/TASKS.jsonl', W+'/parent/r3/FRAMES.json',
 W+'/parent/r3/STRATA.jsonl', W+'/parent/r3/RUNCARD.md', W+'/direct/DIRECT_B2048_COMPACT.json',
 B+'/builds/05_analysis_fix/in/direct_raw/items_leg_m544_main.jsonl',
 B+'/builds/06_parent_adapter/out/items_parent_main.jsonl']
r1=json.load(open(W+'/full_c8r/x/native/R1.json'))
def trunc(x):
    if isinstance(x,str): return x if len(x)<=6000 else x[:6000]+'...<TRUNC %d>'%len(x)
    if isinstance(x,list): return [trunc(v) for v in x]
    if isinstance(x,dict): return {k:trunc(v) for k,v in x.items()}
    return x
out={'top_keys':list(r1.keys()), 'top_scalars':{k:v for k,v in r1.items() if not isinstance(v,(list,dict))}}
out['nonarm']={k:trunc(v) for k,v in r1.items() if k not in('arms',) and isinstance(v,(dict,list)) and len(json.dumps(v))<200000}
arms={}
for a,rows in r1['arms'].items():
    arms[a]=[trunc(r) for r in rows if r.get('question_type') in ('object_abs_distance','room_size_estimation','absolute_distance_object','absolute_size_room')]
    out.setdefault('arm_counts',{})[a]=len(rows)
out['arms']=arms
data=json.dumps(out).encode()
buf=tarfile.open(fileobj=sys.stdout.buffer,mode='w|')
ti=tarfile.TarInfo('R1_distroom.json'); ti.size=len(data); buf.addfile(ti,io.BytesIO(data))
tot=len(data)
for f in small:
    if os.path.isfile(f):
        tot+=os.path.getsize(f)
        if tot>19_000_000: print('CAP',f,file=sys.stderr); break
        buf.add(f,arcname=f.lstrip('/'))
    else: print('MISSING',f,file=sys.stderr)
buf.close(); print('total',tot,file=sys.stderr)
