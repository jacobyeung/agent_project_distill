<!-- recovered by seal_plan: transcript=71f94277 line=27143 utc=2026-11-14T01:15:03.150Z kind=commands original_path=(bash command)  -->
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$M" <<'EOF'
import sys, os
m = sys.argv[1]
p = os.path.join(m, "MEMORY.md")
lines = open(p).read().split("\n")
i20 = next(k for k, l in enumerate(lines) if l.startswith("- Trainer/sets:"))
i21 = next(k for k, l in enumerate(lines) if l.startswith("- Results: [Answer-only vs C]"))
assert i21 == i20 + 1
body = ("---\nname: archive-index-trainer-sets-and-early-results\n"
        "description: Index of September to mid-October memories on the student trainer, training sets and early results (moved out of MEMORY.md to keep it under its size limit)\n"
        "metadata:\n  type: reference\n---\n\n"
        "Pointers moved out of `MEMORY.md` on 2026-11-14; every file still exists in this folder (or at the absolute path given). Open one when a task touches the old trainer, the September and October training sets, or results before 2026-10-15.\n\n"
        + lines[i20] + "\n" + lines[i21] + "\n")
open(os.path.join(m, "archive-index-trainer-sets-and-early-results.md"), "w").write(body)
new = "- Archive: [Trainer, sets and early results](archive-index-trainer-sets-and-early-results.md) September to mid-October pointers (trainer v3.1, corrected/full-pool sets, holdout, seed noise, early results, old handoffs)"
lines[i20:i21+1] = [new]
open(p, "w").write("\n".join(lines))
print(len("\n".join(lines).encode()))
EOF
cat > $M/result-legs1-m100-20261114.md <<'EOF'
---
name: result-legs1-m100-20261114
description: "LEG-S1 step-100 read on dev-S1 (Orchard H100, 2026-11-14): registered stop test PASS; route planning +24.7 vs parent, counting 63.3 vs parent 59.9 vs f17 69.1; the direct read cannot score absolute distance and room size for this lineage (routing calls repeat without a tool response)"
metadata:
  type: project
---

LEG-S1 (Orchard job 169097, run 469ddece, parent CP1 m200) passed its registered step-100 stop test on dev-S1: no tested type has an interval wholly below zero against f17 (evalx packet `/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step100_b719d20dd/PACKET.json`, sha 59cb98e6; reader fb2796c5; job 169328).

Leg (2,048-token budget) minus parent, steps 50 and 100: route planning +22.7 and +24.7 [+17.0, +32.3]; counting -0.4 and +3.3 [-1.5, +8.4] (raw 59.5, 63.3; parent 59.9; f17 69.1); direction hard -2.0 and +3.3; relative distance +0.7 and -4.7 [-10.0, +0.6]; size +6.3 and +3.7; primary overall -0.9 and -1.6 [-3.6, +0.5]. Leg minus f17 at step 100: route planning -9.3 [-20.3, +0.7] (parent was -34.0), counting -5.9 [-15.3, +3.5], size +21.9, primary overall -3.4 [-7.4, +0.9].

The direct read cannot score the two routed types for this lineage: the leg has no direct rows for absolute distance and room size, emits routing calls (`<gap a=... b=...>`) and repeats them because the direct harness returns no tool response (thinking at the 2,048 cap on both types; 16k-cap outputs end in repetition). Hence absolute distance -16.6 and room size -19.4 against the parent, 164 of the 168 budget hits, and all four producer errors (retokenizing a cut thinking prefix) are harness effects. Without those two types the leg is about +0.7 against the parent on primary overall (my arithmetic from the per-type table, not a bootstrapped number).

Facing-away direction controls fell to 22 / 12 / 4 (step 50: 30 / 14 / 10; majority constants 54 / 40 / 36); forward controls 96 / 98 / 84.

**Why:** this is the first scored read of the four-stream leg; it sets what each later milestone read must show and what the next seal must change.

**How to apply:** judge routed types (absolute distance, room size, camera types) only from the routed read with the model's own heads; in any direct serving or eval path stop generation at a routing call. At step 200 watch relative distance, size, the facing-away controls and route planning's margin against f17. Related: [[result-f17-devs1-vs-parent-20261112]], [[result-devs1-route-table-predicted-masks-20261112]], [[lesson-review-decision-code-before-read-20261113]].
EOF
echo "- **READ FIRST, result 11-14:** [LEG-S1 step 100 passes](result-legs1-m100-20261114.md) route +24.7 vs parent, counting 63.3 (f17 69.1); direct read cannot score routed types (calls repeat); facing-away 22/12/4" >> $M/MEMORY.md; wc -c $M/MEMORY.md; tail -n 2 $M/MEMORY.md | cut -c1-120