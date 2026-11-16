<!-- recovered by seal_plan: transcript=71f94277 line=32683 utc=2026-11-14T17:26:50.959Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_NATIVE_PIN_GRAPH_AUDIT.md  -->
# Audit: every hash or identity check a routed-read pilot job performs before its GPU work, against what is actually uploaded

You are an independent auditor from a different model family than the author (a GPT-family lane). A one-GPU job family on the Orchard cluster ("native routed read") has now lost five pilots in a row to packaging faults, each found only on the real node:

1. a run folder that already existed;
2. a gate probe the model was never trained on;
3. a logit tolerance below what 16-bit logits can represent;
4. job 169537: the uploaded code archive still held old bytes of three job files whose pins had moved;
5. job 169589: a second, separate pin of the worker file (inside a "runtime spec" asset) still named the old worker hash, so the bootstrap refused the correctly uploaded worker.

Faults 4 and 5 are the same kind: a file changed, and one of several places that record its hash was not regenerated. The author's local pre-submission check verified the family's code pins against the uploaded code archive but not other embedded pins. Your task is to find every remaining instance before pilot 6, so that pilot 6 is not the detector.

## Material (read-only; all under `/scratch/jjyeung/orch_cd/evalx/work/milestone/` unless a full path is given)

- The current family seal and packet of the failed pilot 5: `native_package_s23_02/seal/FAMILY.json` (family 62a94599), `native_package_s23_02/authorized_advanced_v2/` (BATCH.sh, CONFIG.json, PACKET.json), the local check `native_package_s23_02/LOCAL_INPUT_CHECK_V2.json`.
- The family's source: `native_fix_s23_01/orchard_native/` (`native_job.py`, `native_stage.py`, `native_bootstrap.py`, `native_worker.py`, `native_metrics.py`, `native_launcher.py`, `native_local_check.py`, `native_common.py`, `kernels.py`, and the files beside them) and the reader `native/out2/nomdg.py`.
- The failures' returns and diagnoses: `native_package_s23_01/CAUSE_CONFIRMED.json` (pilot 4) and `native_package_s23_02/pilot5_failure/` (DIAGNOSIS.json, AUTHENTICATED_FAILURE.json, and the returned logs it names).
- Local copies of the uploaded objects: look for an `uploads/` folder under `native_package_s23_02/`, `native_p1_s23_02/`, `native_probe_s23_01/` and `native_fix_s23_01/orchard_native/` (code, geometry, masks, metadata, model, runtime spec, whatever the family's `assets` section lists); FAMILY.json gives each object's name, sha256 and member list. Do not copy anything larger than 100 MB; list archives and read small members in place.

## What to produce

1. **The complete list of checks.** Walk the job's path in execution order, from the first line of BATCH.sh to the worker's first GPU call: the batch script, the job controller, staging of every archive and object, the bootstrap and its entrypoint check, the input-pin validation, the worker's own start-up checks. For every comparison of a hash, size, generation, version string, path or identity, record: the code location (file and line); where the **expected** value comes from (which file or object carries it, and which field); where the **actual** value comes from (which staged file or object); and whether the expected value is a copy of a value that also lives somewhere else (a duplicate pin).
2. **The current truth of each.** Using the local copies of what is uploaded and the current source files, evaluate each check: would it pass today for family 62a94599? Mark every expected value that is stale, and every duplicate pin whose copies disagree. Pilot 5's worker pin in the runtime spec must show up as stale; say what else does.
3. **What regenerates what.** For each file that has changed since the first family seal (the reader, `native_job.py`, `native_metrics.py`, `native_worker.py`, `native_launcher.py`, the new `native_local_check.py`), list every place that records its hash, and say which build step regenerates each place and which are edited by hand or not at all.
4. **What the local check must cover.** State exactly which checks from item 1 the author's permanent local check executes (read `native_local_check.py`), which it cannot (for example anything that needs the production interpreter), and for those the static proof that would stand in (for example: parse the runtime spec, read its entrypoint pin, compare with the staged worker).
5. **Beyond pins.** While walking the path, note anything else that a first real run past the bootstrap would hit and no pilot has yet executed: the report written after the gate, the five geometry captures, the ten item pairs, the publication of the return. Only concrete defects with file and line, not general worries.

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PIN_GRAPH_AUDIT.md`, at most 70 lines: first a one-line verdict (how many checks, how many would fail today, how many duplicate pins); then a table of the checks in execution order (location, expected-from, actual-from, duplicate?, passes today?); then the stale or disagreeing items with the exact fix for each; then items 3 to 5 briefly. Return a summary of at most 10 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_pin_graph/` (private copies, at most 500 MB). No Git commands, no ssh, no network, no GPU, no agents. No agent runs a command that removes files, and the names of such operations must not appear in any shell command text (a local guard blocks those commands and they may not be retried); use your file tools for anything of that kind. Stay on `/scratch`; never search or list `/home` or `/data*`; no recursive search outside the folders named here; do not read files larger than 20 MB into memory. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. At most 8 threads. The author is fixing fault 5 in parallel and may write new folders named `native_package_s23_03` or similar; audit the state described here and note if you see a newer seal. Aim for 25 minutes.
