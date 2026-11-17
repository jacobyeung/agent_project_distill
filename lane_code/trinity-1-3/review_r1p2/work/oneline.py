import sqlite3,json,sys,re
from collections import Counter
sys.path[:0]=['s5/work/tree','s5/work/tree/generator/derivgen_v7']
from student_pilot.type_mix import room_trace
cnt=Counter();ex=[]
for p in ['/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final/a0_room.jsonl','/scratch/jjyeung/orch_n30/rows_a2/out/a2_room_ft2_v1/slice_a2_room_ft2.jsonl']:
    for line in open(p):
        d=json.loads(line);cnt[(p[-20:],'asis',room_trace(d))]+=1
        d['pool']='r1_room_traced';r=room_trace(d);cnt[(p[-20:],'pool_forced',r)]+=1
        if len(ex)<2:ex.append(repr(d.get('target'))[:300])
print(dict(cnt));print(ex)
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1',uri=True)
ids=json.load(open('traced_i.json'));rel=Counter();restate=Counter();nl=Counter()
for i in ids:
    d=json.loads(c.execute('select row from rows where i=?',(i,)).fetchone()[0])
    m=re.fullmatch(r'\s*<think>\s*(.*?)\s*</think>\s*(\S+)\s*',d['target'],re.S);lines=[l.strip() for l in m[1].splitlines() if l.strip()]
    rel[tuple(k for k in ['apart','between','side','left','right','opposite','near','behind','front','across'] if re.search(r'\b'+k+r'\b',lines[-1],re.I))]+=1
    restate[lines[0].startswith('The question asks')]+=1; nl[len(lines)]+=1
print('relation keywords',dict(rel));print('restate',dict(restate));print('nlines',dict(nl))
print(repr(d['target']))
