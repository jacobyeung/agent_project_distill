<!-- recovered by seal_plan: transcript=71f94277 line=2623 utc=2026-11-11T14:13:58.779Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/vla_design_review && cp -p VLA_SCHEMA.md VLA_SCHEMA.pre_check2.md && cp -p schema_examples.py schema_examples.pre_check2.py && python3 - <<'EOF'
import re
p='VLA_SCHEMA.md'; s=open(p).read()
a="`w2g = pose_encoding_to_extri_intri(global_[None], (518, 518), 'absT_quaRy_noFoV', build_intrinsics=False)`"
b="`w2g, _ = pose_encoding_to_extri_intri(global_[None], (518, 518), 'absT_quaRy_noFoV', build_intrinsics=False)` (the decoder returns a tuple)"
assert a in s; s=s.replace(a,b)
a="`vla.eval`, `vla.data`, `vla.where`, `vla.provider` and `vla.cond` are ignored for navigation arms;"
b="`vla.eval`, `vla.data`, `vla.where` and `vla.cond` are ignored for navigation arms, and of `vla.provider` only `vla.provider.g3t` is kept (the evaluation-only `g3t_depth` check and section 6.5 need the tower settings);"
assert a in s; s=s.replace(a,b)
open(p,'w').write(s)
p='schema_examples.py'; s=open(p).read()
a="why = 'no_lift' if 'no_lift' in (ent.get('wrist'), ent.get('agent')) else 'not_seen'"
b="views = (ent.get('wrist'), ent.get('agent'))\n            why = 'no_lift' if 'no_lift' in views else ('no_point' if 'no_point' in views else 'low_presence')"
assert a in s; s=s.replace(a,b)
a="elif why == 'not_seen':"
b="elif why in ('low_presence', 'no_point'):"
assert a in s; s=s.replace(a,b)
open(p,'w').write(s); print('patched')
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -B schema_examples.py 2>&1 | tail -n 3 | cut -c1-200; grep -n "not_seen" schema_examples.py VLA_SCHEMA.md | head -3