Same-package routed resume is not supported by the sealed D payload.
`orchard_h10/job.py:80–97` restores only `metadata/IDENTITY.json` and `metadata/journals/*`.
`a/6.py:prepare` dispatches under `metadata/reads/0`; its journals are `metadata/reads/0/metadata/journals/3/0/*`.
B5's real return uses the same nesting (type 4). Restore accepts its own plan but restores zero journals.
A synthetic D partial also restores its outer identity and zero journals. B5 with D's plan is rejected.
Pointing D's `a/1.json.resume` at its archive repeats completed items; do not resubmit it. Fixing restore changes the payload/pins and requires a new plan/package; moving journals alone does not fix operator output paths.

Parent files and guards
No parent package file, receipt, submission marker, or return is changed by this implementation.
`a/4.py` normally writes `resume=None`; a resume specification would be `{path, bytes, sha256}` with an absolute Orchard archive path.
The runner hashes inputs excluding `resume` (`job.py:191`), but `a/c/CPU.json.inputs` binds the raw `a/1.json` SHA256.
Changing that entry invalidates the CPU receipt. Rewriting its digest is not a CPU check.
`o_sub_D.sh` also rejects existing `a/8.txt`; `o_cpu_D.sh` rejects existing `a/4.txt` or `a/c`. Leave those guards intact.
Neither a fresh CPU receipt nor bypassing a duplicate marker repairs the routed-journal mismatch.

Implemented continuation
`make_items_remainder.py` authenticates EXIT/RETURN_RECEIPT, archive SHA/size, package token plus job suffix, plan, operator, inputs, export, settings, journals and summary.
It selects only IDs without a complete committed row, rejects duplicate IDs and incomplete JSONL tails, and preserves unfinished rows byte-for-value, order, answers, captures and twin IDs.
The manifest embeds the validated full parent manifest and partial-return provenance; a completed twin may be absent from the remainder.
`dbuild/build_d.py` is a workspace copy of the supplied builder adapted for remainder counts, capture bounds, timing and nonempty rehearsal sets; the upstream directory is untouched.
It binds a fresh token, plan, payload, member hashes and embedded batch operator. The export binding must equal the parent's.
The validator extension is confined to `h1eval/dist580.py`; the reader, scorer, mapper and other evaluator files remain unchanged from D.
`build_remainder.py` stages the builder's delivery plus placement/fill helpers and adapted CPU/submission guards; it stops without placement or submission.
Fill the fresh package normally: its `a/1.json.resume` remains None. Reuse only authenticated export parts/preparation for the same step.
The fresh fill creates `a/1.json`, `a/export.json`, preparation archive `a/6`, `a/e/*`, `a/10.json` and successful `a/1.txt`; dry resolution and `3.py check` run again.
Then run the fresh CPU allocation to create its own `a/c/*` receipt, memory proof, full-reader rehearsal and bundle/entry-sequence proofs.
Before any later GPU submission, retain receipt/input/plan/operator/batch checks, dynamic rehearsal IDs, memory bound, duplicate markers, general-queue emptiness, pool limit and `3.py check --gpus 1 --time "$T"`.
Use the new build's sealed T (at most 04:00:00); it need not equal the parent's T. No old CPU receipt is reusable.

Commands (Python 3.6 stdlib; replace uppercase paths; use fresh scratch/stage destinations)
`/usr/bin/python3 -B make_items_remainder.py --items FULL_D_ITEMS --package PARENT_PACKAGE --archive PARTIAL_TGZ --exit EXIT_JSON --receipt RETURN_RECEIPT_JSON --work SCRATCH_UNPACK --out REMAINDER_JSON`
`/usr/bin/python3 -B build_remainder.py --stage NEW_STAGE --source AUTHENTICATED_B5_1TGZ --source-sha B5_SHA256 --items REMAINDER_JSON --binding dbuild/bind_D544.json --time 03:30:00`
On Orchard, KROOT defaults to `/project/community/jjyeung/okh7`; local builds must set KROOT under `/dev/shm/c18r`.
Placement/fill uses `REUSE_PARTS_FROM=OLD_PACKAGE/a/e /usr/bin/python3 -B NEW_STAGE/place_fill_d.py NEW_STAGE`; export STEP-appropriate preparation paths if needed.
After fill, export P=NEW_PACKAGE and T=SEALED_TIME, run `bash NEW_STAGE/o_cpu_D.sh`, await success, and use the staged `o_sub_D.sh` only when ready to submit.
For D@200, select its own partial return and `dbuild/bind_D200.json`; never reuse D544's completed-ID list or export binding.

Scoring and pairing
`score_d.py --spec SCORE_SPEC.json --work FRESH_SCRATCH --out SCORES.json` authenticates both publications and merges disjoint completed IDs.
`SCORE_SPEC.example.json` lists the required absolute paths. Add a `compare` group with the same fields for the other step.
Use trusted package directories (including 0.tgz), or BUILD.json files containing evaluator_files; the older D BUILD.json alone lacks that inventory for merging.
Each segment must match its own item hash, plan and operator; different plans/tokens are required. Only the verified subset-validator evaluator hash change is allowed.
Export binding, settings, artifact, reader, parity and maker hashes must match within a merge. D200 and D544 are separate merged runs.
Reworded/twin differences pair reciprocal IDs even across allocations; cross-step differences pair identical completed IDs. Both resample room_key with seed 17 and 10,000 draws.
Missing items never become zero scores. Planned call-rate denominators remain 580; paired counts include only available pairs.
Allocation-local memo state and loading/timing restart; this is a continuation of item coverage, not same-plan execution or a continuous timing measurement.

Finding the published partial on Orchard
The pool path is `<plan.pool>/<package-token><job-id-as-8-hex>/result.tar.gz`, alongside `EXIT.json` and `RETURN_RECEIPT.json` (B5/fetch_return.py).
For job 172957: `/project/community/jjyeung/okh7/ae71c903/d00c03dcc685e0002a39d/result.tar.gz`.
Wait for a verified pool receipt; a partial can have `complete=false,status=FAILED` while `archive_complete=true`. A killed job is not guaranteed to publish journals.
Run the package's `3.py fetch --return-token FULL_RETURN_TOKEN --out FRESH_DEST` after publication, or use the three pool files directly on Orchard.
If resume were supported, RET could point at that persistent pool archive; it must remain readable for staging, not live only in allocation-local /tmp or on Trinity.

Validation and limits
`/usr/bin/python3 -B test_remainder.py --work /dev/shm/c18r/test1` passed; `TEST_RESULTS.json` records real B5 restore behavior and synthetic D evidence.
Tests built full D544 and a 250-item remainder from authenticated B5 member bytes, checked sealed bundle/count/memory bindings, and merged 330+250 into 580 rows and 290 pairs.
Ten rejection tests cover plan mismatch, edited subsets, duplicate IDs, completed runs, mixed exports, truncated journals, wrong token and changed serving code; singleton selection also passed.
Production D partial bytes were not supplied. The built continuation is a synthetic integration artifact under `/dev/shm/c18r/test1`, not a production missing-ID selection.
No Orchard restore, CPU allocation, model loading or GPU run was performed. No SSH, network, Git or deletion operation ran.
