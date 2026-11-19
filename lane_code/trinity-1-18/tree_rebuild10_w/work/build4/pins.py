from pathlib import Path
import hashlib
L = Path(__file__).resolve().parents[2]
for src, dest, expected in (
    ('work/rows_slices/work/trace_grammar.py', 'work/tree_r1/student_pilot/trace_grammar.py', 'a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268'),
    ('work/shared/dev_scene_exclusions_d0.json', 'work/tree_r1/student_pilot/r2_dev_merged.json', 'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5')):
    raw = (L/src).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    (L/dest).write_bytes(raw)
p = L/'work/tree_r1/student_pilot/r2_grammar.py'
p.write_text(p.read_text().replace('49e814ebfa1a4a4b3b1dc865c4ee715ae65b6f80aa3d5c8d28e5c649f6d1a635', 'a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268'))
