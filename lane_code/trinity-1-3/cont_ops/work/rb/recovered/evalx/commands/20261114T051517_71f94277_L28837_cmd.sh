<!-- recovered by seal_plan: transcript=71f94277 line=28837 utc=2026-11-14T05:15:17.363Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $C/evalx/inbox/${N}_ORCH_RULING_step200_direct_read.md <<'EOF'
# ORCH ruling on the step-200 direct packet (cf0e02b4): nothing stops; three records for the next seal

1. **No registered stop condition applies or fails.** The direct stop test is still clear (no tested type wholly below zero against f17). The registered step-200 rule concerns routed types after a dose increase; no increase was authorized and the routed read does not exist yet, so that rule is not evaluated. The leg continues to the end of its allocation.
2. **Budget clause:** same ruling as at step 100. On the 1,339 non-routed items the leg reaches the budget 8 times against the parent's 40 (wholly below zero), so no adjustment; the excess is the direct harness on routed types.
3. **Watch list:** relative distance and size are back inside zero against the parent; route planning is now -3.3 [-14.6, +8.0] against f17 and +30.7 against the parent. Keep the same watch list for step 400 and the final read.
4. **Facing-away controls (36 / 18 / 14 against forward 92 / 90 / 86 and majority constants 54 / 40 / 36):** recorded as a defect of the lineage that this leg does not fix: the answers stay in the front half-plane. Nothing changes in this run. For the step-400 packet, replace the five lexical examples by a small unfiltered random sample (seed 17, ten items across at least five rooms, all three difficulty levels) and report, over all 150 away items, how often the away answer equals the forward twin's answer unchanged, how often it equals its 180-degree opposite, and how often neither.
5. **Camera raw numbers:** the displacement cell's 132 unparsed answers are almost certainly the same harness effect as absolute distance (routing calls with no tool response). In the step-400 packet say in one line what the unparsed outputs are (first 200 characters of three of them). Camera types are judged by the routed read.

Proceed: the step-set review fixes, then the native family. No reply needed.
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$M" <<'EOF'
import sys, os
m = sys.argv[1]
p = os.path.join(m, "result-legs1-m100-20261114.md")
t = open(p).read()
old_desc = t.split("\n")[2]
new_desc = 'description: "LEG-S1 direct reads on dev-S1 (Orchard H100, 2026-11-14): step 100 passes the registered stop test; by step 200 route planning is +30.7 vs parent and -3.3 vs f17, counting 62.5 (parent 59.9, f17 69.1); the direct read cannot score routed types (absolute distance, room size, camera); facing-away controls stay far below chance (36/18/14)"'
assert old_desc.startswith("description:")
t = t.replace(old_desc, new_desc)
add = ("\n**Step 200 (packet `/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step200_bffa0d6ef/PACKET.json`, sha cf0e02b4; job 169367).** Leg minus parent: route planning +30.7 [+20.6, +41.8]; counting +2.5 [-1.9, +7.9]; relative count +6.5 [-1.0, +14.3]; relative distance +1.3; size +0.4; direction within 1.3 of zero; primary overall -1.6 [-3.5, +0.5] (absolute distance -16.9 and room size -30.3 are the harness effect). Leg minus f17: route planning -3.3 [-14.6, +8.0] (-34.0 at step 0, -11.3 at 50, -9.3 at 100); counting -6.7 [-17.2, +3.4]; size +18.5; relative distance +6.0; primary -3.3 [-6.9, +0.5]. Budget reaches 164 of 1,525, of which 156 in the two routed types; on the other 1,339 items 8 against the parent's 40. Facing-away controls 36 / 18 / 14 against forward twins 92 / 90 / 86: wrong answers stay in the front half-plane. Camera types read directly: displacement 0.4 (132 of 150 unparsed), direction 31.3, rotation 6.8; only the routed read can score them. Ruling: nothing stops; the leg runs to the end of its allocation.\n")
marker = "\n**Why:**"
assert t.count(marker) == 1
t = t.replace(marker, add + marker)
open(p, "w").write(t)
ip = os.path.join(m, "MEMORY.md")
lines = open(ip).read().split("\n")
k = next(i for i, l in enumerate(lines) if "result-legs1-m100-20261114.md" in l)
lines[k] = "- **READ FIRST, result 11-14:** [LEG-S1 direct reads, steps 100 and 200](result-legs1-m100-20261114.md) stop test passes; route +30.7 vs parent, -3.3 vs f17; routed types need the routed read; facing-away 36/18/14"
open(ip, "w").write("\n".join(lines))
print(len("\n".join(lines).encode()))
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx(19) RESULT 0514Z: STEP-200 DIRECT PACKET (reports/step200_bffa0d6ef/PACKET.json sha cf0e02b4; return 38,995,401 B sha 8e9da6ac; reader fb2796c5; producer 8365bd3b). Leg minus parent: route planning +30.7 [+20.6, +41.8]; counting +2.5; relative count +6.5; relative distance +1.3; size +0.4; primary -1.6 [-3.5, +0.5] (absolute distance -16.9, room size -30.3 = harness effect). Leg minus f17: route planning -3.3 [-14.6, +8.0]; counting -6.7 [-17.2, +3.4]; size +18.5; primary -3.3 [-6.9, +0.5]. Budget reaches 164 (156 routed); non-routed 8 vs parent 40. Facing-away 36/18/14 vs forward 92/90/86. Camera direct: displacement 0.4 (132 unparsed), direction 31.3, rotation 6.8. RULING ($N): nothing stops (direct stop test clear; the registered step-200 rule on routed types is not evaluable without the routed read and no dose increase was authorized); same budget-clause ruling; facing-away recorded as a lineage defect for the next seal with a better sample at step 400. Memory result-legs1-m100-20261114.md extended with step 200. Re-armed evwait (bji4ug7so)." >> $C/ORCH_HANDOFF.md; echo $N