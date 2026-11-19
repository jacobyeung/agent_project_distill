E is built locally for D0 step 200; local validation passed. Nothing was placed or submitted on Orchard.
The default WALLTIME is 02:00:00. D's conservative budget requires 02:16:42, so BUILD.json reports budget_fits=false.

- The authenticated source is A4/1.tgz, SHA256 dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459.
- The tested E token is d52e3a4ed3fd4; delivery SHA256 is 9477ace59b4267469296106509c0c6a0c9674efa308b36714bbe0670c0eb8a2d.
- The local delivery is /dev/shm/c18e/test2/K/a15_cot_ap01b0b3ec74d5a2a1/1.tgz. Each build issues a fresh token.
- evidence/INDEX.md lists stored SHA256 hashes. review_e.py reconstructs the complete delivery in memory using only workspace evidence.
- A4's 15 delivery-member bytes were reproduced. Of 927 payload members, only 9.json changes; its changed keys are token, budget_gpu_seconds and export_binding.
- The 636-item items/devs1_routed.json remains byte-identical. The reader selects its 150 object_abs_distance items by type, in A4's original order.
- a/6.py uses types [3], COUNTS (0,0,0,150,0), SCHEDULE ((0,3),), expected 150, and a distance-only rehearsal and summary.
- a/0.json and a/5.py require the distance input type. A4's preparation settings omit types, so the CPU check validates inputs['types'].
- The payload, serving code, item answers, capture paths, selector, scorer, six-call cap, memo settings and dependency pins remain A4's exactly.
- The retained 84-capture memory bound fits 200 GiB. A4's real selector stub rehearsal runs locally; this is not a full export restore or GPU decode.
- A4's unwrapped BATCH.sh receives build_r10.wrap_batch once with the new token. Embedded public/operator bytes and all derived hashes agree.
- 3.py seals one GPU and WALLTIME for check/submit; SUBMIT.cmd defaults to those values. WALLTIME accepts HH:MM:SS up to the inherited four-hour builder limit.

- bind_E200.json binds run 359fcc3c, m200, q8/8865619b/359fcc3c_m200.tar, 21,583,032,320 bytes and SHA256 6bd9eb26e22c7bdd26fe6e5a932502fa7d1aebd57024861bca786b027ff7d61b.
- The config identity, duplicate frame layout, preparation hashes/paths and upstream .done path come from bind_E200_partial.json.
- base_identity c202236235762e1c871ad0ccb60c8ee5ba337b9a identifies the shared Qwen/Qwen3.5-9B base snapshot, separately from the run and step.
- A4's students.py registers that snapshot; carrier_c1_run.py checks original-base provenance; stage_restore.py checks the original model manifest. evidence/BASE_IDENTITY.json includes authenticated source excerpts.
- Placement also checks D0's hash-pinned preparation config base_identity before transfer; a/4.py checks the export artifact against both preparation and export_binding.
- Four ordered parts each contain 5,395,758,080 bytes. No per-part hashes are invented: placement checks sizes, then a/4.py hashes every part and authenticates the whole stream against the sealed archive SHA256.
- The driver pulls each part once, serially, with retries and sliced/parallel downloads disabled. REUSE_PARTS_FROM can supply numbered local parts; whole-stream verification still runs.
- PREP_FROM accepts numbered 7/8/9 files, config.json plus prepared/s1_receipt.json plus data_receipt.json, or the D0 inputs root. Without it, the sealed D0 paths are used.
- DONE_FROM may override the receipt path, but its three fields must equal the sealed binding. Missing or mismatched preparation/receipts fail closed.

- A4 measured 3,539.964 seconds for 150 distance items (23.599762 seconds/item). D's formula gives ceil(1.3 * 3539.964 + 1800) = 6,402 seconds, plus the retained 1,800-second stop margin.
- The 02:00:00 default may return partial results under that conservative estimate. WALLTIME=02:20:00 covers the estimate if the operator chooses it before building.
- score_e.py reports call rate from authenticated h1eval.scorers.records and MRA from stored answer/released_answer scores, overall and by question unit: cm=28, ft=46, in=33, m=43.
- The scorer executes that exact pure records() function without importing the scorer's NumPy dependency; all Orchard-side helper code uses Python 3.6 and the standard library.
- Baselines are A4 R1 step 200 read 0 and the supplied step-544 return read 1. Both contain all 150 IDs in the same order. T1 pairing is preserved by unchanged items and serving pins; no T1 return was supplied for a separate test.
- The 544 baseline records memo=verify for its first 30 IDs; the scorer accepts and reports that setting. E retains A4's memo=on.
- Paired differences include call rate and both MRAs, overall and by unit, with 10,000 room-bootstrap draws, seed 17. Missing rows remain missing; call rate uses planned counts and also reports completed-only counts.
- A4 against itself yields zero differences and [0,0] intervals in every group. A4's call rate/MRA are 58.67%/50.27%; the 544 baseline's are 99.33%/28.27%. These are baseline results, not E results.

- test_e.py passed: delivery/payload allowlists, exact item order, offline prepare/rehearsal/mapping/summary, bindings, whole-stream hashing, malformed inputs and scorer checks.
- test_scripts_e.py passed: the actual CPU receipt expression, 15 rejected corruptions, four return-pool checks, shell syntax, and a shell build sealing WALLTIME=01:23:45.
- test_place_e.py passed: four ordered mocked pulls and five preparation/receipt failures before any pull. check_release_e.py passed embedded-asset, dry-header and reuse-hash checks.
- All workspace Python files and changed delivery Python files compiled with /usr/bin/python3 3.6.8. The unchanged reader rehearsal ran with the local p1cpu environment and no GPU.
- The 21.6 GB export, real preparation files, model restore, allocated CPU rehearsal and GPU serving remain untested locally. No SSH, network, Git, GPU or deletion operation ran.

On Orchard, run `STAGE=/project/community/jjyeung/okh7/813f42db/e WALLTIME=02:00:00 bash o_build_E.sh`, then `STAGE=<same-stage> bash o_place_fill_E.sh`.
After filling, export P=/project/community/jjyeung/okh7/a15_cot_ap<new-token> and T=<sealed-WALLTIME>; run o_cpu_E.sh, wait for its successful CPU receipt, then run o_sub_E.sh.
The submission script retains A4-compatible fill, CPU receipt, bundle, entry sequence, memory, duplicate-submit, queue and return-pool checks.
Score fetched E returns with `/usr/bin/python3 -B score_e.py evidence/scoring/items/devs1_routed.json --src evidence/scoring --return E_RETURN --out scores.json`.
For a portable self-test, add `--self-test --a4 evidence/A4_return --baseline544 evidence/step544_return` and omit --return. `python3 -B review_e.py` verifies all evidence without external files.
