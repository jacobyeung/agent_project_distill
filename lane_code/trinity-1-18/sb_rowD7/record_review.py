"""Record the agent's completed reading of all 60 sampled questions and traces."""
import hashlib,json,re
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'out'
def pin(p):return dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
rows=[json.loads(x) for x in re.findall(r'```json\n(.*?)\n```',(O/'READ60.md').read_text(),re.S)]
assert len(rows)==60
v=json.loads((O/'VERIFY.json').read_text());assert v['status']=='PASS'
assert v['input_sha256'][str(O/'READ60.md')]['sha256']==pin(O/'READ60.md')['sha256']
observations=[
 (1,10,'The source right relation becomes left, and each option letter agrees.'),
 (11,20,'The source left relation becomes right. Row 17 preserves the source agreement error “is the books”; the facing edit adds no error.'),
 (21,30,'Front-right becomes back-left. The preserved Cartesian sentence defines forward along the new facing direction.'),
 (31,40,'Front-left becomes back-right. Row 40 preserves “is the mailboxes” and the literal source name “trash bin(s)”.'),
 (41,50,'Back-right becomes front-left. Row 43 preserves the source spelling “collander”.'),
 (51,60,'Back-left becomes front-right. Every standing point, heading object and query object agrees between question and trace.')]
notes=[dict(row=17,qid=rows[16]['qid'],finding='Inherited source agreement: “is the books”.'),
 dict(row=40,qid=rows[39]['qid'],finding='Inherited source agreement: “is the mailboxes”; source name “trash bin(s)” remains literal.'),
 dict(row=43,qid=rows[42]['qid'],finding='Inherited source spelling: “collander”.')]
v.update(manual_review='PASS: all 60 sampled questions, options and complete traces read; inherited source wording notes recorded in READ60_REVIEW.json.',
 manual_review_scope='Question and trace semantics read from REVIEW_TEXT60.md; all full JSON records parsed and compared. Frame pixels were not reopened.',
 inherited_wording_notes=notes)
v['input_sha256'][str(Path(__file__))]=pin(Path(__file__));v['input_sha256'][str(O/'REVIEW_TEXT60.md')]=pin(O/'REVIEW_TEXT60.md')
v['command']+='; PYTHONDONTWRITEBYTECODE=1 python record_review.py'
(O/'VERIFY.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
value=dict(command='PYTHONDONTWRITEBYTECODE=1 python record_review.py',input_sha256={str(p):pin(p) for p in [Path(__file__),O/'READ60.md',O/'READ30.md',O/'REVIEW_TEXT60.md',O/'VERIFY.json',O/'NEW_ROWS.jsonl']},
 status='PASS',rows=60,reviewer='Codex /root sb_rowD7',
 method='Read all questions, options and complete traces in rows 1–20, 21–40 and 41–60; independently parsed all complete JSON records and compared them to output. Ten rows cover each answer cell.',
 observations=[dict(first=a,last=b,note=n,qids=[r['qid'] for r in rows[a-1:b]]) for a,b,n in observations],
 inherited_wording_notes=notes,blocking_issues=[],limitation='The task requires preserving source wording outside the clause. Listed source agreement/spelling defects remain unchanged; frame-image contents were not reread.')
(O/'READ60_REVIEW.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
(B/'STATUS.md').write_text('The 60-row semantic review is complete. All half-turn labels, option letters and object roles agree. The review records three inherited source wording notes; questions differ from sources only in the facing clause. VERIFY.json has a final manual-review result. Packaging remains.\n')
print('Semantic review PASS: 60 rows; 3 inherited source wording notes; no blocking issues.')
