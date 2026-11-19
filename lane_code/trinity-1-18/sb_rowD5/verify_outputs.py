"""Independently check the failure evidence, using source records and a separate rule."""
import collections as C
import hashlib
import json
from pathlib import Path
import sqlite3

BASE=Path(__file__).resolve().parent
OUT=BASE/'out'
DB=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()

def opts(r):return dict(s.split('. ',1) for s in r['student_input']['options'])

def main():
    gate=json.loads((OUT/'GATE.json').read_text())
    counts=json.loads((OUT/'COUNTS.json').read_text())
    checks=json.loads((OUT/'CHECKS.json').read_text())
    dbhash=sha(DB);assert dbhash==gate['input_sha256'][str(DB)]['sha256']
    con=sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    exact=consistent=literal_pass=0;fail=[];literal_fail=[];seen=set();medium=C.Counter()
    for x in gate['comparisons']:
        a_raw=con.execute('select row from rows where i=?',(x['away_i'],)).fetchone()[0]
        t_raw=con.execute('select row from rows where i=?',(x['toward_i'],)).fetchone()[0]
        assert sha_bytes(a_raw)==x['away_row_sha256'] and sha_bytes(t_raw)==x['toward_row_sha256']
        a=json.loads(a_raw);t=json.loads(t_raw)
        assert a['qid']==x['away_qid'] and t['qid']==x['toward_qid']
        assert a['qid'] not in seen;seen.add(a['qid'])
        assert a['pool']=='r1_away_opp' and a['facing']=='away' and t['facing']=='toward'
        assert a['pair_id']==t['pair_id'] and a['scene']==t['scene'] and a['dataset']==t['dataset']
        av=opts(a)[a['answer']];tv=opts(t)[t['answer']]
        assert av==x['stored_away_label'] and tv==x['toward_label']
        flipped='-'.join({'front':'back','back':'front','left':'right','right':'left'}[z] for z in tv.split('-'))
        literal_pass+=flipped==av
        if flipped!=av:literal_fail.append(a['qid'])
        if x['family']=='medium':
            allowed={'left':{'right','back'},'right':{'left','back'},'back':{'left','right'}}[tv]
            assert set(opts(a).values())=={'left','right','back'}
            assert not x['exact_unique_reproduction'] and not x['option_bijection']
            medium[tv,av]+=1;fail.append(a['qid'])
        else:
            allowed={flipped};assert x['exact_unique_reproduction'] and x['option_bijection']
            assert flipped==av;exact+=1
        assert allowed==set(x['allowed_away_labels'])
        assert av in allowed;consistent+=1
    assert len(seen)==8511 and exact==gate['exact_unique'] and consistent==gate['set_consistency_pass']
    assert fail==[x['away_qid'] for x in gate['failures']]
    assert literal_fail==[x['away_qid'] for x in gate['literal_flip_disagreements']]
    assert literal_pass+gate['literal_flip_diagnostic_disagreements']==8511
    assert counts['before']==counts['after'] and counts['admitted_before']==counts['admitted_after']
    assert checks['status']=='FAIL_STOP' and checks['binding_ready'] is False
    assert sum(x['rows'] for x in counts['before'])==93370
    for name in ('NEW_ROWS.jsonl','SOURCE_MAP.jsonl'):assert (OUT/name).stat().st_size==0
    for example in json.loads((OUT/'EXAMPLES.json').read_text())['examples']:
        for role,key in [('toward','toward_i'),('away','away_i')]:
            assert example[role]==json.loads(con.execute('select row from rows where i=?',(example['comparison'][key],)).fetchone()[0])
    con.close()
    inputs={str(p):sha(p) for p in [Path(__file__),BASE/'build_rows.py',OUT/'GATE.json',OUT/'COUNTS.json',OUT/'CHECKS.json',OUT/'EXAMPLES.json',OUT/'READ60.md',OUT/'NEW_ROWS.jsonl',OUT/'SOURCE_MAP.jsonl']}
    inputs[str(DB)]=dbhash
    result=dict(status='PASS_FAILURE_EVIDENCE_ONLY',binding_ready=False,
        command='PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py',input_sha256=inputs,
        checked_pairs=len(seen),exact_unique=exact,ambiguous=len(fail),consistency_pass=consistent,
        literal_flip_disagreements=len(literal_fail),new_rows=0,
        medium_transitions=[dict(toward=a,away=b,rows=n) for (a,b),n in sorted(medium.items())])
    (OUT/'VERIFY.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

def sha_bytes(s):return hashlib.sha256(s.encode()).hexdigest()
if __name__=='__main__':main()
