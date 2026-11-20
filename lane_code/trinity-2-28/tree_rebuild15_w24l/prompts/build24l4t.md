# Codex build 24l4t of lane tree_rebuild: TREE fix on top of 24l4s: the MUST of the Cursor short re-check of 24l4s (pointing fail-open on an unresolvable canonical_scene)

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. Build 24l4s finished there: tree `J/work/tree_r1` (seal dd522bb92a7005e63130d40e9947258fda0c0196f533fb9d9677a1a0a7981781, 945 files; read `J/out/BUILD24L4S_REPORT.md` and `J/out/PROTECTED_ROOMS_API_24L4S.md` first). The review: `/scratch/jjyeung/orch_n30/tr16_rev24l4s/VERDICT.md` (read it in full). First copy `J/work/tree_r1` to `J/work/tree_r1_24l4s` (untouched; never edit it; check its seal is dd522bb9), then work in `J/work/tree_r1`. Binding prompts: `J/prompts/build24l4s.md` and those it names. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 35 minutes.

## Change (only in check_protected_rooms / its pointing resolution; API and call contract unchanged)
1. Pointing: when a row carries a canonical_scene (provenance.canonical_scene or the field the 24l4s code reads) and Rooms.room raises on it and the withheld check finds no hit, the row refuses `R1_PROTECTED_ROOM_UNRESOLVED:pointing`, whether or not the ordinary Rooms resolution on the other fields is clean (restores 24l4r's refusal, keeps 24l4s's SHOULD a fix). For a listed key the same row is not accepted as protected (a list key must resolve to a protected room by at least one resolution and must not carry an unresolvable canonical_scene).
2. Tests: the reviewer's cases ('ScanNet/scene0001_02', 'scannet/', 'd1/opaque', 'unknown/token' as canonical_scene paired with a clean ordinary resolution) refuse UNRESOLVED:pointing on 24l4t and are admitted on 24l4s (failing-before). Re-run the reviewer's described fuzz idea in a test: on random rows of all four streams, 24l4t never admits a row that 24l4r or 24l4s refuses.
3. Nothing else. Do not wire the post-condition into native admission.

## Tests
All 24l4s, 24l4r, 24l3, 24n, 24l and 24j tests still pass; scoped suites as before (report pre-existing failures).

## Outputs
`J/out/HOST24L4T.patch` (diff against tree_r1_24l4s), `J/out/HOST24L4TR.patch` (diff against tree_r1_24l4r), `J/out/HOST24L4TB.patch` (diff against 96ff9a03 at `J/work/tree_r1_24l3`), `J/out/TREE24L4T_SEAL.json`, `J/out/UNCHANGED24L4T.json` (every file's sha256 vs 96ff9a03), `J/out/PROTECTED_ROOMS_API_24L4T.md`, `J/out/BUILD24L4T_REPORT.md` under 15 lines (line 1: new seal), `J/out/tree_rebuild_b24l4t_<seal8>.tar` of work/tree_r1 plus the 24l4r, 24l4s and 24l4t J/out reports.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Admission semantics otherwise unchanged.
