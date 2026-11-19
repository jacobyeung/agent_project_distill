"""Byte-exact copies of pinned tree files, checked at import.

trace_grammar.py = the sealed validator a41ba191... (tree build 5 student_pilot/trace_grammar.py)
answers.py       = student_pilot/benchmark_eval/answers.py (parser student-answer-v1), base tree b01ce449
"""
import hashlib
from pathlib import Path

PINS = {
    'trace_grammar.py': 'a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268',
    'answers.py': '65df49a70f0ca5c160926ea9b65df7a134758e768f509374fbea6eaf6e8fb146',
}
for _name, _sha in PINS.items():
    _got = hashlib.sha256((Path(__file__).parent / _name).read_bytes()).hexdigest()
    if _got != _sha:
        raise ImportError(f'vendored {_name} sha256 {_got} != pin {_sha}')
