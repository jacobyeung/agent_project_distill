"""Report direction inputs and the census plan; production loader reporting is separate."""
from pathlib import Path
from collections import Counter
import json,sqlite3,sys,hashlib
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
sys.path[:0]=[str(L/'work/tree_r1')]
from student_pilot.p3_provenance import load,pinned,digest
from student_pilot.r1_routing import Filters
from student_pilot.r1_population import family
from student_pilot.r1_training import row_check
from student_pilot.r1_direction_twins import Binding,dimensions
cfg=load(D/'inputs/config.json');dest=D/'DIRECTION_ROWS.json'
if '--plan' not in sys.argv:
    filters=Filters(cfg,cfg['scene_division']);rows=[];counts=Counter();unicode=0
    def consume(row,twin=False):
        if family(row,'vqa')!='direction' or filters.reason(row,'vqa'):return
        row_check(row,'vqa');parts=dimensions(row);counts['|'.join(parts)]+=1
        rows.append(dict(qid=row['qid'],clause=parts[0],difficulty=parts[1],answer=parts[2],twin=twin))
    receipt=load(pinned(cfg['streams']['vqa']));db=sqlite3.connect(pinned(receipt['database']).as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        for raw, in db.execute('SELECT row FROM rows ORDER BY i'):consume(json.loads(raw))
    finally:db.close()
    for row in Binding(cfg).rows():
        consume(row,True)
        unicode+=digest(row)!=hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert len(rows)==55808 and unicode==100
    dest.write_text(json.dumps(dict(rows=rows,input_counts=dict(counts),unicode_digest_differences=unicode),indent=2)+'\n')
    print('PASS direction input audit',len(rows),unicode)
else:
    from student_pilot.r1_mix import plans,validate_binding
    data=load(dest);summary=load(D/'proofs/census/PLAN_RUN.json');binding=summary['binding']
    card,index,allocation=validate_binding(binding)
    offsets=index['cells']['direction'];assert len(offsets)==len(data['rows'])
    owners=dict(zip(offsets,data['rows'],strict=True));draws=Counter({r['qid']:0 for r in data['rows']});answers=Counter()
    stream_counts={s:sum(len(index['cells'][c['type']]) for c in card['cells'] if c['stream']==s) for s in ('pose','vqa','routing','pointing')}
    for plan in plans(binding,stream_counts,1000):
        for stream,batch in plan:
            if stream!='vqa':continue
            for i in batch:
                if i not in owners:continue
                r=owners[i];draws[r['qid']]+=1;answers['|'.join((r['clause'],r['difficulty'],r['answer']))]+=1
    def shares(counts):
        groups=sorted({tuple(k.split('|')[:2]) for k in counts});result=[]
        for clause,difficulty in groups:
            n=sum(counts.get('|'.join((clause,difficulty,s)),0) for s in ('front','back','other'))
            result.append(dict(clause=clause,difficulty=difficulty,total=n,**{
                s:dict(count=counts.get('|'.join((clause,difficulty,s)),0),share=counts.get('|'.join((clause,difficulty,s)),0)/n)
                for s in ('front','back','other')}))
        return result
    result=dict(scope='N census plan over real eligible direction rows in native order; other streams use census virtual offsets. Production loader audit is pending the frame host.',
        eligible=len(draws),draws=sum(draws.values()),draws_per_row=dict(draws),input_shares=shares(data['input_counts']),
        planned_shares=shares(answers),unicode_digest_differences=data['unicode_digest_differences'],binding=binding)
    assert result['draws']==summary['cells']['direction']['draws']
    (D/'DIRECTION_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS direction census-plan draws',result['draws'])
