<!-- recovered by seal_plan: transcript=71f94277 line=11533 utc=2026-11-12T10:37:16.008Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; python3 - <<'EOF'
p='/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/result-devs1-baseline-cp1-20261112.md'
s=open(p).read()
old="- Facing-away direction items (150, held-out): 14.0 (easy 24, medium 12, hard 6), below every constant; 95 of 150 answers are the facing-toward answer."
new="- Facing-away direction items (150, held-out): 14.0 (easy 24, medium 12, hard 6), below every constant; 95 of 150 answers are the facing-toward answer. Forward twins of the same 150 geometries: 91.3 (easy 92, medium 96, hard 86); on 118 pairs the forward question is right and the facing-away one wrong, so perception is not the failure."
assert old in s
open(p,'w').write(s.replace(old,new))
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1036Z (FINAL): CP1 m200 on the same 150 held-out geometries: forward twins 91.33 (easy 92, medium 96, hard 86) vs facing away 14.0; 118/150 pairs forward right and away wrong; budgets identical; ran on 1-18 GPU 2 under vnice 10:29-10:34Z. Perception is not the failure; the reversal is. Memory updated." >> ORCH_HANDOFF.md