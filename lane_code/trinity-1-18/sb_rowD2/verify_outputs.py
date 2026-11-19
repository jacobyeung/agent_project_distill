"""Check the census/removal artifacts independently of the generator counters.

This checks artifact integrity, not missing geometry or nonexistent generated rows.
"""
from collections import Counter
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
    checks=json.loads((OUT/'CHECKS.json').read_text())
    counts=json.loads((OUT/'COUNTS.json').read_text())
    plan=json.loads((OUT/'TWIN_PLAN.json').read_text())
    refused={}
    for line in (OUT/'REFUSED.jsonl').open():
        r=json.loads(line)
        assert r['qid'] not in refused
        refused[r['qid']]=r
    removals=[json.loads(l) for l in (OUT/'REMOVE.json').read_text().splitlines()]
    expected_keys={'pool','question_type','reason','row_key','scene'}
    assert all(set(r)==expected_keys for r in removals)
    assert len({r['row_key'] for r in removals})==len(removals)
    samples=[json.loads(s) for s in re.findall(r'```json\n(.*?)\n```',(OUT/'READ30.md').read_text(),re.S)]
    assert len(samples)==30
    samples_by_qid={r['qid']:r for r in samples}
    cells=Counter(); clauses=Counter(); seen=0; sampled=0; frame_cites=Counter(); flagged=Counter()
    expected_removals={}
    with sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True) as c:
        for raw, in c.execute('SELECT row FROM rows ORDER BY i'):
            r=json.loads(raw)
            if r.get('question_type','').split('_')[:3]!=['object','rel','direction']:continue
            seen+=1
            q=r['student_input']['question'].casefold()
            kind='opposite' if 'opposite' in q else 'away' if ('away from' in q or 'with my back to' in q) else 'toward'
            first=r['target'].splitlines()[1]
            opening='Seen' if first.startswith('Seen:') else 'Step 1' if first.startswith('Step 1:') else 'OTHER'
            cells[(r['question_type'],r['pool'],r.get('retrace',{}).get('rule','none'),opening,kind)]+=1
            clauses[kind]+=1
            rr=refused[r['qid']]
            assert rr['source_row_sha256']==hashlib.sha256(raw.encode()).hexdigest()
            assert rr['opening']==opening and rr['clause']==kind
            assert rr['input_sha256'][str(DB)]==checks['input_sha256'][str(DB)]['sha256']
            if 'facing' in r:
                assert r['facing']==('away' if kind=='opposite' else kind)
                flagged[kind]+=1
            if rr['excluded_by']:
                expected_removals[r['qid']]=dict(pool=r['pool'],question_type=r['question_type'],
                    reason='excluded_room:'+','.join(rr['excluded_by']),row_key=r['qid'],scene=r['dataset']+'/'+r['scene'])
            if r['qid'] in samples_by_qid:
                assert r==samples_by_qid[r['qid']]
                sampled+=1
            cites=re.findall(r'\bframe\s+(\d+)\b',first)
            assert all(1<=int(x)<=32 for x in cites)
            frame_cites[(opening,'frames' if cites else 'no_frames')]+=1
    assert seen==len(refused)==counts['direction_rows']==93370
    assert sampled==30
    expected_counts={(r['question_type'],r['pool'],r['retrace_rule'],r['opening'],r['clause']):r['rows'] for r in counts['cells']}
    assert cells==expected_counts
    assert clauses==counts['clauses']
    assert {r['row_key']:r for r in removals}==expected_removals
    assert (OUT/'REPLACEMENTS.jsonl').stat().st_size==(OUT/'TWINS.jsonl').stat().st_size==0
    assert len(plan['quota_cells'])==24 and sum(c['required'] for c in plan['quota_cells'])==24936
    quota=Counter()
    for c in plan['quota_cells']:
        assert c['actual']==0 and c['status']=='MISSING'
        quota[(c['question_type'],c['clause'])]+=c['required']
    for level in ('easy','medium','hard'):
        values=[c['required'] for c in plan['quota_cells'] if c['question_type'].endswith(level)]
        assert len(values)==8 and len(set(values))==1
    assert checks['status']=='MISSING' and checks['binding_ready'] is False
    assert checks['exact_cell_counts']['status']=='FAIL_SHORT_CELLS'
    dependencies=[Path(__file__),OUT/'CHECKS.json',OUT/'COUNTS.json',OUT/'REFUSED.jsonl',OUT/'REMOVE.json',
        OUT/'READ30.md',OUT/'TWIN_PLAN.json',DB]
    pins={str(p):sha(p) for p in dependencies}
    result=dict(status='PASS_ARTIFACT_INTEGRITY_ONLY',row_build_status='MISSING',
        command='PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py',input_sha256=pins,
        source_rows=seen,counts_cells=len(cells),clauses=dict(clauses),facing_field_crosscheck=dict(flagged),
        removal_records=len(removals),source_samples_byte_content_equal=sampled,
        generated_rows=0,short_twin_cells=24,GT_recomputation='MISSING',
        explanation='Census, refusal identities, exact removal schema, sampled source content and quota arithmetic agree. This is not new-row acceptance.')
    (OUT/'VERIFY.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))


if __name__=='__main__':main()
