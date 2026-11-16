# VLA kits status (lane b15_vla, 2026-11-16; CPU only)

The LIBERO Test L kit survived intact on Orchard and passes every CPU proof again with results identical to 2026-11-11. B1 is bound to the step-544 export with its heads dropped. navrun had no surviving copy; it was rebuilt from its record on trinity-1-18 and passes its CPU proofs, with the differences listed below. U1 stays blocked.

## 1. LIBERO Test L kit (survived)
- Location: Orchard `/project/community/jjyeung/vla_libero` (kit, envs e_sv 7.0G / e_lb 2.2G / e_tool 0.2G, LeRobot data 1.8G, hdf5 1.2G, tiny Qwen3.5, src, osmesa). `kit/KIT_SHA256` = af43148989f7837ef8e137453096f6a67fb366242a6f16fa454544ac55303897; `sha256sum -c kit/SHA256SUMS`: 199 lines, 0 failed (2026-11-16 12:31Z).
- Proofs re-run on orchard-login-001, 12:31-12:57Z, nice 19, OMP 4, one at a time, into `out/rerun_20261116/` through a symlinked shadow root so no 11-11 output was overwritten (driver `rerun_driver.sh`, sha256 39f111f7...; pulled logs: trinity-1-18 `b15_vla/work/rerun/pulled/`, archive sha256 188b09f9...).

| Proof | Result 2026-11-16 | Record 2026-11-11 |
|---|---|---|
| hook_check (step-0 loss parity with StarVLA head, masked tail chunk, proprio grads, strict server reload) | HOOK_OK | HOOK_OK |
| exact resume (4 steps, resume from step-2 state) | HOOK_RESUME_EXACT; step-3/4 losses 0.3647024 / 0.5427384 and batch fps equal 11-11's | HOOK_RESUME_EXACT |
| repeat equality | REPEAT_EXACT | REPEAT_EXACT |
| state rotation, torn-state resume, disk guards, early-loss stop | ROTATE_TEST_OK (10/10 checks) | ROTATE_TEST_OK |
| parity of eval and training (state after 10 settle steps, image flip, prompts) | state max diff 0.0; flip matches eval client; 40/40 prompts | same |
| T-4 / T-5 / T-6 | PASS 19/20 with fx<0, hand-eye t (0.050, 0.000, -0.097) m, residual 6e-8 m / PASS / PASS corr 0.932, 0.970, 0.962 | same |
| closed loop, 10 episodes (OSMesa) | random 0/10, demo replay 10/10 | same |

## 2. Student binding
- **B1 (heads dropped) -> step-544 export, artifact 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef.** Source: Orchard `okh7/i_bb09a77d/m.tar` (sha256 3ed73aea..., 21.6 GB; members `ap/8865619b/runs/469ddece/m544/full_weights/*`, `heads.pt`, artifact at `ap/93ccadab/m544/artifact.json`). Header check (`B1_BIND_544_HEADER_CHECK.json`): 760 tensors, names and shapes equal to base Qwen3.5-9B c2022362 (426 LM, 333 ViT, 1 lm_head); 48 tensors stored BF16 where base is F32 (the trainer loads both arms in bf16); heads.pt (2.76 GB) is not used.
- Launch wrapper `kit_bind/train_b1_544.sh` (sha256 647fc50c...): extracts full_weights and the artifact into job-local /tmp, checks the artifact sha256, refuses heads.pt and any arm but B1, then runs the sealed `kit/train_arm.sh` with `B1_SRC=dir:...`. It exists because stage.sh's `tarparts:` mode expects the artifact under the full_weights prefix. Logic tested on a fake archive (pass, wrong-sha refusal, U1 refusal); kit bytes unchanged.
- **First batch.** Tiny Qwen3.5: the arm_testL recipe runs forward and backward on CPU with finite loss (cpu_hook straight and resumed runs). **Real-config batch (Qwen3.5-9B shapes, bf16, ~40 GB RAM) not run**: ORCH holds it (needs an Orchard general CPU job or a governed stream).
- **U1: BLOCKED.** Under the end-to-end ruling its where input must come from heads inside the artifact (briefs 04 and 05), not vla_where's runtime; train_arm.sh refuses U1 without WHERE_CACHE.
- B0 (base reference) is user-approved (`VLL_RULING=user_20261111_base_yes`).

## 3. Finding for any GPU launch
Orchard naming: the kit root, SBATCH `--output` and every job log sit under `/project/community/jjyeung/vla_libero` and the kit's scripts are named after LIBERO/VLA; the Orchard rule forbids project, dataset and method words in paths and logs. Relocate or alias the root under an opaque path before a job is submitted (ORCH decision; the sealed kit hard-codes the root in vl_env.sh and every script header, so the fix is a re-seal).

## 4. navrun (rebuilt; no copy survived)
- Rebuilt by Codex (GPT-6 Astra, high) from VLA_NAV_RUNNER_20261111.md, vla_heads' `nav_text` codec (vendored byte-for-byte, drift test) and vla_where's ClickTranslator/lift/controller (imported, not copied). Package trinity-1-18 `/scratch/jjyeung/orch_n30/b15_vla/navrun` (`BUILD_REPORT.md`, `run.sh`); source archive `navrun/out/navrun_src.tgz` sha256 496836be8e375da80b807a87a26d1e9899540ede18f42cdb9243061514d51328.
- Inputs on trinity-1-18 (all copied over IB): env `/scratch/jjyeung/envs/nav_habitat024` (habitat-sim 0.2.4, py3.9); R2R-CE v1-3 + R2RIE-CE json (`navrun_inputs/refs`); official VLN-CE preprocessed GT (`refs/r2r_vlnce_preprocessed`, from 0-13 zip sha 3171f5be...); glb+navmesh of the 72 non-test scenes (`navrun_inputs/scenes`, 4.8 GB, from 0-13 mp3d_habitat.zip sha 470948ee..., equal to its .sha256).
- Interfaces kept: `act(history_frames, instruction, state)`, formats text / nav / waypoint / click / chunk, 32-frame history `[i*t//31]` with configurable length (64 works; prompt and click frame number follow it), VLN-CE movement, NE/SR/SPL/OSR/TL/nDTW/SDTW, lists with ordered-id sha256, nested seed-0 subsets, row builder, compare (GAIN/HARM/EQUIVALENT/INCONCLUSIVE, Holm), audit, resume, stop file, step cap. CPU runs blind on the navmesh (no renderer).

| CPU proof | Rebuilt | Record |
|---|---|---|
| unit tests (unittest) | 118 pass in 6-8 s (I re-ran: OK) | 58 pass |
| shortest-path oracle, 1,839 val-unseen | SR 1.000, SPL 0.9988 | 1.000 / 0.999 |
| oracle, val_unseen_600_s0 / R2RIE 600 | SR 1.000 / 1.000 | 1.00 / 1.00 |
| blind SR full 1,839: random / forward / instruction | 0.022 / 0.039 / 0.047 | 0.024 / 0.041 / 0.042 |
| blind SR val_unseen_600 | 0.028 / 0.047 / 0.053 | 0.027 / 0.032 / 0.033 |
| oracle-click, no occlusion, 600 ids: GT-location lead | SR 0.887, SPL 0.879, OSR 0.887 | 0.802 / 0.792 / 0.847 |
| oracle-click: geodesic lead (2 m along shortest path) | SR 0.665, 201 step caps | - |
| nav-answer replay vs official GT actions | 10,819/10,819 exact; sim replay of every GT path within 2e-6 m (episode 3707 included) | 10,819 exact; ep 3707 off 0.42 m mid-path |
| 1% plan (108 eps, 61 scenes): states / nav / click / waypoint rows | 6,114 / 1,093 / 1,009 / 1,301 | 6,348 / 1,158 / 1,497 / 1,232 |
| 10% plan (1,082 eps) | 62,749 states, 11,370 nav rows | 63,302 frames, ~11.6k nav rows |
| scene audit train / val-unseen / test | disjoint (61 / 11 / 18) | disjoint |

- Differences are reported, not tuned away: the record's blind-policy definitions, list hashes, lead-point rule and terminal sampling were lost, so blind priors and row counts differ by small amounts, and the oracle-click ceiling depends on the lead rule (0.665 to 0.887 against 0.802).
- Finding: with geodesic leads, 118 of 201 capped episodes stand still; in 102 of them the controller rounds a nonzero bearing to zero turns at every one of the last 20 decisions and keeps commanding blocked forward steps (vla_where `nav.py` controller). Model clicks near obstacles can hit the same stall. Test N's NU arm should either fix the controller or log the stall rate.
- Blocked: rendering and depth-occlusion checks (CUDA EGL; GPU job), MIP rand100 ids (not recovered; loader verifies a supplied id file), habitat-lab cross-check (not installed), `nav.contracts.validate_public` (not available here), real tokenizer/model integration, R2RIE detection scores.

## 5. Costs for the queue (from the records; not re-measured)
- Test L shake-down: about 3.6 H100-hours plus 2 GPU-hours. Decisive Test L: 2 x 18 H100-hours plus 30-60 GPU-hours of evaluation (the record estimates about 21 H100-hours per decisive arm, unmeasured at world 4).
- Test N: 2 x 27 H100-hours plus about 36 GPU-hours. navrun's CPU simulator cost is negligible (blind 1,839 episodes in 9-94 s); model cost dominates: nav 10.2 calls per episode (13 GPU-h at 2.5 s per call, 84 GPU-h at 16 s with reasoning), click 12.9 calls (26 GPU-h at 4 s). At 64 history frames each call carries twice the visual tokens of 32, so expect up to about 2x prefill cost per call (estimate, unmeasured).
- B0 is user-approved as the base comparison. No VLA GPU run starts before the spatial model is strong (user, 2026-11-11).

## 6. Copies
- Orchard: kit and proofs at `/project/community/jjyeung/vla_libero` (KIT_SHA256 above; rerun under `out/rerun_20261116/`).
- Mirror: trinity-1-13 `/scratch/jjyeung/n30_mirror/b15_vla/` (see STATUS.md for the archive sha256).
