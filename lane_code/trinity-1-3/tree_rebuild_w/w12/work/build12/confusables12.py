"""Check each reviewed code point in both independent text gates."""
from pathlib import Path
import hashlib,json,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L/'work/tree_r1';O=B/'proofs/confusables'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot import row_text_audit as A
cases=[(0x0455,'not {}een'),(0x0422,'NO{} SEEN'),(0x0430,'box un{}vailable'),
       (0x0456,'own metr{}c'),(0x0441,'tower_s{}ale_rule'),(0x039D,'{}OT SEEN'),
       (0x03A4,'NO{} SEEN'),(0x0585,'n{}t seen')]
rows=[]
for code,template in cases:
    text=template.format(chr(code));assert chr(code) in text
    row={'target':'<think>'+text+'</think>\n1'}
    reasons=A.reasons(row);assert 'non_ascii_authored_think' in reasons
    with patch.object(A,'reasons',return_value=[]),patch.object(A,'normalized_text',return_value=''),patch.object(A,'PATTERNS',{}):
        try:A.check(row,'vqa')
        except ValueError as error:
            assert 'non_ascii_authored_think' in str(error);refusal=str(error)
        else:raise AssertionError('Independent reader admitted '+hex(code))
    rows.append(dict(codepoint=f'U+{code:04X}',text=text,reasons=reasons,reader_refusal=refusal))
record=dict(status='PASS',cases=rows,source='work/tree_r1/student_pilot/row_text_audit.py',
    source_sha256=hashlib.sha256((T/'student_pilot/row_text_audit.py').read_bytes()).hexdigest(),
    driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(O/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');monitor.save(O)
print(json.dumps(dict(status='PASS',codepoints=[r['codepoint'] for r in rows])))
