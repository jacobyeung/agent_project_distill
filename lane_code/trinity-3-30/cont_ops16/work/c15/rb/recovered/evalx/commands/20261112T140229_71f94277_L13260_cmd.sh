<!-- recovered by seal_plan: transcript=71f94277 line=13260 utc=2026-11-12T14:02:29.414Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%FT%TZ); /scratch/jjyeung/envs/p1cpu/bin/python -I -s - "$T" <<'EOF'
import sys, os
t = sys.argv[1]
f = '/scratch/jjyeung/orch_cd/model_design_review/MODEL_IMPROVEMENT_PLAN_20261111.md'
L = open(f).read().split('\n')
i = 151
assert L[i].startswith('- **At m100, the reversal test of section B**')
L[i] = L[i].rstrip() + (' The tested tasks are the benchmark tasks the leg trains directly and dev-S1 holds: route planning, counting, relative direction (easy, medium, hard), relative distance and size; relative count and relative size (dev-only types with no rows this leg) are reported beside them and do not stop the leg (scope fixed %s, before any leg read). Baseline at step 0, f17 minus the parent CP1 m200 on dev-S1 primary (evalx RESULT 20261112T1400Z): overall +1.85 [-2.06, +5.49] (73.50 against 71.64); route planning +35.3 [+23.6, +47.1]; counting +10.5 [+1.1, +20.1]; relative count +15.1 [+4.4, +26.9]; size -16.9 [-25.6, -8.9]; every other type spans zero. The leg therefore has to close route planning and counting by m100.' % t)
open(f + '.next', 'w').write('\n'.join(L)); os.replace(f + '.next', f)
print('ok')
EOF
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $M/result-f17-devs1-vs-parent-20261112.md <<'EOF'
---
name: result-f17-devs1-vs-parent-20261112
description: "f17 on dev-S1 primary (1,375 items, true timing, 32 spread) scores 73.50 against the LEG-S1 parent CP1 m200 at 71.64; f17 leads route planning +35, counting +10.5, relative count +15; the parent leads size +17; the m100 rule tests route planning and counting"
metadata:
  type: project
---

On dev-S1's primary stratum f17 scores 73.50 and the LEG-S1 parent CP1 m200 scores 71.64 (B2048); the difference +1.85 [-2.06, +5.49] spans zero (evalx RESULT 20261112T1400Z, 1-18 GPU 2, r5 scorer, room bootstrap).

Per type, f17 minus the parent: route planning +35.3 [+23.6, +47.1] (own labels); counting +10.5 [+1.1, +20.1] (68.9 against 58.4); relative count +15.1 [+4.4, +26.9]; size -16.9 [-25.6, -8.9] (51.2 against 68.1); absolute distance +4.3, direction easy +2.0, medium +1.3, hard +6.0, relative distance -4.7, relative size -3.3, room +15.8 (36 items): all span zero.

**Why:** these are the comparators of the leg's m100 stop rule. The rule tests the benchmark tasks the leg trains directly (route planning, counting, direction, relative distance, size); relative count and relative size are dev-only types with no rows in LEG-S1 and are reported only (scope fixed 2026-11-12 before any leg read; plan line 152).

**How to apply:** at m100 the leg must have closed route planning and counting against f17 (interval not wholly below zero), or it stops and the lineage reopens. Add direct relative-count rows to the next leg's mix. Related: [[result-devs1-baseline-cp1-20261112]], [[result-devs1-route-table-predicted-masks-20261112]].
EOF
echo "- **READ FIRST, result 11-12:** [f17 vs parent on dev-S1](result-f17-devs1-vs-parent-20261112.md) f17 73.50 vs CP1 m200 71.64 (tie); f17 leads route +35, counting +10.5, relative count +15; parent leads size +17; m100 rule tests route + counting" >> $M/MEMORY.md
echo "$T orch-home-distill-79: evalx RESULT 1400Z: f17 on dev-S1 primary (1,375; true timing; 32 spread; 1-18 GPU 2, 19 min): 73.50 vs CP1 m200 71.64 (B2048), +1.85 [-2.06,+5.49]; f17 - CP1: route planning +35.33 [+23.57,+47.14], counting +10.53 [+1.09,+20.13], relative count +15.11 [+4.44,+26.87], size -16.93 [-25.56,-8.92], abs distance +4.27, dir easy +2.00 / medium +1.33 / hard +6.00, rel distance -4.67, relative size -3.33, room +15.83 (36 items) all spanning zero. m100 rule scope fixed in the plan (line 152) before any leg read: tested = route planning, counting, direction, relative distance, size; relative count and relative size (dev-only, no rows this leg) reported only. Memory result-f17-devs1-vs-parent-20261112.md. Facing-away cells for f17 running; then dense+aliases. Content scan of kit ae3cfc04 with the code-aws naming scanner: 31,538 naming hits (not applicable on Orchard; precedent okit_cr self-certified); dispatched the Orchard-scope independent scan (integrity + secrets + run-time refusal analysis; leg_s1_review/BRIEF_ORCHARD_SCOPE_SCAN.md) and asked leg_s1_tree for the gate's intent and any in-job naming check." >> ORCH_HANDOFF.md