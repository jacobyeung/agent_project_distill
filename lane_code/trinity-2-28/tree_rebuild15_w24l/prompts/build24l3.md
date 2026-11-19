# Codex build 24l3 of lane tree_rebuild: TREE fix on top of 24l2: native re-verification only for the native stager; a stage hook is recorded, not re-verified (ORCH 2157Z)

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. Build 24l2 finished there: tree `J/work/tree_r1` (seal e17fc130870963170e6bc5f4f536ca0c36a7afa272725908afdcaa7ad5dc26eb, 942 files), outputs `J/out/*24LN*` (read `J/out/BUILD24LN_REPORT.md` and `J/out/KIT_WIRING_24LN.md` first). First copy `J/work/tree_r1` to `J/work/tree_r1_24ln` (untouched; never edit it), then work in `J/work/tree_r1`. Binding prompts: `J/prompts/build24l2.md` and those it names (rules and conditions hold). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 35 minutes.

## Ruling (ORCH 2157Z)
24l2 re-verifies hook-staged entries with the native launch_r2.staging checks; the launch kit's hook (`J/in24kr/kit_n_go/b/pl.py`) does not use the native layout, so q refuses `R1_HOST_STAGING_DIFFERS:e:Staging target escaped the input root` (`J/out/KIT_PLAN_PROBE24LN.json`). Change: keep native re-verification exactly as 24l2 built it when the native stager runs (stage is None); when a caller stage hook is passed, do not re-verify with the native layout checks; instead host.json records `stager: "hook"` and `staging_plan_sha256` (the sha256 of the staging plan bytes the request pins, i.e. the pinned `request['staging']` file), and the native-stager branch records `stager: "native"` with the same field. Nothing else in 24l2 changes.

## Tests
Both branches: native stager with wrong bytes still refuses by name; hook stager with the 24k kit's plan shape (use `J/out/KIT_PLAN_PROBE24LN.json`'s plan or a fixture of that shape) passes stage_host and host.json records stager hook and the plan sha; the plan sha in host.json equals the pinned file's sha256. All 24j, 24l and 24n tests still pass; scoped suites as in 24l2 (report pre-existing failures).

## Outputs
`J/out/HOST24L3.patch` (diff against tree_r1_24ln), `J/out/HOST24LN3.patch` (diff against tree_r1_base, 189df6ac), `J/out/TREE24L3_SEAL.json`, `J/out/UNCHANGED24L3.json` (every file's sha256 vs 189df6ac), `J/out/BUILD24L3_REPORT.md` under 20 lines, `J/out/tree_rebuild_b24l3_<seal8>.tar` of work/tree_r1 plus all J/out reports of 24l2 and 24l3.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Admission semantics otherwise unchanged.
