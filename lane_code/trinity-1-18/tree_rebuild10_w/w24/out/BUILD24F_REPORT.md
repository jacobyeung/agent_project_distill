BUILD24F PACKAGED FOR REVIEW; four-rank training awaits the external CPU script. Normal kits remain GO=false.
Tree: 57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7. The only tree change is launch_r2/persistence.py (out/PERSIST24F.patch).
Kit n: 89ec4951f4a075fd499a8b95e012857effe42fe7b38f3b0d25fdc7ddd991efeb; kit q: 3d14429690aae6ebd1dc569010802487d37944368a4e6b78a9e016b69717d6a8; GO: fb7a6d462f59b2f5fe2085c6bce0bbe751b8250c173861cb1203d85ddd1f16b6.
24e is delivered in out/DELIVERY_24E.json with its report, upload diff and immutable package.
N requests advanced, 4 GPUs, 48 CPUs, 800G and 24 hours; k/a.json and BUILD.json match job.sh.
CPU-stage OMP/MKL/OpenBLAS limits are 48 in job.sh and tk_env; the four training workers use 8 each.
LIMIT: native production_proof calls s1_admission with threads=8, and admission caps it at 16. Raising that native stage to 48 is outside the allowed tree/admission changes.
Kit q only receives the new sealed source and source pins; its 8-CPU/192G/12-hour proof request is unchanged.
TK_JOB_START is exported before staging and explicitly enters bwrap. The launcher preserves it; CPU view prints TK_JOB_START=1795111111 (RUNTIME_TESTS.json).
Two batch-shell workers independently publish small evidence every 600 s and inspect export markers every 10 s; EXIT/TERM/USR1 perform a final copy.
The supplied decoded runtime contains tk_step but no tk_persist_small; b/pc.sh and b/pc.py provide the requested batch-shell persistence.
SBATCH --signal=B:TERM@600 targets the batch shell. The copier reads the resolver's actual training output, Q_ROOT/r.
Small publications include t/q/h/rooms tails, metrics, attempt/run JSON, .steps and marker names/sizes/SHA-256; they never read weights for their listing.
A shared 50 MB copy cap includes a 40 MB total log-tail budget. TERM and concurrent-upload tests pass (LIVE_TESTS.json, LIVE_REPEAT.json, RUNTIME_TESTS.json).
Each immutable m export uses the unchanged gcsput.py split writer, four parts/four workers, and a verified object/bytes/SHA-256 done marker.
Global project claims reserve fixed milestone objects and mstop/mstopB/mstopC once. Failed sends retry on the next pass; native archives are reused without duplicate in-flight tars.
Missing sessions produce 'export not uploaded: no sessions' and retain the node-local tar. No session URL or Google credential was added.
The exit path copies only the latest completed stop checkpoint to n_ck/<jobid> after size+50 GiB admission; insufficient space uses ckstop GCS or records that it remains local.
Two-hourly checkpoints stay local. Small-evidence GCS mirroring remains pending the orchestrator's credential ruling.
Persistence permits the local path only for r1_training present and r2_persistence absent; explicit persistence bindings retain their upload behavior and every invalid binding still refuses.
Local receipts retain source/archive pins, parts=[], durable=false and project_required=false. Tests prove identical export bytes and receipt pins against a stub uploader (PERSISTENCE_TESTS.json).
All eight changed statements execute; local checkpoint/export, configured upload, invalid bindings, native-state and disk refusals pass (COVERAGE.json).
Decoded scans pass for q/n/GO; guard (17 per kit), kit, naming, resolver, launch, selection-refresh and room-pin suites pass (FINAL_VALIDATION.json).
The hidden-path q/n runs pass staging, guard, room authority/audit and publication; their canaries stop at missing production routing payload a67a3f6f489031d4.jsonl.gz (SEQUENCE.json).
Synthetic canary: ADMIT; room audit, v.json producer and fixture gate checks pass. No distributed optimizer step is claimed in this sandbox.
Run work/build24f/go_rehearsal.sh outside the sandbox: nice 10, OMP 8, gloo, 4 CPU ranks, aggregate RSS guard 19 GB, output work/build24f/rehearsal.
REHEARSAL_OVERRIDES.json and FIXTURE_DIFF.json enumerate fixture differences. REHEARSAL_PATHS.md lists native calls, refusals, outputs and the one-line-per-path checker.
The script is designed to test step-1 persistence, a milestone export/copier done marker, timed checkpoint, allocation-age self-stop with checkpoint/export, and latest resume for one more step; these distributed paths remain unproved here.
Upload delta after 24e: 22 files, 6662365 bytes; stream root work/build24f/upload; names out/UPLOADS_24F.list. The GO-only three-file diff is not authorized for upload.
Config, admission, legality, trained groups, export contents, removals, opener rows, step-544 lineage, resolver identities and DEFERRED checks are unchanged (INVARIANTS.json).
The card records cadence and accepted loss: node death between exports restarts from the last export with a fresh optimizer.
Package SHA-256, byte count, verified member seal and workspace growth are in out/DELIVERY_24F.json. Existing packages remain unchanged; no upload or submission ran.
Evidence paths without a prefix are under work/build24f. Superseded files remain in attic; compressed fixture evidence is lossless and indexed by COMPRESSED_EVIDENCE.json.
