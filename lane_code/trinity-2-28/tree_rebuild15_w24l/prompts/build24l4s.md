# Codex build 24l4s of lane tree_rebuild: TREE fix on top of 24l4r: the two SHOULD findings of the Cursor re-review of 24l4r (post-condition room resolution)

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. Build 24l4r finished there: tree `J/work/tree_r1` (seal 92fe11f83f9e79234f00ed56521e8ad0b1dd48c80ffc593e9c0f6814610186b9, 944 files; read `J/out/BUILD24L4R_REPORT.md` and `J/out/PROTECTED_ROOMS_API.md` first). The review: `/scratch/jjyeung/orch_n30/tr16_rev24l4r/VERDICT.md` (read it in full). First copy `J/work/tree_r1` to `J/work/tree_r1_24l4r` (untouched; never edit it; check its seal is 92fe11f8), then work in `J/work/tree_r1`. Binding prompts: `J/prompts/build24l4r.md` and those it names. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 40 minutes.

## Change (only in check_protected_rooms and what it calls; API and call contract unchanged)
1. Pointing: a row is protected if ANY of the resolutions the tree uses places it in a protected room: provenance.canonical_scene, Rooms.canonical / provenance.canonical / dataset+scene as Rooms.status reads them, and the withheld check. (a) refuses an admitted row that either resolution places in K1 held-out, R0 or the withheld 80; (b) accepts a listed key only if its source row is protected by at least one resolution. Test: the reviewer's probe (clean canonical_scene, protected by another field) now refuses.
2. VQA: resolve VQA rows with the tree's own VQA authority (`r1_direction_twins` Binding.room with its tiered aliases, as r1_rooms census does at r1_rooms.py:224-237), not strict Rooms only, so the production VQA store (119,375 rows strict Rooms cannot resolve, tests/test_r1_build18.py:39) does not refuse R1_PROTECTED_ROOM_UNRESOLVED:vqa; rows the native VQA authority cannot resolve still refuse. Say in the report exactly which authority each stream uses (pose, vqa, routing, pointing) and that it is the one the tree's own room census uses for that stream.
3. Nothing else. Do not wire the post-condition into native admission (that is a kit binding, ruled separately).

## Tests
Both fixes with failing-before tests on 24l4r; all 24l4r, 24l3, 24n, 24l and 24j tests still pass; scoped suites as before (report pre-existing failures).

## Outputs
`J/out/HOST24L4S.patch` (diff against tree_r1_24l4r), `J/out/HOST24L4SB.patch` (diff against 96ff9a03 at `J/work/tree_r1_24l3`), `J/out/TREE24L4S_SEAL.json`, `J/out/UNCHANGED24L4S.json` (every file's sha256 vs 96ff9a03), updated `J/out/PROTECTED_ROOMS_API.md` copy as `J/out/PROTECTED_ROOMS_API_24L4S.md`, `J/out/BUILD24L4S_REPORT.md` under 15 lines (line 1: new seal), `J/out/tree_rebuild_b24l4s_<seal8>.tar` of work/tree_r1 plus the 24l4r and 24l4s J/out reports.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Admission semantics otherwise unchanged.
