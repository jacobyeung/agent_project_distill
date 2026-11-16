The adapter regression suite passes 42 tests on CPU: 0 failures, 0 errors, 0 skips. Both kit dry binds pass. `TESTS.log` contains the complete test names and counts. No test loads a model, opens a network connection, starts a GPU job, or reads the run-host frame tree.

Run `/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/test_adapter.py` from this lane. The suite uses the two copied kits in `work/dry_release_cp1` and `work/dry_release_f17`. Temporary fixture directories stay under `work/`; the tests perform no deletion.

Coverage includes the complete 2,136-item partition; 1,536 equal cell memberships; all ordered PLAN anchors; outside-plan and unwithheld-scene refusal; exclusion reasons; all frozen strata and SHA; numeric threshold/zero/nonfinite and MC rules; actual scorer dispatch for all 11 types; prompt equality across both kits; both dry binds; fixed model identity; both-layout PNG receipt loading and corruption/path/missing-file refusal; incomplete-bind and missing-label gates; report counts; and paired room-cluster bootstrap behavior.

The synthetic PNG test creates 32 tiny RGB PNGs, computes real kit pixel hashes, and loads both spread and consecutive-duplicate receipts through `media.load`. It then corrupts a linked PNG and verifies rejection. This is a real loader test, not a stub for missing production frames.

Both dry binds load all 1,536 task rows using their copied kit's `tasks_for`, validate the cell and answer types, and pin every prompt. Both stop before PNG bytes, with 161 missing-label records explicitly recorded. `DRY_BIND_cp1m200.json` and `DRY_BIND_f17.json` are the exported receipts. The AWS `local/bind_vl.py` is not invoked: its thinking variant intentionally rejects non-ReVSI cells, and its remote launch path decodes videos. The custom binder supplies the same evaluator request/data formats directly.

Unexecuted acceptance checks: production PNG bytes, real model weights, GPU inference/parity, CP1 budget continuations, and a real paired report. The revision lane's tests and complete inherited kit suites were not rerun here; this suite checks the adapter boundary on the named baseline copies.
