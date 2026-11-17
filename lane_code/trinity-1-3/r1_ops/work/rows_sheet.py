import sqlite3, json, random, collections, sys
SEED=20261117
db='/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
c=sqlite3.connect('file:%s?immutable=1'%db,uri=True)
groups=collections.defaultdict(list)
for i,row in c.execute("select i,row from rows"):
    d=json.loads(row); t=d.get('question_type'); q=str(d.get('qid',''))
    key=t
    if q.endswith('_away_opp'): key=t+' [away_opp, ReVSI wording]'
    if d.get('pool')=='r1_room_traced': key=t+' [traced room]'
    groups[key].append(i)
rng=random.Random(SEED)
out=['# PRELAUNCH_ROWS_R1, VQA part (store v7 rows.sqlite sha256 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443; byte-equal to Orchard okh7/s_22b44165/d.db)',
 'Five rows per question type, drawn with random.Random(%d).sample over each type\'s row ids in the store; full target text. object_size_estimation is in the store but its cell is 0 (SIZE-V): no size row is drawn. Routing families come from the proof\'s loader audit on Orchard (separate section).'%SEED,'']
for key in sorted(groups):
    ids=sorted(groups[key]); pick=sorted(rng.sample(ids,min(5,len(ids))))
    out.append('## %s (%d rows in store)'%(key,len(ids)))
    for i in pick:
        d=json.loads(c.execute("select row from rows where i=?",(i,)).fetchone()[0]); si=d['student_input']
        out.append('### i=%d qid=%s dataset=%s'%(i,d.get('qid'),d.get('dataset')))
        out.append('Q: '+str(si.get('question')).replace('\n',' '))
        if si.get('options'): out.append('Options: '+str(si.get('options')))
        out.append('Answer field: '+str(d.get('answer')))
        out.append('```\n'+str(d.get('target'))+'\n```')
    out.append('')
open('PRELAUNCH_ROWS_R1_vqa.md','w').write('\n'.join(out)+'\n')
print(len(groups), sum(len(v) for v in groups.values()))
