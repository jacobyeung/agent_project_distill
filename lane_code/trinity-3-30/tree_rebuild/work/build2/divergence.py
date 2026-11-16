import json
from pathlib import Path
import re
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot import trace_grammar as shared, r2_grammar as wrapper
cases=[
    ('duplicate object across lines','Locate: the chair is seen in frame 2.\nLocate: the chair is seen in frame 3.\nRelate: the chair is to the right.', 'Where is the chair?'),
    ('explicit-label relation without Locate','Relate: the chair is to the right.', 'Where is the chair?'),
    ('frame stated in seconds','The chair is seen in frame 2 seconds.', 'Where is the chair?'),
    ('single-line count before a list','Locate: chair a is seen in frame 1.\nLocate: chair b is seen in frame 2.\nStep: list [chair a; chair b]; count = 3.', 'Count chairs.'),
]
results=[]
for name,body,question in cases:
    errors=shared.validate_trace(body,form='direct',question=question,n_frames=32)
    try:wrapper.validate_direct('<think>\n'+body+'\n</think>\nA',question,32);refused=False
    except ValueError:refused=True
    results.append(dict(name=name,example=body,question=question,shared_rules=[e.rule_id for e in errors],wrapper_refuses=refused))
(L/'out/GRAMMAR_DIVERGENCE.json').write_text(json.dumps(results,indent=2)+'\n')
text=['# Grammar divergence','',
      'The shared validator is byte-identical to the supplied copy; its binding is `work/tree_r1/student_pilot/r2_grammar.py:SHARED_SHA256`. '
      'The wrapper calls `validate_trace`, preserves native event masking and retains the stricter explicit-label dialect needed by build-1 fixtures. '
      'The original shared test file runs unchanged through an import-path adapter in `work/build2/run_tests.py`.','']
for item in results:
    text+=['**'+item['name']+'**', '', '```text',item['example'],'```','',
           'Shared result: '+(', '.join(item['shared_rules']) or 'accept')+'. Tree wrapper: '+('refuse' if item['wrapper_refuses'] else 'accept')+'.','']
text += ['The explicit-label no-Locate refusal is a compatibility restriction, not a new requirement on the shared prose dialect. '
         'Native call parameters are checked by the event parser, then represented as `<call>` for lexical validation. '
         'For example, `<gap rule="box_grid_5cm">` after inline response tags otherwise exposes the rule-name digit to the shared quantity checker. '
         'The original event bytes, response spans and training masks remain unchanged.', '',
         'The wrapper also refuses a response without a corresponding masked event, a later response used to justify an earlier number, '
         'a call after a failed response, and deployed-selector training responses. These checks need native event structure, which the shared lexical API does not own. '
         'Examples and mutations are in `work/tree_r1/tests/test_r2_families.py`, `test_r2_refusals.py` and `test_r2_edges.py`.']
(L/'out/GRAMMAR_DIVERGENCE.md').write_text('\n'.join(text)+'\n')
