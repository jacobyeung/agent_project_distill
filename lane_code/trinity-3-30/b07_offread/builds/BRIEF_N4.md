# Build N4 + R2: fix the build N review findings 1-6 and the naming rule in builds N and R (one-shot Codex build)

You run once on trinity-3-30; nobody answers questions while you run. Write source, docs and final evidence only
inside `/scratch/jjyeung/orch_n30/b07_offread/builds/N/` and `/scratch/jjyeung/orch_n30/b07_offread/builds/R/`,
and at most 100 MB of new bytes there in total (the node's /scratch is at its floor): every pytest basetemp,
rehearsal, fixture run, packet build and other scratch output goes under `/dev/shm/b07_n4/<fresh name>`
(RAM disk; keep it under 4 GB in total; copy only small logs and JSON evidence back). No ssh, network, Git,
GPU, Slurm or Orchard command; no deletion (write new versions; keep previous archives under new names
inside the 100 MB budget, or record their sha256 only if they would exceed it); no recursive search of /home
or /data*; Python `/scratch/jjyeung/envs/p1cpu/bin/python -B`; never open a benchmark answer or score.
Read first: `builds/N/out/NATIVE_KIT_READY.md`, `builds/N/RUN.md`, `builds/N/DIFF.md`, `builds/R/out/REBIND_READY.md`,
`builds/R/RUN.md`, and the verdict
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offnative/REVIEW_VERDICT_OFFNATIVE.md`.
offkit (`/scratch/jjyeung/orch_n30/b07_offread/kit/offkit`) is read-only for you.

## Gate
Copy the reviewer's tests
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offnative/review_offnative_tests/test_review_offnative.py`
into `builds/N/kit/tests/` (5 cases, all failing now). Every one must pass at the end, with the whole N suite
(`"$PY" -B -m pytest -p no:cacheprovider kit/tests --basetemp=/dev/shm/b07_n4/<fresh> -q`), the whole R suite,
all CPU worker fixtures and rehearsals, and R's exact reproduction of 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4].

## Fixes (orchestrator order: all six; no exemption)
1. ReVSI model prompt: the model keeps the 32-frame clip's own indices 0..31, fps and total frame count
   exactly as the direct kit gives them; only the geometry manifest carries the dense 64-frame slots
   (give V1 validate_dense a geometry-only capture). Check the e2e payload and b04's loaded entry the same way.
   Add a test that the model-facing prompt bytes of a ReVSI item equal the direct kit's prompt bytes.
2. Unserved decodes (both secondary arms) use the registered budget: DECODE_BUDGET 2048 + 64 with the same
   ThinkingBudget guard as the primary.
3. Reduced proof is harness-only for distance; e2e distance items stay "reported" in every mode (b04 changes
   them by design). Fix the builder test that asserts the opposite.
4. The 170056 mask cache is lost (orchestrator ruling). In reduced mode the harness proof never serves a
   distance item from a missing cache: the five distance items become "reported" (token, call and answer
   equality checked where the decode reaches them; no served-response requirement), camera items stay
   required. Docs say exactly what the reduced proof no longer checks.
5. Naming rule (AGENTS.md): no project, benchmark, dataset, model or method word anywhere on Orchard: sbatch
   line, environment variable names and values, job script, every in-job extracted path and file name, log
   lines. Rename `OFFNATIVE_*` env vars, `--export=...` contents, and every packed member path
   (offnative/, d/01/kit/revsi/, out/REVSI_*, out/VSI_*, work/runtime/revsi_media, student_pilot, and the like)
   to opaque names, with the meaning kept in a Trinity-side map. Apply the same to build R: its packed paths
   (`kit/vsi/`, `kit/revsi/`, inherited names listed in `builds/R/out/ORCHARD_NAMES.md` /
   `INHERITED_NAMES.json`) become opaque inside the packet; bytes of the accepted reader, scorer and items
   stay identical, only their paths change; R's reproduction must still be exact. Extend both kits' packed-byte
   name scans to the decoded member paths, env and sbatch line, and test them.
6. VSI-Bench harness sharding: split the read across K jobs (each its own id shard, journal and return; the
   merge already checks the union) so each shard fits the 6-hour limit with the 600 s reserve, K computed from
   SIZING.md's measured rates; a shard that hits the cutoff returns what it finished and its missing ids, never
   loses finished items. Test with a fixture of 3 shards, one cut off.
7. Fold in the 288 VSI-Bench media sizes from
   `/scratch/jjyeung/orch_n30/b07_offread/work/VSI_MEDIA_SIZES.json` (all exist on Orchard; sha verified in-job).
   If `/scratch/jjyeung/orch_n30/b07_offread/work/stage_rv/A2_RESULT.json` exists, fold its 604 clip sha256/bytes
   into the ReVSI media manifest and record its pixel check; else leave hashes pending.

## Deliver
Rebuild R packages and N code.tar with all manifests, pins (N's R snapshot refreshed deliberately with its
diff recorded), `SHIP_SHA256SUMS`; update both readiness reports (first sentence: READY / NOT READY per
benchmark x reader), RUN.md, DIFF.md, OPEN_INPUTS.md. Nothing submitted or uploaded. Final message under
10 lines: hashes and test counts, including the reviewer's 5.
