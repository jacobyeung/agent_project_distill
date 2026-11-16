# Whole-worker CPU rehearsal

The operator reports a passing CPU fixture at `out/rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json`. It covers stage, prepare, proof, canary, native_subset, merge, admit, publish, fetch and report. The proof passes 20/20 comparisons; the unchanged report refuses the 20-item fixture with return code 3, as designed (same `RESULT.json`; `OPERATOR_EVIDENCE_G3.json`). G3 records this supplied evidence without reading or modifying `out/rehearsal/whole/` and does not rerun the namespace worker.

Run this command outside the Codex sandbox on the same compute node:

```sh
/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/rehearsal/run_whole_worker.sh
```

The launcher uses `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, `nice -n 10`, and one thread per numerical library. It creates a fresh operator run under `out/rehearsal/whole/`. A namespace failure stops the command; it does not retry.

`run_whole_worker.py:split_mounts` supports bwrap 0.4.0 by splitting directory binds into `--dir` and per-child binds along later mount paths. This lets bwrap create nested mountpoints without writing inside a read-only bind. This adapter stays outside the production code tar (`../CODE_MANIFEST.json`).

`inside_whole.py` explicitly prepends `/scratch/jjyeung/orch_n30/b01_d0guard/work/tvoverlay3` to `sys.path`. The p1cpu environment lacks torchvision, which the Qwen3VL video processor needs. The operator supplied torchvision `0.26.0+cpu` from `/scratch/jjyeung/orch_n30/b01_d0guard/work/whl/torchvision-0.26.0+cpu-cp312-cp312-manylinux_2_28_x86_64.whl`, SHA256 `cf547dc0975eb40bc3249be4ccbeb736597d2c3ece305b1c4e5b7a5dd7363567` (`OPERATOR_EVIDENCE_G3.json`). G3 did not read or install that wheel. The proof `generate` stand-in accepts and forwards `*args`, including the caller's fifth positional argument. These changes stay outside the production code tar.

The command shares the production phase coordinator (`../guard_kit/worker.py:coordinate`). It stages tiny local exports, invokes the unchanged checker, starts separate checkpoint processes, publishes proof and canary receipts with local readback, reads the candidate subset, merges and admits it, archives and fetches the return, and invokes the unchanged report. Production merge compares canonical JSON digests and then uses journal rows; differing content refuses with `MERGE_DIFF.json` (`../guard_kit/admission.py`, `../G2_TESTS.json`).

The fixture cannot establish real tensor restoration, GPU parity or token identity. Each tiny artifact re-derives only `heads.sha256` and `full_weights.sha256`; other artifact fields retain the supplied metadata values. Model boundaries bypass actual tensor loading, so retained trained-group fingerprints do not validate tiny tensors. The proof substitutes pinned historical tokens. The configuration projections and boundary declarations belong to each operator run's `PREPARATION.json` and phase `BOUNDARY.json` files. Shared pre-staged assets and allocation boundaries also prevent a claim that a full production packet was tested with transport alone changed.

The candidate subset preserves the sealed canary and fills from the proof list in accepted order (`inside_whole.py`). The report's incomplete-read refusal is expected; no unexecuted items are filled. The separate full recorded-row fixture at `records_pass/RESULT.json` has no model decode.

Run the proof-mismatch variant outside the sandbox:

```sh
/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/rehearsal/run_whole_worker.sh --mismatch
```

A valid mismatch publishes a failed `PROOF.json` and creates no candidate canary or arm. The supplied whole-worker pass does not establish this variant. Namespace-free mismatch evidence remains at `records_mismatch/RESULT.json`; process failure and receipt-ordering tests are indexed in `../PROCESS_TESTS.json`.

Inspect the run's `RESULT.json`, phase logs, `PROOF.json`, `CANARY.json`, `IN_JOB_ADMISSION.json` and publication readbacks. The CPU-fixture blocker is closed; real runtime validation and production authority remain required (`../RELEASE_BLOCKERS.json`).
