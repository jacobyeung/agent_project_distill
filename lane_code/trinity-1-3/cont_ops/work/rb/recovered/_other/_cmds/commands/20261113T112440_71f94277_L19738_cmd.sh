<!-- recovered by seal_plan: transcript=71f94277 line=19738 utc=2026-11-13T11:24:40.010Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
p="/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/MEMORY.md"
t=open(p).read()
if not t.endswith("\n"): t+="\n"
t+="- **READ FIRST, result 11-13:** [Official VSI-Bench routed](result-vsi-routed-official-20261113.md) abs distance + room size routed around f17: 65.1 strict / 65.4 with fallback vs 63.79; mask setting adds nothing with fallback\n"
open(p,"w").write(t)
print(len(t.encode()))
d="/data2/jjyeung/agent_project_data/distill_design/MASK_PROPOSAL_RECALL_DEVS1_20261112.md"
with open(d,"a") as f:
    f.write("\n## Benchmark read 2026-11-13 (official VSI-Bench 5,130, f17 direct 63.79)\nRouting absolute distance and room size to the programs: 65.14 strict at the frozen setting (+1.35 [+0.57, +2.13]); with fallback to direct for unanswered items 65.43 at baseline proposals and 65.36 at the frozen setting. Absolute distance (834 items): direct 53.38, routed with fallback about 63 (+10 [+6, +13.5]), positive on ScanNet, ARKitScenes and ScanNet++. The frozen dense+aliases setting gains +3.06 [+0.97, +5.19] only in the strict arm and -0.59 [-2.29, +1.04] with fallback: its gain is recall that the fallback already supplies. Status: the question this record asked (does more proposal recall pay on absolute distance) is answered: not once fallback is used; no further proposal-recall work for this type. Record of the read: /scratch/jjyeung/orch_cd/official_reads/ROUTED_ABSDIST_ROOM_VSI5130_20261113.md.\n")
PY