# Whole-worker rehearsal

Run outside the Codex sandbox on the same compute node:

```sh
/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/rehearsal/run_whole_worker.sh
```

The command creates a fresh directory under `out/rehearsal/whole/`. It stages local tensor stand-ins, invokes the unchanged checker, starts separate checkpoint processes, publishes the proof and canary with verified local readback, runs the candidate subset, merges and admits the result, archives it, fetches it locally, and invokes the unchanged report. A namespace failure stops the command; it does not retry.

The command calls the same phase coordinator as production (`../guard_kit/worker.py:coordinate`). Stage-failure and proof-failure tests exercise its terminal receipt and return paths (`../PROCESS_TESTS.json`). The namespace, tiny checker setup and shared-asset adapters remain rehearsal-specific.

The sandbox attempt stopped before checkpoint execution (`whole/sandbox/RESULT.json`, `whole/sandbox/namespace.stderr`). The tensor checker passed independently through a read-only path adapter (`whole/TENSOR_CHECKS.json`). Metadata restoration passed through the same kind of adapter (`../RESTORATION_TEST.json`). Neither result establishes a whole-worker pass.

The candidate uses the supplied milestone metadata (`whole/sandbox/fixture/PREPARATION.json`). Each tiny artifact changes only `heads.sha256` and `full_weights.sha256`; those fields bind actual tiny files. All other artifact fields, including trained-group fingerprints, remain identical. The C8r model boundary bypasses tensor loading, so those retained fingerprints are not validated against tiny model tensors. `cpu_boundary.py` is read unchanged from the supplied C8r rehearsal; the wrapper supplies its local roots and replaces proof token generation with the pinned historical tokens. It does not establish GPU backend identity.

The worker configuration and a local-transport projection are written to each fixture directory. `PREPARATION.json` records their differences and all additional boundaries. The shared production objects use the supplied extracted read-only assets. The rehearsal does not re-run production cloud staging or allocation admission; therefore a pass would not prove that the entire production packet differs only in transport.

The candidate subset contains the sealed canary plus proof-list items in the accepted order, for a total of twenty (`inside_whole.py`, emitted `candidate_BOUNDARY.json`). The unchanged full-list report must refuse this incomplete result. The command records its refusal rather than filling unexecuted items. The separate full recorded-row report fixture passes against itself (`../rehearsal/records_pass/RESULT.json`); it has no model decode.

Run the proof-mismatch variant outside the sandbox:

```sh
/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/rehearsal/run_whole_worker.sh --mismatch
```

A valid mismatch result publishes `PROOF.json` with failure and creates no candidate canary or arm. The namespace-free recorded-row mismatch already passes (`records_mismatch/RESULT.json`); checkpoint-process failure and publication-before-tail tests pass separately (`../PROCESS_TESTS.json`).

The operator must inspect `RESULT.json`, both phase logs, `PROOF.json`, `CANARY.json`, `IN_JOB_ADMISSION.json`, and publication readbacks. This command is runnable but its namespace-dependent portion is unexecuted and may reveal further integration defects.
