from pathlib import Path
import hashlib
L = Path(__file__).resolve().parents[2]
T = L/'work/tree_r1'
source = (L/'work/shared/trace_grammar.py').read_bytes()
assert hashlib.sha256(source).hexdigest() == '49e814ebfa1a4a4b3b1dc865c4ee715ae65b6f80aa3d5c8d28e5c649f6d1a635'
old = T/'student_pilot/r2_grammar.py'
if not old.exists():
    text = (T/'student_pilot/trace_grammar.py').read_text()
    text = text.replace('def validate_direct(', 'def legacy_direct(').replace('def validate_program(', 'def legacy_program(')
    old.write_text(text)
(T/'student_pilot/trace_grammar.py').write_bytes(source)
(T/'student_pilot/r2_withheld.json').write_bytes((L/'work/shared/WITHHELD_ROOMS_80.json').read_bytes())
for relative in ['student_pilot/r2_contract.py', 'tests/test_r2_data_path.py', 'tests/test_r2_families.py', 'tests/test_r2_refusals.py']:
    path = T/relative
    text = path.read_text().replace('from .trace_grammar import PROGRAM_TYPES, validate_direct, validate_program', 'from .r2_grammar import PROGRAM_TYPES, validate_direct, validate_program')
    text = text.replace('trace_grammar as G', 'r2_grammar as G')
    path.write_text(text)
