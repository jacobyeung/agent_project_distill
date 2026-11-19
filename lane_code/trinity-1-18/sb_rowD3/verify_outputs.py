"""Independent artifact checks; never interprets empty rows as successful generation."""
import collections as C
import hashlib
import json
from pathlib import Path
import re
import sqlite3
BASE=Path(__file__).resolve().parent
OUT=BASE/'out'
DB=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    counts=json.loads((OUT/'COUNTS.json').read_text());plan=json.loads((OUT/'PLAN.json').read_text())
    checks=json.loads((OUT/'CHECKS.json').read_text());ra=json.loads((OUT/'ROW_AUDIT.json').read_text())
    missing=json.loads((OUT/'MISSING.json').read_text())
    audit={r['qid']:r for r in ra['records']};assert len(audit)==len(ra['records'])==93370
    samples=[json.loads(s) for s in re.findall(r'```json\n(.*?)\n```',(OUT/'READ30.md').read_text(),re.S)]
    samples={r['qid']:r for r in samples};assert len(samples)==30
    exclusions=[json.loads(l) for l in (OUT/'ROOM_EXCLUSIONS.json').read_text().splitlines()]
    e={r['row_key']:r for r in exclusions};assert len(e)==3026
    assert all(set(r)=={'pool','question_type','reason','row_key','scene'} for r in exclusions)
    b=C.Counter();eligible=C.Counter();facing=C.Counter();total=0;sampled=0;names=C.defaultdict(set)
    with sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True) as con:
        for raw, in con.execute('SELECT row FROM rows ORDER BY i'):
            r=json.loads(raw)
            if r.get('question_type','').split('_')[:3]!=['object','rel','direction']:continue
            total+=1
            q=r['student_input']['question'].casefold()
            kind='opposite' if 'opposite' in q else 'away' if 'away from' in q or 'with my back to' in q else 'toward'
            first=r['target'].splitlines()[1]
            opening='Seen' if first.startswith('Seen:') else 'Step 1' if first.startswith('Step 1:') else 'OTHER'
            key=(r['question_type'],r['pool'],r.get('retrace',{}).get('rule','none'),opening,kind)
            b[key]+=1;a=audit[r['qid']]
            assert a['source_row_sha256']==hashlib.sha256(raw.encode()).hexdigest()
            assert (a['opening'],a['clause'])==(opening,kind)
            if 'facing' in r:
                assert r['facing']==('toward' if kind=='toward' else 'away');facing[kind]+=1
            if a['excluded_by']:
                x=e[r['qid']]
                assert x==dict(pool=r['pool'],question_type=r['question_type'],reason='excluded_room:'+','.join(a['excluded_by']),row_key=r['qid'],scene=r['dataset']+'/'+r['scene'])
                assert a['excluded_by']==['K1']
            else:eligible[key]+=1;assert r['qid'] not in e
            if r['qid'] in samples:assert samples[r['qid']]==r;sampled+=1
    def unpack(rows):return {(r['question_type'],r['pool'],r['retrace_rule'],r['opening'],r['clause']):r['rows'] for r in rows}
    assert b==unpack(counts['before'])==unpack(counts['actual_after'])
    assert eligible==unpack(counts['room_eligible'])
    assert sampled==30 and total==93370 and sum(eligible.values())==90344
    for tag,c in [('before_room_rule',b),('after_room_rule',eligible)]:
        binary=C.Counter();literal=C.Counter()
        for k,n in c.items():
            binary[k[-2],k[-1]=='toward']+=n;literal[k[-2:]]+=n
        m=max(binary.values());required=4*m-sum(c.values())
        assert plan[tag]['equal_four_binary_cells']==required
        assert plan[tag]['equal_six_literal_cells']==6*max(literal.values())-sum(c.values())
        conditional=sum(abs(binary[o,True]-binary[o,False]) for o in ('Step 1','Seen'))
        assert plan[tag]['within_each_opening_binary']==conditional
        assert sum(x['required_additions'] for x in plan[tag]['family_quotas'])==required
        assert all(x['actual_additions']==0 for x in plan[tag]['family_quotas'])
    assert plan['after_room_rule']['equal_four_binary_cells']==101004>30000
    for name in ('NEW_ROWS.jsonl','REPLACEMENTS.jsonl','REMOVE.json'):assert (OUT/name).stat().st_size==0
    assert len(missing['sources'])==11 and sum(r['rows'] for r in missing['sources'])==93370
    assert all(not r['inventory_basename_matches'] for r in missing['sources'])
    assert checks['status']=='MISSING' and checks['binding_ready'] is False
    assert checks['exact_cell_counts']['status']=='FAIL_SHORT_CELLS'
    assert checks['independent_GT_recomputation'].startswith('MISSING')
    inputs={str(p):sha(p) for p in [Path(__file__),BASE/'build_rows.py',OUT/'COUNTS.json',OUT/'PLAN.json',OUT/'CHECKS.json',OUT/'ROW_AUDIT.json',OUT/'READ30.md',OUT/'ROOM_EXCLUSIONS.json',OUT/'MISSING.json',DB]}
    assert inputs[str(DB)]==counts['input_sha256'][str(DB)]['sha256']
    result=dict(status='PASS_ARTIFACT_INTEGRITY_ONLY',row_build_status='MISSING',binding_ready=False,
        command='PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py',input_sha256=inputs,
        independently_counted_direction_rows=total,cells=len(b),eligible_rows=sum(eligible.values()),
        excluded_rows=len(e),sampled_source_rows_equal=sampled,facing_field_crosscheck=dict(facing),
        minimum_four_cell_additions=101004,generated_rows=0,exact_cell_counts='FAIL_SHORT_CELLS',
        independent_GT_recomputation='MISSING; the numerical census checks do not certify answers')
    (OUT/'VERIFY.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
if __name__=='__main__':main()
