# VLA kits status (lane b15_vla, 2026-11-16; CPU only)

The LIBERO Test L kit survived intact on Orchard, now sits under an opaque root with a new seal, and passes every CPU proof with results identical to 2026-11-11. B1 is bound to the step-544 export with its heads dropped. navrun had no surviving copy; it was rebuilt from its record on trinity-1-18, gained a stall-free click controller and the rand100 list, and passes its CPU proofs, with the differences listed below. U1 stays blocked.

## 1. LIBERO Test L kit (survived)
- Location: Orchard `/project/community/jjyeung/45e92888780e` (moved from the old named root on 2026-11-16 13:55Z; kit, envs e_sv 7.0G / e_lb 2.2G / e_tool 0.2G, LeRobot data 1.8G, hdf5 1.2G, tiny Qwen3.5, src, osmesa). `kit/KIT_SHA256` = **e6bccd3deea4d7ab1c342061a3f3130e3d24eb83f622f2159ab2aa829a5fb775** (198 files, `find . -type f` minus SHA256SUMS, KIT_SHA256 and __pycache__, sorted; KIT_SHA256 = sha256 of SHA256SUMS). The previous seal af43148989f7837e... (verified 12:31Z, 0 failed) is kept in `out/reseal_20261116/`, with the pre-edit bytes of all 246 rewritten files in `/project/community/jjyeung/45e92888780e_w/pre_sed_backup.tar`.
- Proofs re-run on orchard-login-001 before the move (12:31-12:57Z, `out/rerun_20261116/`) and after it from the new root (`out/rerun_20261116b/`, see section 3), nice 19, OMP 4, one at a time, into `out/rerun_20261116/` through a symlinked shadow root so no 11-11 output was overwritten (driver `rerun_driver.sh`, sha256 39f111f7...; pulled logs: trinity-1-18 `b15_vla/work/rerun/pulled/`, archive sha256 188b09f9...).

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
- Launch wrapper `kit_bind/train_b1_544.sh` (sha256 cf047044..., also at Orchard `45e92888780e/bind/`; SBATCH header and kit path follow the new root): extracts full_weights and the artifact into job-local /tmp, checks the artifact sha256, refuses heads.pt and any arm but B1, then runs the sealed `kit/train_arm.sh` with `B1_SRC=dir:...`. It exists because stage.sh's `tarparts:` mode expects the artifact under the full_weights prefix. Logic tested on a fake archive (pass, wrong-sha refusal, U1 refusal); kit bytes unchanged.
- **First batch.** Tiny Qwen3.5: the arm_testL recipe runs forward and backward on CPU with finite loss (cpu_hook straight and resumed runs). **Real-config batch (Qwen3.5-9B shapes, bf16, ~40 GB RAM) not run**: ORCH holds it (needs an Orchard general CPU job or a governed stream).
- **U1: BLOCKED.** Under the end-to-end ruling its where input must come from heads inside the artifact (briefs 04 and 05), not vla_where's runtime; train_arm.sh refuses U1 without WHERE_CACHE.
- B0 (base reference) is user-approved (`VLL_RULING=user_20261111_base_yes`).

## 3. Orchard naming (ORCH order 1328Z)
- Done: the root moved to the opaque `/project/community/jjyeung/45e92888780e` (one `mv` on the same filesystem); 246 text files that held the old root (venv pyvenv.cfg and entry-point shebangs, osmesa pkg-config and *-config scripts, `st/p310_path`, the Python sysconfig file, kit scripts) were rewritten and 66 absolute symlinks re-pointed; SBATCH `--output` is now `$ROOT/logs/j_%j.out`; usage lines name jobs `a15_cot_ap<opaque hex>`; the project name left kit comments. No `vla_libero` path remains.
- Re-proof from the new root, 13:59-14:22Z (`out/rerun_20261116b/`, kit e6bccd3d..., `sha256sum -c` 0 failed; pulled logs `b15_vla/work/rerun/pulled_b/`, archive sha256 e1141882...): every proof passes again; hook straight/resumed traces are byte-equal to the pre-move run; closed-loop rows differ only in wall seconds and video paths.
- Residual words that the code needs and that renaming would break: StarVLA's config keys (`framework.qwenvl.*`) and the `Qwen3.5` substring its loader matches in the model dir name; LIBERO's suite names (`libero_spatial` ...) and the mixture and data-dir names derived from them (`vll_libero_spatial_d5_s0`, `*_lerobot`); the Python packages `libero`, `robosuite`, `vla_heads`, `vla_where` and their source paths (`src/LIBERO-master`, `src/starVLA-pilot/examples/simBenchmarks/LIBERO/...`, `kit/ext_v2/vla_heads`); the kit's own file names (`libero_render.py`, `libero_*_manifest.json`); env var names LIBERO_HOME and LIBERO_CONFIG_PATH that LIBERO reads; the shared HF cache path `models--Qwen--Qwen3.5-9B`. These appear in job arguments and log text, not in the job name, root path or log file names. Removing them needs a StarVLA/LIBERO rename layer and a full re-proof.

## 4. navrun (rebuilt; no copy survived)
- Rebuilt by Codex (GPT-6 Astra, high) from VLA_NAV_RUNNER_20261111.md, vla_heads' `nav_text` codec (vendored byte-for-byte, drift test) and vla_where's ClickTranslator/lift/controller (imported, not copied). Package trinity-1-18 `/scratch/jjyeung/orch_n30/b15_vla/navrun` (`BUILD_REPORT.md`, `run.sh`); source archive `navrun/out/navrun_src.tgz` sha256 4e85320b37314837c09eb77ac4049a57430e59cd795bfed28713ec05dc95c607.
- Inputs on trinity-1-18 (all copied over IB): env `/scratch/jjyeung/envs/nav_habitat024` (habitat-sim 0.2.4, py3.9); R2R-CE v1-3 + R2RIE-CE json (`navrun_inputs/refs`); official VLN-CE preprocessed GT (`refs/r2r_vlnce_preprocessed`, from 0-13 zip sha 3171f5be...); glb+navmesh of the 72 non-test scenes (`navrun_inputs/scenes`, 4.8 GB, from 0-13 mp3d_habitat.zip sha 470948ee..., equal to its .sha256).
- Interfaces kept: `act(history_frames, instruction, state)`, formats text / nav / waypoint / click / chunk, 32-frame history `[i*t//31]` with configurable length (64 works; prompt and click frame number follow it), VLN-CE movement, NE/SR/SPL/OSR/TL/nDTW/SDTW, lists with ordered-id sha256, nested seed-0 subsets, row builder, compare (GAIN/HARM/EQUIVALENT/INCONCLUSIVE, Holm), audit, resume, stop file, step cap. CPU runs blind on the navmesh (no renderer).

| CPU proof | Rebuilt | Record |
|---|---|---|
| unit tests (unittest) | 132 pass in 21 s (I re-ran: OK), incl. replay of the 102 stalled episodes | 58 pass |
| shortest-path oracle, 1,839 val-unseen | SR 1.000, SPL 0.9988 | 1.000 / 0.999 |
| oracle, val_unseen_600_s0 / R2RIE 600 | SR 1.000 / 1.000 | 1.00 / 1.00 |
| blind SR full 1,839: random / forward / instruction | 0.022 / 0.039 / 0.047 | 0.024 / 0.041 / 0.042 |
| blind SR val_unseen_600 | 0.028 / 0.047 / 0.053 | 0.027 / 0.032 / 0.033 |
| oracle-click, no occlusion, 600 ids, controller v2: GT-location lead | SR 0.887, SPL 0.879, OSR 0.887 (v1 identical) | 0.802 / 0.792 / 0.847 |
| oracle-click, controller v2: geodesic lead (2 m along shortest path) | SR 0.683, SPL 0.675, 190 step caps (v1: 0.665, 201) | - |
| rand100 (Open-Nav OpenNav_R2R-CE_100; 100/100 ids, scenes, trajectories, starts match val-unseen): oracle / random / forward / instruction SR | 1.00 / 0.02 / 0.05 / 0.06 | 1.00 / 0.030 / 0.060 / 0.060 |
| nav-answer replay vs official GT actions | 10,819/10,819 exact; sim replay of every GT path within 2e-6 m (episode 3707 included) | 10,819 exact; ep 3707 off 0.42 m mid-path |
| 1% plan (108 eps, 61 scenes): states / nav / click / waypoint rows | 6,114 / 1,093 / 1,009 / 1,301 | 6,348 / 1,158 / 1,497 / 1,232 |
| 10% plan (1,082 eps) | 62,749 states, 11,370 nav rows | 63,302 frames, ~11.6k nav rows |
| scene audit train / val-unseen / test | disjoint (61 / 11 / 18) | disjoint |

- Differences are reported, not tuned away: the record's blind-policy definitions, list hashes, lead-point rule and terminal sampling were lost, so blind priors and row counts differ by small amounts, and the oracle-click ceiling depends on the lead rule (0.683 to 0.887 under controller_v2, against 0.802).
- Controller stall (ORCH order 1328Z): vla_where's controller (v1) stalls when a bearing rounds to zero turns and forward steps stay blocked (118 of 201 capped geodesic-lead episodes stand still; 102 with a nonzero bearing rounded to zero at all last 20 decisions). navrun's `controller_v2` (default for NU and oracle-click; `vla.nav.eval.controller_version`, v1 kept exact) cancels the rest of a leg at the first blocked forward step (< 1e-6 m moved), then turns one 15-degree quantum toward the blocked leg's bearing and probes one 0.25 m step per decision until motion resumes; STOP wins; no fitted threshold. The model-facing click decoder and an injected vla_where ClickTranslator both go through it; vla_where's sealed source is unchanged. Logged changes (v2 minus v1): geodesic SR +0.018, SPL +0.017, OSR +0.012, nDTW -0.026, step caps -11, stationary tails 118 -> 0; GT-location SR/SPL/OSR unchanged, nDTW -0.008, stationary tails 45 -> 4 (the 4 left alternate 90-degree turns without forward steps). Training rows and blind priors are unchanged.
- rand100 source: Google Drive id 1SfrPWqCIiivwduCYPMe-Za1wOt4eU6G9 (linked from the Open-Nav README), 1.85 MB plain JSON despite its .json.gz name, sha256 f4770f1b...; ordered-id sha256 230eada8...; fetched once with curl at 8 MB/s as a single file under 20 MB (LANE_RULES exemption); `navrun_inputs/rand100/`.
- Blocked: rendering and depth-occlusion checks (CUDA EGL; GPU job), habitat-lab cross-check (not installed), `nav.contracts.validate_public` (not available here), real tokenizer/model integration, R2RIE detection scores.

## 5. Costs for the queue (from the records; not re-measured)
- Test L shake-down: about 3.6 H100-hours plus 2 GPU-hours. Decisive Test L: 2 x 18 H100-hours plus 30-60 GPU-hours of evaluation (the record estimates about 21 H100-hours per decisive arm, unmeasured at world 4).
- Test N: 2 x 27 H100-hours plus about 36 GPU-hours. navrun's CPU simulator cost is negligible (blind 1,839 episodes in 9-94 s); model cost dominates: nav 10.2 calls per episode (13 GPU-h at 2.5 s per call, 84 GPU-h at 16 s with reasoning), click 12.9 calls (26 GPU-h at 4 s). At 64 history frames each call carries twice the visual tokens of 32, so expect up to about 2x prefill cost per call (estimate, unmeasured).
- B0 is user-approved as the base comparison. No VLA GPU run starts before the spatial model is strong (user, 2026-11-11).

## 6. Copies
- Orchard: kit and proofs at `/project/community/jjyeung/45e92888780e` (KIT_SHA256 above; reruns under `out/rerun_20261116/` and `out/rerun_20261116b/`).
- Mirror: trinity-1-13 `/scratch/jjyeung/n30_mirror/b15_vla/` (see STATUS.md for the archive sha256).
