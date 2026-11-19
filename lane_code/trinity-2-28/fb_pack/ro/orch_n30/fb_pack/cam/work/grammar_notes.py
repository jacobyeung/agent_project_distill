from common import *
seen=start('grammar_notes.py')
from student_pilot import trace_grammar as grammar
from student_pilot.r2_grammar import check_shared,SHARED_SHA256
check_shared();pin(grammar.__file__,SHARED_SHA256)
classification=load(ROOT/'out/CLASSIFICATION.json');sources=load(ROOT/'out/SOURCE_FORMS.json')
# Small counterexamples exercise the provenance boundary that motivates the edits.
cases=[
 ('symbolic_negation','<call>\n<tool_response>dz = -0.68 m</tool_response>\nThe backward response component is -dz = 0.68 m.',False),
 ('unsupported_zero','<call>\n<tool_response>dz = -0.68 m</tool_response>\nThe backward response component is 0 - -0.68 = 0.68 m.',False),
 ('sourced_zero','<call>\n<tool_response>dz = -0.68 m</tool_response>\nThe response gives -0.68 - -0.68 = 0.00.\nThe backward response component is 0.00 - -0.68 = 0.68 m.',True),
 ('symbol_only','<call>\n<tool_response>dz = -0.68 m</tool_response>\nThe backward response component is -dz.',True),
 ('numeric_half_turn','I will use the pose head turn, wrapped to (-180, 180], with positive turn meaning left and a half turn reported as +180 degrees.\n<call>\n<tool_response>turn = -88 deg</tool_response>',False),
 ('worded_half_turn','I will use the pose head turn, '+ROT_NEW+'\n<call>\n<tool_response>turn = -88 deg</tool_response>',True)]
results=[]
for name,body,expected in cases:
 errs=grammar.validate_trace(body,form='program',question='How did the camera move?')
 results.append(dict(name=name,body=body,expected_pass=expected,passed=not errs,violations=[e._asdict() for e in errs]))
 assert (not errs)==expected,(name,errs)
capture(seen)
write('out/GRAMMAR_CHECKS.json',dict(grammar_sha256=SHARED_SHA256,cases=results))
text='''The pinned shared grammar accepts numeric tokens with these sources: valid one-based frame citations; consecutive Step labels starting at 1; explicit list counts and prior list cardinalities; constants printed in the question or options; program-response values; and verified explicit binary arithmetic. The r2 program adapter passes the question but does not pass the options separately, so only options already embedded in the question can license constants on this intake path.

Program-response matching compares Decimal values rounded to two decimal places with ROUND_HALF_UP. Complete tool-response bodies, including later bodies, populate all_printed for numeric provenance. Response bodies themselves are masked from lexical checks. Call attributes are syntax, not evidence; r2 replaces the recorded call token with <call> before shared validation.

Arithmetic must literally match a op b = c, with op in +, -, Unicode minus, *, x, multiplication sign, or /. Both operands need provenance from responses, question constants, prior list counts, prior results, or results derived earlier on the same line. The fixed conversion literals 100, 1000, 3.28084, 39.3701, 10.7639, 0.3048, and 2.54 are also allowed as operands. Decimal arithmetic must produce the printed result at its written precision (ROUND_HALF_UP); fractions and percentages require exact equality. A symbolic unary expression such as -dz does not license a following numeric result. Zero and minus one are not generally licensed arithmetic operands. A subtraction that first derives zero from an operand minus itself would work, but it adds unnecessary trace text.

A numeric token followed by a measurement unit has a stricter rule: in a program trace, the token must match a printed response value or be the result occurrence of correct explicit arithmetic on that line. A question constant, frame index, prior result, or list count alone does not license a unit quantity. Thus a question may license 180 as a number while +180 degrees still fails unit_quantity. Number words generally require matching question words or digits; the exact half turn idiom is permitted. Writing a half circle is not a safe general substitute.

CAM-ROT-WORDS-v1 replaces only the numeric wrap/convention clause with: wrapped to the shortest signed turn, with positive turn meaning left and a half turn reported as positive. This preserves the signed shortest-turn convention and assigns the half-turn tie to the positive/left direction. CAM-DIR-SYMBOL-v1 removes only the numeric restatement after a negated component in Scoring each option lines; for example, backward = -dz = 0.68 m becomes backward = -dz. Direct printed component values, option order, the largest-component conclusion, and the option letter remain unchanged.

These are two uniform syntactic rules. They apply to every matching line, including four direction rows whose derived numbers happened to be licensed already. Displacement traces need no change. The checks in GRAMMAR_CHECKS.json demonstrate why adding an unsourced zero would fail and why keeping the symbolic component passes. CLASSIFICATION.json records every original refusal with its exact line and diagnostic; SOURCE_FORMS.json records all numeric-normalized line variants and their counts.

The same two forms occur in the authenticated CAMERA_SOURCES.jsonl.gz subset: 2,000 rotation convention lines and 2,000 direction score lines. This supports a comparison of the retained source traces with the rewritten wording traces, but it does not establish the composition or total counts of the unavailable full P routing base.

Command: use the recorded CPU prefix with work/grammar_notes.py. Exact source hashes, cases, and expected/observed results are in GRAMMAR_CHECKS.json. No grammar or tree file is modified.
'''
(ROOT/'out/GRAMMAR.md').write_text(text)
print('grammar boundary cases',len(results),'PASS')
