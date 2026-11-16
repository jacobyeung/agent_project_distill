<!-- recovered by seal_plan: transcript=71f94277 line=18185 utc=2026-11-13T08:22:15.266Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
p="/data2/jjyeung/agent_project_data/distill_design/INDEX.md"
t=open(p).read()
a="| MASK_PROPOSAL_RECALL_DEVS1_20261112.md | variants running on trinity-1-18 (evalx) |"
b="| MASK_PROPOSAL_RECALL_DEVS1_20261112.md | DONE: setting FROZEN 2026-11-13 for absolute distance and room size (dense text pass + aliases, kit_combo3 b3fa05c6; dev-S1 abs distance 46.9 -> 56.2, +9.3 [+4.2, +14.9], gain on ScanNet++; counting -8.3, stays direct; cross-family review closed); frozen file /scratch/jjyeung/orch_cd/official_reads/FUSION_PROPOSAL_SETTING_FROZEN_VSI_20261113.md; benchmark cache on 288 VSI-Bench scenes next |"
assert t.count(a)==1
open(p,"w").write(t.replace(a,b))
r="/data2/jjyeung/agent_project_data/distill_design/MASK_PROPOSAL_RECALL_DEVS1_20261112.md"
with open(r,"a") as f:
    f.write("\n## Status 2026-11-13: setting frozen\nThe variant dense_aliases (dense text pass at joint floor 0.05 and cap 30, plus the frozen alias prompts, merged at IoU above 0.95) is frozen for the routed types absolute distance and room size: `/scratch/jjyeung/orch_cd/official_reads/FUSION_PROPOSAL_SETTING_FROZEN_VSI_20261113.md`, kit_combo3 tar sha256 b3fa05c6. Evidence on dev-S1: absolute distance 46.93 to 56.20, +9.27 [+4.16, +14.90] (28 items fixed, 8 broken); the gain sits on ScanNet++ v2 (+17.3), ScanNet does not move (-0.7); counting falls 8.3 because the selector accepts fewer candidates, so counting stays direct. Rejected: dense_link05 (counting collapses), tiles and dense_tiles (smaller gain), student pointing and grid proposals for the never-proposed objects (15/81 and 22/81 recovered). Might not hold: the interval is not adjusted for the choice among six variants; we would notice on the benchmark read per dataset (ScanNet++ first). Review: `/scratch/jjyeung/orch_cd/combo2_review/REVIEW_VERDICT.md` (cross-family; fixes closed with 11 tests).\n")
print("ok")
PY