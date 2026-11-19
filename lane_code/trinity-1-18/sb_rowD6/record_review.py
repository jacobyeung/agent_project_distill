"""Record the completed agent reading of all sixty sampled questions and traces."""
import hashlib,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/'out'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[json.loads(x) for x in re.findall(r'```json\n(.*?)\n```',(OUT/'READ60.md').read_text(),re.S)]
assert len(rows)==60
verify=json.loads((OUT/'VERIFY.json').read_text())
assert verify['status']=='PASS' and verify['input_sha256'][str(OUT/'READ60.md')]['sha256']==sha(OUT/'READ60.md')
verdicts=[
    (1,5,'Away easy: each reference right becomes left, with the resulting letter taken from the unchanged options.'),
    (6,10,'Away easy: each reference left becomes right. Standing point, heading object and queried object agree across question and trace.'),
    (11,15,'Away hard: reference front-right becomes back-left. Plural object names preserve grammatical agreement.'),
    (16,20,'Away hard: reference front-left becomes back-right. The half turn is stated in its own Step 3.'),
    (21,25,'Away hard: reference back-right becomes front-left. Unusual names remain exactly the source names.'),
    (26,30,'Away hard: reference back-left becomes front-right. Source sentences with the queried object first retain the correct spatial roles.'),
    (31,35,'Toward easy: the source away answer right maps to left. Seen frame citations remain unchanged and the heading is explicitly kept.'),
    (36,40,'Toward easy: the source away answer left maps to right. No turn appears in the new trace.'),
    (41,45,'Toward hard: source front-right maps to back-left, consistent with each printed reference-heading relation.'),
    (46,50,'Toward hard: source front-left maps to back-right, with correct option letters and kept headings.'),
    (51,55,'Toward hard: source back-right maps to front-left. All frame slots are in range and retain the source citations.'),
    (56,60,'Toward hard: source back-left maps to front-right. Row 59 legitimately cites two distinct objects in frame 12; the source citation is preserved.'),
]
value=dict(command='PYTHONDONTWRITEBYTECODE=1 python record_review.py',input_sha256={str(p):dict(sha256=sha(p),bytes=p.stat().st_size)
    for p in (Path(__file__),OUT/'READ60.md',OUT/'REVIEW_TEXT60.md',OUT/'VERIFY.json',OUT/'NEW_ROWS.jsonl')},status='PASS',rows=60,
    reviewer='Codex /root sb_rowD6',full_record_file_sha256=sha(OUT/'READ60.md'),review_text_sha256=sha(OUT/'REVIEW_TEXT60.md'),
    method='All sixty complete JSON records were parsed and matched by the verifier. The agent read every question, option list and full reasoning/answer text from READ60.md in three batches of twenty.',
    observations=[dict(first=a,last=b,verdict='PASS',note=n,qids=[r['qid'] for r in rows[a-1:b]]) for a,b,n in verdicts],
    unresolved_issues=[],limitation='Frame-image contents were not reopened; full metadata is exactly source-preserved and verified.')
(OUT/'READ60_REVIEW.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
(BASE/'STATUS.md').write_text('The 60-row semantic review passes: every sampled question, option list, reference-heading relation, turn/keep step and answer is consistent. Full JSON records match the emitted rows, and their frame metadata matches the sources. The final report and archive remain to be sealed.\n')
print('READ60 review PASS: 60 rows, 12 cells, no unresolved issues.')
