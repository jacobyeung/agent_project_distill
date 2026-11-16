"""Extract only object names from source naming sentences; never copy answers into scripts."""
import gzip,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'out'))
from common import *
install_tree()
from student_pilot.scripted_calls import validate_reference

tasks={r['id']:r for r in rows(VENDOR/'r3/TASKS.jsonl')}
supported={'object_abs_distance','object_rel_distance','object_rel_direction_medium','object_rel_direction_hard'}
refs={}; failures={}; source=Path('/scratch/jjyeung/orch_cd/dose_pool/out/pool_v0/ROWS_ALL.jsonl.gz')
with gzip.open(source,'rt') as f:
    for line in f:
        r=json.loads(line);qid=r.get('qid')
        if qid not in tasks or tasks[qid]['question_type'] not in supported: continue
        t=tasks[qid];typ=t['question_type'];trace=r['target']
        try:
            if r['student_input']['question']!=t['question'] or r['student_input']['options']!=t['options']: raise ValueError('Source prompt differs')
            if typ=='object_abs_distance':
                names=list(re.search(r'Step 1: find the (.+?) and the (.+?)\.\n',trace).groups());boxed=True
            elif typ=='object_rel_distance':
                names=[re.search(r'Step 1: find the (.+?) and each candidate\.\n',trace)[1]]
                names += [re.sub(r'^[A-Z][.)]\s*','',s) for s in t['options']];boxed=True
            else:
                names=list(re.search(r'Step 1: locate the centres of the (.+?), the (.+?) and the (.+?)\.\n',trace).groups());boxed=False
            for name in names:
                if name.lower() not in (' '.join([t['question'],*t['options']])).lower(): raise ValueError('Operand not in prompt')
            calls=[f'<ground obj="{name}"'+(' mode="box"' if boxed else '')+'>' for name in names]
            if boxed: calls.append('<gap a="'+names[0]+'"'+''.join(' b="'+n+'"' for n in names[1:])+' rule="sampled_box_512">')
            else: calls.append('<angle S=P1 F=P2 Q=P3 rule='+typ.rsplit('_',1)[1]+'>')
            ref=dict(schema='scripted-calls-v1',free_answer=True,segments=[dict(call=c,text=('<think>\n' if i==0 else '\n')+c) for i,c in enumerate(calls)])
            validate_reference(ref)
            refs['devrows:'+qid]=ref
        except (ValueError,AttributeError,TypeError) as exc:failures[qid]=str(exc)
dump(ROOT/'out/SCRIPTED_REFERENCES.json',refs)
dump(ROOT/'out/SCRIPTED_COVERAGE.json',dict(items=len(refs),types=sorted(supported),failures=failures,
    source=pin(source),unsupported=[dict(key='devrows:'+t['id'],type=t['question_type']) for t in tasks.values() if 'devrows:'+t['id'] not in refs],
    policy='Only naming sentence operands enter references; all responses and final answers come from the live runtime/model.'))
print(len(refs),'references;',len(failures),'parse failures')
