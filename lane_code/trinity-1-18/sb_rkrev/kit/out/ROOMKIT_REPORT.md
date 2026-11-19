# Room-call pricing kit: CPU delivery

The kit is built. S0, all six S1 CPU forwards, S1b and all 22 CPU tests pass. GPU pricing has not run.
No GPU, network, SSH, Git, process termination or writes outside the workspace were used.
The original specification and evidence remain byte-identical snapshots; OPERATOR.md defines the executable protocol.

Review edits applied by finding number:
1. The step-200/read-0/journal-4/0 baseline is frozen at SHA256 c9b5994cc461420a0ccfb035cd252e27bac6da3016ab5d5a28f77a14239b319d. The bar uses unrounded D+5.
2. Both arms retain R0 mesh labels. The guide discloses the measurement-target mismatch and preregisters an outcome-independent diagnostic label audit with no relabeling.
3. R0-dev diagnostics cannot tune the candidate. K1 held-out, R0-dev and benchmark rooms fit no rule, threshold, frame budget, admission policy or checkpoint. No adaptive reruns are allowed.
4. The hashed kernel-provenance record states MISSING. The GPU gate requires verified train-only selection and the kernel's relation to the benchmark-selected rule. Tower pretraining overlap is UNKNOWN.
5. Full digests, both question sets, 162 scene manifests and exact 32/94 layouts are pinned. Remote checkpoint/read/frame provenance remains MISSING.
6. The lane-local adapter extracts only the harness's pure functions, unpacks its R0 tuple, preserves the deployed kernel, and adapts depth_grid64/anchor_slots. All caches and TMPDIR stay in the workspace.
7. Resume distinguishes absent, valid and corrupt/stale receipts and binds predictions, frames, slots, weights, code and settings. GO binds host/card/run and checks one actual CUDA device.
8. DA3 f32+R0 is the sole confirmatory test. Part B is exploratory; a trained-route claim requires fresh rooms. Missing primary/items, duplicate baseline IDs and invalid cached scores are fatal.
9. Unreproducible power probabilities are omitted.
10. The runner enforces a cumulative 5,400-second budget with exclusive ownership, an OS deadline and conservative interruption accounting. It records the first u94 memory probe and drops u94 on OOM. Guard and Part B costs are separate.

CPU commands and results (run from the workspace; C means `bash scripts/cpu.sh`):
- `C scripts/s0.py > out/S0.log 2>&1`: COMPLETE; 18,556 full local hashes, 3,015 sealed files, 15,228 PNGs, 162 scenes and 98 R0-dev room items.
- `C vendor/kitcheck.py /scratch/jjyeung/geo_bakeoff_kit out/KITCHECK.json > out/KITCHECK.log 2>&1`: COMPLETE; all five checkpoint checks pass.
- `C scripts/reproduce.py > out/S1b.log 2>&1`: PASS; 134/134 stored R0 areas and all 24 train-table entries match; held-out variants stay null.
- `C tests/test_roomkit.py > out/TESTS.log 2>&1`: 22 tests pass, including K1 source-slot identity, kernel equality, exact outlier removal, refusals, units, resume, scorer failures, GO binding before CUDA access and budget ownership.
- `C scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1`: PASS. Its oracle PASS is a synthetic test, not a room-pricing result.
- S1 command: `source scripts/env.sh`, then `$GEO_BAKEOFF_ROOT/runtime/base/bin/python3 -B scripts/cpu_forward.py --capture scannetpp/067e2e4e61 --worker 0` and the same command with `scannetpp/036bce3393 --worker 1`; logs are `out/S1_worker{0,1}.log`.
- `C out/s1a_check.py > out/S1A.log 2>&1`: full 64-frame CPU passes give 14.69 vs 14.73 m² (0.27% error), and 39.79 vs 39.35 m² (1.12% error); both pass 5%. Runtime: 1537.35/1529.91 seconds; peak RSS: 16.041/16.034 GiB.
- `C scripts/summarize_s1.py > out/S1_summary.log 2>&1`: PASS; both 64-frame checks are within 5%; all six full CPU forwards have verified receipts.
- scannetpp/067e2e4e61 K1 32-frame area: 14.98 m²; 32/64 ratio: 1.019741.
- scannetpp/036bce3393 K1 32-frame area: 39.28 m²; 32/64 ratio: 0.987183.
- R0-rl 01ce24e652: label 7.290000000000001 m²; R0 7.9 m²; T10 7.62 m². These plumbing values decide nothing.
- R0-rl 0452249a1e: label 2.16 m²; R0 1.94 m²; T10 1.91 m². These plumbing values decide nothing.
- Both K1 32/64 ratios outside [0.85,1.15]: False. No rule or setting was adjusted.

Remaining gaps:
- MISSING: authenticated sources on trinity-3-30: `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/src/items/room134.json`.
- MISSING: `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl` and `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A/src/tree` on trinity-3-30.
- The direct export omits reader frame indices. Both R0-dev and dev-S1 frame equality remain unverified against the remote reader.
- UNREACHABLE HERE: trinity-3-30 `/scratch/jjyeung/n30_mirror/b14_k1towers/geo_k1_mirror_1600Z.tar` and `/scratch/jjyeung/orch_n30/b14_k1towers/k1towers`. S1b uses the successful local stored-prediction equivalent.
- MISSING: evidence resolving kernel-selection provenance. No clean held-out design is certified.
- GPU pricing, physical-card gate execution and 94-frame peak memory are untested; no confirmatory decision exists. The 0.6 GPU-hour figure remains an estimate. This task used zero GPU-hours.
- The optional guard is skipped without authenticated local reader frames; Part B is outside Part A. A second-node mirror is MISSING because this task forbids network access.

The kit, exact GPU command and GO format are in OPERATOR.md. `configs/GO.template.json` is NOT_GO.
Final evidence seal: `C out/finalize_delivery.py` verifies every distinct local input digest. Packaging command: `C scripts/package.py`; deliverable: `out/sb_roomkit.tar`, checksum: `out/sb_roomkit.tar.sha256`. The packager checks every member against `out/DELIVERY_SHA256.txt`.
The report retains provenance disclosures and numbered review edits because the task explicitly requires them.
