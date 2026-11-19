D builds and local checks passed for steps 200 and 544. Nothing was submitted.
The measured budget does not fit the requested four-hour cap; both BUILD.json files explicitly report `budget_fits=false`.

Files
- `make_items_d.py` builds a canonical h1-items-v1 manifest from a list or an object containing `items`.
- `build_d.py` takes STAGE_DIR SOURCE_1TGZ SOURCE_SHA256 ITEMS_JSON BINDING_JSON; KROOT overrides the delivery root.
- `build_support.py` reuses build_r10's archive, replacement, embedded-bundle, and wrap_batch functions verbatim.
- `bind_D200.json`, `bind_D544.json`, and `TIMING_D.json` hold export pins, ordered part pins, and timing evidence.
- `o_build_D.sh` embeds the delivered items, builder, both bindings, and helpers; STEP selects 200 or 544.
- `o_place_fill_D.sh`, `place_fill_d.py`, and `dryres_d.py` place, verify, pull once or reuse, fill, and check without submitting.
- `score_d.py` scores fetched returns; `test_d.py`, `check_release_d.py`, and `generate_scripts_d.py` reproduce local checks and script generation.

Items and required payload changes
- The embedded source is dist_diag/R0_HELDOUT_EVAL_V1.json, SHA256 d98c9efbc1648e535630fb503c29d07d9371becb823c3a09860268389541f729.
- `/dev/shm/c18d/items/dist580.json` has SHA256 ff9795a886be8173f67ca3bba9bc5271fde5c6f35a58855478e29965b93063bb.
- D contains 290 reworded items and 290 original twins, with reciprocal twin IDs and exactly 98 R0-dev rooms.
- Reworded units are m=73, ft=73, in=72, cm=72; all 290 twins use metres. No dev-S1 item is admitted.
- Capture fields come from the R0-dev room item; frame indices must match before copying. The 32 paths remain pinned to B5 captures.
- Sets are R0-dev-reworded, R0-dev-twin, and their union R0-dev; development_only=true and fitting_permitted=false.
- B5's loader rejects an unknown R0 manifest name and its mapper rejects new IDs. D therefore adds h1eval/dist580.py and narrow dispatch branches in h1eval/items.py and h1eval/h10/parity_adapter.py.
- The added validator enforces membership, twins, units, frames and hashes. The read contract permits only tower/none/object_abs_distance.
- The mapper uses B5's 98 pinned captures and preserves each item answer, including rounded converted answers, for output.scores.answer.
- Payload changes are exactly those three Python files, new items/dist580.json, and 9.json; items/room134.json stays byte-identical.

Package changes
- The token, payload/plan/member hashes, and embedded batch public descriptor/operator are rebound together.
- a/6.py selects counts (0,0,0,580,0), schedule ((0,3),), distance type 3, and expected 580 throughout.
- Its full-reader rehearsal chooses one item per new set and checks distance records under journal index 3. a/5.py checks the same types and sets.
- a/0.json selects object_abs_distance so prepared settings agree with the operator and CPU checks.
- memory_bound uses 98 captures. Memo identity depends on images, indices and weights, not question wording; the existing 200 GiB allocation still fits.
- 3.py enforces one GPU and 04:00:00; SUBMIT.cmd defaults to those values. No submission command was executed against Orchard.
- B5 already has wrap_batch's exclusion and EXIT trap. The builder verifies that wrapper, unwraps its Python body, and reapplies the identical wrapper once with the fresh token.
- A4/B5 serving audit found no missing distance setting: scale selection, unit handling, selector code, reader policy and scorer are byte-identical. The inherited six-call cap records but does not serve the sixth call.
- Seven serving files and the call-cap path were compared; evidence is `/dev/shm/c18d/SERVING_AUDIT.json`.

Binding sources
- D200 uses B5 payload 9.json export_binding and a/4.py REVIEWED_* constants. Ordered part pins come from B5/ret/metadata/INPUTS.json; preparation paths come from EXPORT_PIN.json.
- D200 leaves a/4.py and export_binding byte/value-identical to B5, respectively.
- D544 uses bases/b1/export_544.json and inputs_tower.json, plus the pinned 469ddece preparation config and s1_receipt in B5's payload. b1/READ_PLAN.json and src/9.json contain no export_binding.
- D544 binds run 469ddece, member m544, object q8/8865619b/469ddece_mstop.tar, 21,583,032,320 bytes, SHA256 3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7.
- B5's fill accepts an mstop object and an m544 member independently. D544 changes only REVIEWED_OBJECT, REVIEWED_ARCHIVE_BYTES and REVIEWED_ARCHIVE_SHA256; bytes happen to remain equal.
- No upstream 544 .done/.claim receipt was found in the supplied b1 tree. A one-field claim cannot be passed as --done. The driver creates an explicitly documented three-field declaration from sealed archive pins; fill verifies the whole stream against it.
- Optional DONE_FROM and CLAIM_FROM validate supplied receipts. PREP_FROM supplies files 7/8/9; otherwise step 544 uses hash-matched preparation bytes already present in the payload.
- REUSE_PARTS_FROM verifies each part's size and SHA256 before linking/copying. Without reuse, gsutil pulls each part once, serially, with retries and parallel/sliced downloads disabled.

Budget and risks
- A4 journal reads/0/metadata/journals/3/0/items.jsonl contains 150 distance rows totaling 3539.964358 seconds: mean 23.599762 seconds/item.
- ceil(1.3 * 23.599762386313476 * 580 + 1800 conservative load seconds) = 19,595 GPU seconds.
- Adding the retained 1800-second stop margin requires 21,395 seconds (05:56:35). This cannot fit 04:00:00; the cap remains enforced and partial completion is expected at that limit.
- Export bytes, allocated RGB decoding, model loading and GPU serving were not tested locally. No 21.6 GB export was read, downloaded or filled here.

Validation and use
- `/scratch/jjyeung/envs/p1cpu/bin/python -B test_d.py --work /dev/shm/c18d/test2` passed; TEST_RESULTS.json and PLANNING.json are there.
- Tests reproduce all 15 B5 delivery-member bytes, generate synthetic items with make_r0_heldout.py's exact logic using payload R0 questions, and build both bindings with /usr/bin/python3 (3.6).
- Tests cover load_manifest, 580 native mappings, 98 captures, prepare/descriptors/rehearsal/memory/run-summary, exact change allowlists, export binding and seven malformed-input cases.
- All 17 Python files in the integration compile check passed actual Python 3.6 py_compile; final workspace Python files were compiled again after the final checker edit.
- `score_d.py --self-test` and its two-return CLI passed: set/unit counts, call rates, capped counts, missing rows, optional released scores, 10,000-draw room bootstrap, duplicate rejection and item-binding rejection.
- `/usr/bin/python3 -B check_release_d.py` passed; `/dev/shm/c18d/RELEASE_RESULTS.json` records actual-item delivery hashes, embedded asset checks, reuse-hash rejection, dry-header checks and walltime rejection.
- Both shell scripts pass bash -n. o_build_D.sh ran locally for both STEP values with STAGE, SOURCE_1TGZ, SOURCE_SHA256 and KROOT overrides; all artifacts remain under /dev/shm/c18d.
- Actual-item build reports/diffs are `/dev/shm/c18d/actual200/{BUILD.json,DIFF.txt}` and `/dev/shm/c18d/actual544/{BUILD.json,DIFF.txt}`; their delivery directories are recorded in BUILD.json.
- On Orchard: `STAGE=/project/community/jjyeung/okh7/813f42db/d STEP=200 bash o_build_D.sh`; then run o_place_fill_D.sh with the same exported STAGE and optional reuse/preparation variables.
- Locally score with p1cpu: `python -B score_d.py DIST580_JSON --src UNPACKED_D_PAYLOAD --return RETURN_DIR --compare BASELINE_RETURN_DIR --out scores.json`. Omit --compare for one return.
- Scores use stored output.scores.answer/released_answer; MRA and differences are fractions. Call rate uses planned n, with completed-only rate also reported. Paired inference uses only completed pairs and resamples room_key with seed 17.

Follow-up
- `evidence/INDEX.md` indexes 29 evidence files with SHA256 hashes; the complete evidence directory is 5003724 bytes, below 10 MB.
- Evidence includes both BUILD/DIFF pairs, dist580 items, planning/test/audit/release results, all 14 actual544 delivery members except 0.tgz, and the four changed payload files plus 9.json.
- Every copied/extracted source byte and the delivery/payload hashes were verified. No individual evidence file exceeds 5 MB.
- `o_cpu_D.sh` requires P and T, verifies fill status and the sealed walltime, then submits the CPU check on preempt with eight CPUs, 200 GiB, no GPUs and no requeue.
- `o_sub_D.sh` requires P and T and retains the fill-status, CPU receipt, bundle guard, entry sequence, memory, full-reader, duplicate-submit, general-queue, return-pool and entrypoint checks before GPU submission.
- The memory receipt must equal D's 98-capture bound. The return pool must exist, contain no symlinks, and remain at or below 75,000,000 bytes; inspection errors fail the check.
- Rehearsal pairs, selected as the first manifest item in each set by a/6.py: (R0-dev-reworded, r0_0064a29747f8cc8de793_ho), then (R0-dev-twin, r0_0064a29747f8cc8de793).
- Both rehearsal records must have type object_abs_distance. The separate five-minute trap-test submission is omitted.
- `o_build_D.sh` and its generator accept WALLTIME (default 04:00:00) and pass it to b.py --time. The four-hour maximum remains enforced; `o_place_fill_D.sh` is unchanged.
- Build with `WALLTIME=HH:MM:SS STEP=544 STAGE=... bash o_build_D.sh`; place/fill with the same STAGE; export `P=/project/community/jjyeung/okh7/a15_cot_ap<token>` and `T=HH:MM:SS` for the CPU and GPU scripts.
- Run `bash o_cpu_D.sh`, wait for its successful CPU receipt, then run `bash o_sub_D.sh`. T must equal the build's WALLTIME.
- `/usr/bin/python3 -B test_followup_d.py` passed on Python 3.6.8; `evidence/FOLLOWUP_RESULTS.json` records the checks.
- All four shell scripts pass bash -n. The receipt checker accepts a synthetic CPU.json constructed with a/5.py's exact receipt expression and rejects 21 corruptions; four pool checks passed.
- A local build sealed WALLTIME=01:23:45, wrote that default into SUBMIT.cmd, and rejected 04:00:00 at the entrypoint. Embedded assets match their source files.
- Synthetic checks do not establish a successful export restore or real CPU rehearsal. Nothing was submitted; no network, SSH, Git, GPU or deletion operation ran.
