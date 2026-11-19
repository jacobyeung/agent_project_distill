# Codex build 24l2 of lane tree_rebuild: finish TREE build 24l (its first run died at "model at capacity") and do TREE build 24n in the same tree, one patch

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. Two prompts bind you and you do both: `J/prompts/build24l.md` (read it whole) and `J/prompts/build24n.md` (read it whole), with the changes below. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 80 minutes.

## State
- The first 24l run (label tree_rebuild24l) died after partial work: `J/work/tree_r1` differs from `J/work/tree_r1_base` (seal 189df6ac, untouched) in launch_r1/entry.py, launch_r1/production_proof.py and a new tests/test_host24l.py; `J/out/` holds BEFORE24L.json, focused24l.json/.log. Read them; keep what is correct and complete, redo what is not. Do not trust any of it without rerunning its tests.
- build24n.md's base copy `tree_r1_24l` is NOT made: there is one base, `J/work/tree_r1_base` (189df6ac), and one patch for both builds.

## Added by the orchestrator (ORCH GO 2128Z, binding for the 24n part)
1. Comparing by hash is safe only where the bytes at the localised path are known to have that hash. For each comparison you change, show (file:line) where the staged file's sha256 is verified before the handover reads it, and add a test in which the localised path holds different bytes under the same stated sha256: it must refuse.
2. Change only path-only mismatches, each with its own test (same hash at another path passes; another hash refuses; everything else unchanged). List in the report EVERY whole-pin comparison on the q and u.py path, changed or not.

## Outputs (replace both prompts' output lists)
`J/out/HOST24LN.patch` (diff against tree_r1_base), `J/out/TREE24LN_SEAL.json` (seal by `student_pilot.source_seal.inventory` + `p3_provenance.digest`, file count), `J/out/UNCHANGED24LN.json` (every file's sha256 before and after), `J/out/ROUTING_DIGEST_STABILITY.json` (24l item 5), `J/out/PIN_COMPARISONS_24N.md` (24n item 2 table), `J/out/KIT_WIRING_24LN.md` (kit edits needed beyond 24k's wiring; expected none except the new tree tar and seals), `J/out/BUILD24LN_REPORT.md` under 40 lines (24l part, 24n part, tests, pre-existing failures), and `J/out/tree_rebuild_b24ln_<seal8>.tar` of work/tree_r1 plus those outputs.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Admission semantics otherwise unchanged (both prompts' conditions).
