The copier path passes its synthetic test; the four-rank rehearsal remains unrun.
Cause: the fixture used a 0775 sessions directory, a 0664 empty sessions file, and the build24f copier instead of the shipped module.
`rehearsal_copier5.py` imports the supplied kit’s `b/pc.py`, selected from `job.sh` → `b/pc.sh`; decoded `k/j.json` has no separate copier launcher.
The fixture supplies 0700/0600 sessions for every named part, maps m2 to m100, and uses `live_tests.WRITER` locally; only `n_root` is substituted in memory.
PASS: one synthetic `pass_once()` produced `rehearsal5/copier_synthetic/target/o/rehearsal/live/gcs_m2.done`; marker/archive hashes and all four local parts match (`copier_synthetic/RESULT.json`).
PASS: preparation against the selected kit regenerates source/code seals, host receipt, continuation/preparation pins and v.json; native admission, prepared(), component binding and missing-host/review refusals pass (`rehearsal5/PREPARED.json`, `prepare.log`).
The host is an explicit CPU stand-in; the kit’s unmodified h.py consumes its pin. Model, donor, stores, indices and audit are reused read-only; native mode-q was not rerun.
`rehearsal5/SETUP_VALIDATION.json` records kit/module hashes, syntax, writable mounts and disk use; `FIXTURE_DIFF.json.build24fr4` records changed fixture fields.
`out/BUILD24K_REPORT.md` was present at the initial check, so go_rehearsal5.sh was not run; localhost TCP was not attempted. All nine new-run rows remain NOT PROVED in rehearsal5/CHECK.json.
Lane command: `cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24 && nice -n 10 bash work/build24f/go_rehearsal5.sh out/kit_n_go`.
The launcher defaults to out/kit_n_go, runs fresh/budget/resume once, and stops on kit/report changes, resource limits or failure; existing attempts are preserved.
