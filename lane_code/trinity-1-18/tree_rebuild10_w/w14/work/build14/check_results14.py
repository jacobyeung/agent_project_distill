from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build14'
def read(path):return json.loads((L/path).read_text())
for name in ('SUITE_COMPARISON.json','CHANGED_COVERAGE.json','GAPS.json'):
    p=B/name
    if p.exists():
        v=json.loads(p.read_text())
        if name=='SUITE_COMPARISON.json':
            print(name,json.dumps({k:x for k,x in v.items() if k in ('run','passed','preexisting','regressions','skipped','r2_failures','fatal')}))
            print('regressions',json.dumps([{k:r[k] for k in ('test','cause')} for r in v['failures'] if not r['preexisting']]))
        elif name=='CHANGED_COVERAGE.json':print(name,json.dumps({'statements':v['changed_statements'],'classes':v['classes']}))
        else:print(name,json.dumps([(r['file'],r['line'],r['text']) for r in v]))
if '--require' in sys.argv:
    c=read('work/build14/SUITE_COMPARISON.json');assert c['r2_failures']==0 and not c['fatal']
    assert all('BF16 cached/online gradient' in r['cause'] for r in c['failures'] if not r['preexisting'])
    assert not read('work/build14/GAPS.json')
    assert read('work/build14/proofs/final_focused/TESTS.json')['successful']
    before=read('work/build13/proofs/census/CENSUS.json');now=read('work/build14/proofs/census/CENSUS.json')
    assert before['vqa']==now['vqa'] and before['slices']==now['slices']
    a=read('work/build13/proofs/census/PLAN_RUN.json');b=read('work/build14/proofs/census/PLAN_RUN.json')
    for key in ('allocation','per_step_quotas','draws','largest_repeat','steps','facing'):assert a[key]==b[key],key
    a=read('work/build13/proofs/census/population/population.json');b=read('work/build14/proofs/census/population/population.json')
    for key in ('counts','asked_units','facing','source_identity_overrides'):assert a[key]==b[key],key
    assert read('work/build14/proofs/preservation/RESULT.json')['keys']==601
    before=read('work/build12/proofs/n1/text/RESULT.json')['families'];now=read('work/build14/proofs/text/RESULT.json')['families']
    assert {k:v['counts'] for k,v in before.items()}=={k:v['counts'] for k,v in now.items()}
    (B/'COUNT_EQUALITY.json').write_text(json.dumps(dict(status='PASS',census='work/build14/proofs/census/CENSUS.json',
        plan='work/build14/proofs/census/PLAN_RUN.json',text='work/build14/proofs/text/RESULT.json',exclusions=601,
        comparisons=['work/build13/proofs/census/CENSUS.json','work/build13/proofs/census/PLAN_RUN.json','work/build12/proofs/n1/text/RESULT.json']),indent=2))
    print('PASS qualification and count equality')
