H is sealed for steps 544 and 200 with 900 camera items: 450 originals and 450 held-out rewordings.
Each type has 150 originals and 150 rewordings. All 900 questions agree with their display-frame pairs.
Every original matches A4; each twin preserves its original's frame and label fields.
All 900 native mappings use the same 52 captures and frame bindings A4 supplies. No new captures are needed.

The user supplied an independent ACCEPT WITH FINDINGS review; the build enforces its frame-agreement finding.
The scorer patch is pinned from `2736e479…` to `d032f969…`; `rows/expected_calls.py` is unchanged.
The build seals the evaluator digest in the plan and verifies it during preparation; launch and merge retain their checks.
`load_manifest` validates H, and `map_items` requires its explicit native tasks.
The three frozen item/task files and the portable `auth/R0_ROOMS.txt` pin are sealed in the payload.
A4's tower, candidates_argmax, G3T memo, call caps, reader, tree and frame inventories are preserved.
The operator selects ORDER 0,1,2; COUNTS=(300,300,300,0,0); expected=900. Rehearsal and summary cover camera only.
`BATCH.sh` has one build_r10 wrapper, including the EXIT and USR1 guards.

Step 200 uses 673bc60f/m200, archive SHA256 `795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b`.
Its `a/4.py` and `9.json` export_binding remain identical to A4.
Step 544 uses the exact bind_D544.json bytes: 469ddece/m544, object 469ddece_mstop.tar, archive SHA256 `3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7`.
Its preparation hashes match the A-lineage prepare_dd26bb95 export metadata.

A4's 450 camera journals average 7.895331 seconds/item.
The budget is ceil(1.3 × 7.895331 × 900 + 1800 load) = 11,038 seconds.
Including the 1,800-second stop margin gives 12,838 seconds (03:33:58), which fits the sealed 04:00:00 allocation.
This is a measured estimate; no H inference timing or answer result is claimed.

Local CPU checks passed for both builds: 636-item/3,816-case placement parity, 450 original expected-call matches,
900 valid-response measure() stubs, 900 max_calls checks, ten invalid-pair refusals, and 900 unique native mappings.
The fresh p1cpu processes put b/ before reader_core and verify all twin/A4 frame mappings.
Synthetic checks cover room-bootstrap differences (10,000 draws, seed 17), step comparison, missing items,
return identity mutations, malformed journals, whole/part hashes, hardlinks, entrypoint limits and CPU receipt guards.
Local checks do not restore weights or load RGB files; the Orchard CPU job must pass before submission.
Orchard helpers parse under /usr/bin/python3 3.6.8. No network, SSH, Git, GPU, deletion or Orchard job was used.

Run `python3 -B review_h.py` from this workspace to verify every indexed hash and reconstruct both deliveries in memory.
`evidence/INDEX.md` indexes reviewer-visible code, frozen inputs, source A4, delivery deltas, timing journals and test receipts.
No reviewer needs /dev/shm. Every workspace file is below 5 MB; evidence is below 12 MB.
The local delivery tokens and full delivery hashes are in evidence/H200/BUILD.json and evidence/H544/BUILD.json.

On Orchard, use distinct STAGE paths for the two steps:
`STEP=544 WALLTIME=04:00:00 STAGE=/project/community/jjyeung/okh7/813f42db/h544 bash o_build_H.sh`
`STEP=200 WALLTIME=04:00:00 STAGE=/project/community/jjyeung/okh7/813f42db/h200 bash o_build_H.sh`
Run o_place_fill_H.sh with the same STAGE. It selects the supplied step-specific reuse directory and verifies all four parts before hardlinking.
Step 544 requires DONE_FROM; the wrapper defaults to `/project/community/jjyeung/okh7/x_07ca49df/o/gcs_469ddece_m544.done`.
Then use P=<built package path> and T=04:00:00 with o_cpu_H.sh; after its CPU receipt passes, use o_sub_H.sh.
The guards retain one GPU, no requeue, queue/pool checks, receipt/entry-sequence binding and the sealed walltime.

Score actual returns with `python3 -B score_h.py --return RETURN --package BUILD.json --out scores.json`.
Use the trusted BUILD.json from that exact launch, or its placed package directory.
Add `--other-return RETURN200 --other-package BUILD200.json` for current-minus-other step comparisons.
The six type/set cells report call rate and patched-scorer answer; max_calls scores zero. Missing IDs and complete-pair counts are explicit.
`--self-test --out synthetic.json` runs synthetic returns against the two reviewer-visible builds; reviewers may set H_TEST_TMPDIR to their writable temporary directory.
Per-wording cells contain only 13–27 items; endpoint/yaw specificity and rotation h06's shared phrase remain interpretation limits.
