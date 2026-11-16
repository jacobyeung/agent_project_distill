<!-- recovered by seal_plan: transcript=71f94277 line=12534 utc=2026-11-12T12:36:01.062Z kind=commands original_path=(bash command)  -->
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; F=/scratch/jjyeung/orch_cd/ORCH_STATE_20261111T0935Z.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - "$F" "$S" <<'EOF'
import sys
f, s = sys.argv[1], sys.argv[2]
L = open(f).read().split('\n')
assert L[32].startswith('## Active lanes') and L[42].startswith('Ended with final RESULTs') and L[48].startswith('- LEG-S1:') and L[56].startswith('- LEG-S1 review')
lanes = open(s+'/state_lanes.md').read().rstrip('\n').split('\n')
legs1 = open(s+'/state_legs1.md').read().rstrip('\n').split('\n')
rev = open(s+'/state_review.md').read().rstrip('\n').split('\n')
out = L[:32] + lanes + L[43:48] + legs1 + L[49:56] + rev + L[57:]
open(f+'.next', 'w').write('\n'.join(out))
import os
os.replace(f+'.next', f)
print(len(L), '->', len(out))
EOF
grep -n "^## Active lanes\|^- LEG-S1" $F | cut -c1-90