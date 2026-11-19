J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; date -u +%TZ; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; tmux ls | grep -E "tr15|tr16"
cat > $J/prompts/build24l4.md <<'EOPY'
# Codex build 24l4 of lane tree_rebuild: TREE fix on top of 24l3: r1_launch22.validate_removals accepts the pointing K1 held-out removal list as one more pinned list (ORCH RULING 2216Z item 1)

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. Build 24l3 finished there: tree `J/work/tree_r1` (FINAL TREE seal 96ff9a03ae3be43972e060050ab411967e99dc312dc1380fe1c73435bbecebbf, 943 files; read `J/out/BUILD24L3_REPORT.md` first). First copy `J/work/tree_r1` to `J/work/tree_r1_24l3` (untouched; never edit it), then work in `J/work/tree_r1`. Binding prompts: `J/prompts/build24l2.md`, `J/prompts/build24l3.md` and those they name (rules and conditions hold). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 40 minutes.

## Problem
The kit build appended a 13th removal pin (sha256 d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1: 320 pointing row keys in two K1 held-out rooms, scannet/scene0630 and scannet/scene0280; JSONL of row keys built from K1 split 27126674 with the tree's own Rooms.room on provenance.canonical_scene) to cfg['remove_files'] and the sealed `student_pilot/r1_launch22.py` validate_removals refuses `R1_NAMING_REMOVAL_ORDER`: it requires `tuple(actual) == REMOVAL_ORDER` (12 pins, NAMING_REMOVE d1454a44 last) and `actual == launch22.removal_order`. Callers: r1_rooms.py:91, r1_coverage.py:177, r1_routing.py:21.

## Change (smallest; nothing else)
1. Add a module constant `POINTING_K1_REMOVE = 'd21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'` and accept exactly two orders: the existing `REMOVAL_ORDER`, and `REMOVAL_ORDER[:-1] + (POINTING_K1_REMOVE, NAMING_REMOVE)`. Keep every other condition (actual == spec['removal_order'], naming last and once, pinned() of the naming list). Any other 13th sha, any other position, or a duplicate refuses `R1_NAMING_REMOVAL_ORDER` as today.
2. Read every other consumer of `remove_files` or `removal_order` in the tree (position-based indexing, counts, union verification, coverage, room audit, receipts, kit-facing helpers such as verify_union) and say in the report whether each one works unchanged with the 13-list order. If any other place needs a change for the 13-list order to admit, make only that change, with a test, and list it. If a change would alter what is excluded beyond removing these listed keys, or touch scoring, stop and report instead.
3. Say in the report whether `remove_files` is one list for all streams or per stream, and that a list of pointing keys removes nothing from other streams (test it on fixtures: VQA and pose fixture rows unchanged).

## Tests
validate_removals: 12-list order passes; 13-list order with POINTING_K1_REMOVE before naming passes; a different 13th sha refuses; POINTING_K1 after naming refuses; POINTING_K1 twice refuses; spec removal_order differing from actual refuses. With the tree's own Removals on a fixture that holds a pointing row whose key is in a synthetic list with that pin role: the row is removed, the other streams' rows are unchanged. All 24j, 24l, 24n and 24l3 tests still pass; scoped suites as in 24l3 (report pre-existing failures).

## Outputs
`J/out/HOST24L4.patch` (diff against tree_r1_24l3), `J/out/HOST24L4B.patch` (diff against tree_r1_base, 189df6ac), `J/out/TREE24L4_SEAL.json`, `J/out/UNCHANGED24L4.json` (every file's sha256 vs 96ff9a03 tree), `J/out/BUILD24L4_REPORT.md` under 20 lines (line 1: new seal; line 2: consumers checked and any further change), `J/out/tree_rebuild_b24l4_<seal8>.tar` of work/tree_r1 plus the 24l3 and 24l4 J/out reports.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Admission semantics otherwise unchanged.
EOPY
sha256sum $J/prompts/build24l4.md
tmux new -d -s tr16_b24l4 "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $J $J/prompts/build24l4.md --model gpt-6-astra --effort high --label tree_rebuild24l4 --skip-git-check > $J/build24l4_dispatch.log 2>&1"
sleep 15; tmux ls | grep tr16; tail -3 $J/build24l4_dispatch.log
