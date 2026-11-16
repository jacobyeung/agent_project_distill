<!-- recovered by seal_plan: transcript=71f94277 line=30587 utc=2026-11-14T09:39:36.605Z kind=commands original_path=(bash command)  -->
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; F=/scratch/jjyeung/orch_cd/ORCH_STATE_20261111T0935Z.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$F" "$S/state_block.md" <<'EOF'
import sys
f,b=sys.argv[1:]
L=open(f).read().split('\n')
assert L[32].startswith('## Active lanes at 2026-11-14T04:16Z') and L[48].startswith('| leg_s1_tree'), (L[32][:40],L[48][:40])
new=open(b).read().rstrip('\n').split('\n')
out=L[:32]+new+L[49:]
open(f,'w').write('\n'.join(out))
print(len(L),len(out))
EOF
sed -n 33p $F | cut -c1-60; grep -n "^Review briefs and verdicts" $F | cut -c1-40; echo "- $(date -u +%Y-%m-%dT%H:%MZ) ORCH_STATE Active-lanes block rewritten (state at 09:45Z)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md