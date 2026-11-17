"""Give existing consistency assertions an explicit input boundary."""
from pathlib import Path
T=Path(__file__).resolve().parents[2]/'work/tree_r1/student_pilot'
p=T/'h1_faithful.py';s=p.read_text()
old="    if target != result['target']:\n        raise MaterializeRefusal('faithful_render_mismatch')\n    return result, target, spans, segments"
new="    require_render_identity(result, target)\n    return result, target, spans, segments\n\n\ndef require_render_identity(result, target):\n    \"\"\"Require the materializer and training renderer to produce identical bytes.\"\"\"\n    if target != result['target']:\n        raise MaterializeRefusal('faithful_render_mismatch')"
assert s.count(old)==1;p.write_text(s.replace(old,new))
p=T/'gf1_cache.py';s=p.read_text()
old="    if set(donor) != set(info) or any(k == v for k, v in donor.items()) or sorted(donor.values()) != sorted(info):\n        raise AssertionError('Shuffled-bank plan is not a derangement')"
assert s.count(old)==1
s=s.replace(old,"    require_derangement(donor, info)")
position=s.index('\ndef shuffled_bank_plan(')
s=s[:position]+"\ndef require_derangement(donor, info):\n    \"\"\"Check the planner's complete one-to-one assignment without self donors.\"\"\"\n"+old+"\n\n"+s[position:]
p.write_text(s)
