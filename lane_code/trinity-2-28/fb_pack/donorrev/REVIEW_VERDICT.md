GO AFTER FIXES (MUST items M1-M3; the donor code itself passed every check I ran)

# fbp_donorrev: frozen tower-scale donor patch review

Setup: I copied the base tree into `work/base` and verified its 939 hashes and the seal 57a1f14d. I applied `PATCH_DONOR.patch` (fff484d7) cleanly to `work/new`; all eight resulting hashes equal `FILES_TOUCHED.json`. All runs were CPU-only under `nice -n 10`; scripts and JSON outputs are in `work/`.

## MUST
- M1. The tests cannot detect a FoV leak. `point_depth_head.py:169-170` zero-initialises `fov_film[-1]`, so in the tiny fixture FoV has no effect on any depth grid. This makes the V1 check at `tests/test_scale_donor.py:110-114` vacuous (it perturbs live `depth.fov` and `frame_queries`). It also means `K1_INVARIANCE.json` cannot catch a donor that reads live FoV, and `EXPORT_CHECK_V1/V2` report identical V1 and V2 scales. My negative control was a V1 donor whose `encode` takes its FoV from the live `depth.fov`. It went undetected with zero FiLM and was caught once FiLM was nonzero (`work/K1_MINE_FILM0.json` vs `FILM1.json`). Fix: in `fixture()` (`test_scale_donor.py:23-27`) and `code/k1_fixture.py`, give `fov_film[-1]` nonzero weights before saving the source, add the negative control, and regenerate `K1_INVARIANCE.json`.
- M2. Any byte change to nine source files makes N's exports unreadable, and `READER_REQUEST.md` doesn't warn about it. `feature_contract` hashes those nine whole files (`scale_donor.py:18-20,43`), `attach` enforces the hash (`:71-72`), and `verify_export` requires identical settings (`:202-204`). I appended one comment line to `carrier_c1_data.py` in a reader-tree copy. `attach` then refused the N binding, and a repinned reader was refused at `carrier_c1_run.py:3268` (`work/brittle_mine.py`). So any later edit to those files, including a fix to `scale_donor.py` or `tower_read.py` after N launches, locks N's exports out. Fix: state the byte-identity requirement and list the files in `READER_REQUEST.md`, or enforce source hashes only at training-side `attach` and record them, without enforcing, at read.
- M3. The runtime-loader instruction is incomplete. `READER_REQUEST.md:17` tells the separate runtime loader only to "add the attach call". But `mdg_runtime.py:212-213` strict-loads `heads.pt`, and I confirmed it fails on the non-tensor `_scale_donor` key even after `attach`. The request must also say to pop `_scale_donor`, check it equals `artifact['scale_donor']`, and call `scale_donor.verify_export` before the strict load, as `carrier_c1_run.py:3264-3268` does. The current behaviour fails closed.

## SHOULD
- S1. N needs a fresh preparation. `scale_donor` is bound into the preparation receipt (`carrier_c1_run.py:639,744`), so N's existing pre-donor receipt is refused with "C1 preparation frame layout/LM lever differs". Neither `REPORT.md` nor `READER_REQUEST.md` says this. Alternatively, treat it as a freeze-time lever (`:720`), since it changes no prepared stream.
- S2. Every rank hashes and loads the 2.76 GB source `heads.pt`, ignoring `verify_assets` (`scale_donor.py:176,182` via `carrier_c1_run.py:888-890`; `p3_provenance.py:49`).
- S3. `REAL_WEIGHT_COMMAND.sh:15` describes `N_DONOR_BINDING` as "the exact scale_donor configuration", but `scale_donor_check.py:125` reads `binding['scale_donor']`, so the JSON needs a top-level `scale_donor` key. Line 25 also hardcodes a Trinity Python path.

## Verified items: no problem found
1. Optimizer and decay exclusion.
   - Groups take only `requires_grad` parameters (`carrier_c1.py:662`). The gf1 path adds only gf1 parameters (`gf1.py:223-230`), and clipping filters the same way (`carrier_c1_run.py:1645`).
   - Resume shards hold only trainable parameters (`:1966,2074`). The donor has no buffers and is re-attached from its pinned source at every launch (`:888-890`).
   - `compare_configs` refuses removing or changing a binding (`r1_handover.py:164-171`), and `attach` leaves the handover group table unchanged.
   - Native `wrap_model` on a socket-free fake 2-rank group (`work/FSDP_MINE.json`): every donor parameter is an ignored, replicated, non-flattened state. None is in an FSDP optimizer group or `named_trainable`, and `train()` keeps the donor in eval mode.
   - Caveat, not a defect: FSDP mixed precision casts the inputs of the auto-wrapped private-visual blocks to bf16 (max feature difference 9.8e-4; zero with mixed precision off). The live path is affected the same way, and no trainer code runs the tower arm.
2. K1 two-step invariance and field-absent parity, rerun with my own code (`work/K1_MINE_FILM1.json`, `work/PARITY_*.json`).
   - K1 used both authenticated K1 train captures and all 64 frame hashes, random G3T depth, confidence and translations, native AdamW with weight decay 0.01, and two `optimize_step` calls, for V1 and V2.
   - All donor tensors (66 for V1, 64 for V2) and the shared visual kept their hashes. Donor grids and float64 scales stayed bit-identical, while all 63 live point-depth tensors, the live grids, the pose head and the own pose moved.
   - The donor grid bit-equals a recomputation from a separate copy of the checkpoint's depth path.
   - Parity: with the field absent, base and new match byte for byte on both decode arms (before training, after two steps and after reload), optimizer groups by parameter name, the handover table, 275 state tensors, 525 optimizer-state tensors, 202 exported head tensors and the artifact keys.
   - My focused suite of 21 modules (131 tests on base, 138 on new) has identical results; the only difference is the 7 new donor tests, which pass.
3. No live dependency in either variant. Perturbing the pose head, live point-depth head, live `depth.fov`, live frame queries, the LM and the base visual leaves the donor grid bit-identical. The V2 grid tracks the G3T FoV and the V1 grid does not. A changed shared visual is refused by `metadata()`.
4. Exports and reader binding: 26 of 26 end-to-end `load_artifact` cases behave as expected (`work/EXPORT_MINE.json`). It refuses each changed donor tensor (point-depth, frame queries, FoV), a changed shared visual, a missing tensor, a bf16-rounded tensor, forged metadata, dropped metadata, a stripped donor, the wrong variant, and a reader that skipped `attach`.
5. The scale is applied exactly once.
   - Translations equal raw × s exactly, rotation and FoV are untouched, and the depth map equals G3T × s (`tower_read.py:324-331`).
   - The sampler matches the registered profile's endpoint-aligned bilinear interpolation (`geometry_profiles.py:174-180`).
   - The own arm with the donor attached equals the own arm without it: decode, two pose and VQA steps, all state, optimizer and RNG tensors (`work/OWNARM_MINE.json`).
6. Scope: every hunk serves the donor. With the donor present, the tower arm's depth changes from the live head to G3T × s, as the spec's "lifted G3T depth" requires, and `READER_REQUEST.md:21` declares it.
7. `READER_REQUEST.md` is complete apart from M2, M3, S1 and S3. Real step-400 and step-544 heads and the V1/V2 pricing decision remain MISSING, as the lane reports.
