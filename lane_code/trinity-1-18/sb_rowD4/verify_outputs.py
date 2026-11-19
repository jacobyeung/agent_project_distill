"""Independently recount the gate using original source rows and explicit label permutations."""
import collections
import hashlib
import json
from pathlib import Path
import sqlite3
BASE=Path(__file__).resolve().parent
OUT=BASE/'out'
DB=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    gate=json.loads((OUT/'TRANSFORMATION_CHECK.json').read_text())
    expected_ids={x[k] for x in gate['comparisons'] for k in ('toward_i','turn_i')}
    rows={}
    con=sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    for i,raw in con.execute('SELECT i,row FROM rows WHERE i>=? ORDER BY i',(min(expected_ids),)):
        if i in expected_ids:rows[i]=json.loads(raw)
    con.close()
    perm={'left':'right','right':'left','front-left':'back-right','front-right':'back-left','back-left':'front-right','back-right':'front-left','back':'front','front':'back'}
    fail=0;trans=collections.Counter();pairs=0
    for x in gate['comparisons']:
        t,a=rows[x['toward_i']],rows[x['turn_i']]
        assert t['qid']==x['toward_qid'] and a['qid']==x['turn_qid']
        assert (t['dataset'],t['scene'],t['pair_id'],t['question_type'])==(a['dataset'],a['scene'],a['pair_id'],a['question_type'])
        assert t['target'].splitlines()[1]==a['target'].splitlines()[1]
        assert t['student_input']['frames']==a['student_input']['frames']
        labels=[]
        for r in (t,a):
            opt=next(o for o in r['student_input']['options'] if o.startswith(r['answer']+'. '))
            labels.append(opt[3:])
        passed=perm[labels[0]]==labels[1]
        assert passed==x['pass_exact']
        fail+=not passed;pairs+=1
        trans[t['question_type'],labels[0],labels[1]]+=1
    assert pairs==gate['pairs'] and fail==gate['failed']
    assert (OUT/'NEW_ROWS.jsonl').stat().st_size==0 and (OUT/'SOURCE_MAP.jsonl').stat().st_size==0
    counts=json.loads((OUT/'COUNTS.json').read_text());assert counts['before']==counts['after']
    # Check that every pinned local input still matches its recorded hash.
    verified=0
    for name,pin in gate['input_sha256'].items():
        assert sha(Path(name))==pin['sha256'],name
        verified+=1
    out=dict(command='PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py',
             input_sha256={str(p):{'sha256':sha(p)} for p in [Path(__file__),DB,OUT/'TRANSFORMATION_CHECK.json',OUT/'COUNTS.json',OUT/'NEW_ROWS.jsonl',OUT/'SOURCE_MAP.jsonl']},
             status='PASS_EVIDENCE_ONLY_BUILD_GATE_FAILED',pairs=pairs,failures=fail,
             verified_input_hashes=verified,empty_new_rows=True,unchanged_counts=True)
    (OUT/'VERIFY.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='input_sha256'}))
if __name__=='__main__':main()
