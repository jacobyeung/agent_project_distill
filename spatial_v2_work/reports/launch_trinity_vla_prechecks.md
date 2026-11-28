# Trinity VLA GPU Admission Receipt (`KT-1c`: `navrun` + `vla_where` + `vla_heads` + `dyn_probe`)

- **Date (UTC):** `2026-11-28T13:20:00Z` (`2026-11-28 05:20 PT`)
- **Host / GPU Used:** `trinity-2-28` (`1.8 TB` free `/scratch`), GPU `6` wrapped in `/data3/shared/scripts/vnice/vnice.sh` (`0 MB/s` NFS; GPUs `0..3` `mgaur` and `4,5,7` `KT-1`/`KT-6` untouched)
- **Sealed Source Root:** `/scratch/jjyeung/preserved_20261128/b15_vla/` (read-only; `navrun_src.tgz` SHA256 `4e85320b37314837c09eb77ac4049a57430e59cd795bfed28713ec05dc95c607` verified intact)
- **Work & Receipt Directory:** `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/`

---

## 1. Executive Verdict Table

| Suite / Gate | Target Unblocked | Status | Measured Result & Receipt Path |
| :--- | :--- | :--- | :--- |
| **`nav_habitat024` `.ib` Sync** | Test N (`R2R-CE`) on `trinity-2-28` | **PASS** | `2.1 GB` pulled via `trinity-1-18.ib` tar pipe -> `/scratch/jjyeung/envs/nav_habitat024` (`0 MB/s` NFS; `habitat_sim 0.2.4`, Python `3.9.18`) |
| **`navrun` CPU Unittest Suite** | `controller_v2`, schema 8.2/8.4, metrics, resume | **PASS (`132/132`)** | `Ran 132 tests in 20.294s — OK` (`work_vla_prechecks/out/navrun_unittest.log`) |
| **`navrun` MP3D Scene Inventory** | All `val_unseen` (11) & `rand100` (10) scenes | **PASS (`72/72`)** | `72/72` non-test `.glb` + `.navmesh` pairs verified at `/scratch/jjyeung/preserved_20261128/b15_vla/navrun_inputs/scenes/mp3d` (`0` missing) |
| **`navrun` GPU CUDA-EGL `rand100` Smoke** | Headless `512x512` RGB rendering & `oracle-click` throughput | **PASS (`20/20` eps)** | **`22.39 ep/min`** (`53.60s` wall, `70.58 steps/s`), `0` EGL crashes, `1,245/1,245` valid `(512,512,3) uint8` RGB frames across 6 scenes, `SR=0.700`, `SPL=0.700`, `OSR=0.800`, `NE=2.259 m`, `nDTW=0.785`, `SDTW=0.657`, `stationary_tails=0` (`work_vla_prechecks/out/rand100_smoke20_oracle_click_egl.json`) |
| **`vla_heads` CPU Test Suite** | Test L `U0`/`U1` OFT head + `UniformBins`/`Digits`/`Fast` codecs + `nav_grammar_v1` | **PASS (`136/136` + `53/53`)** | `136 passed, 1 skipped in 225.98s` (`work_vla_prechecks/out/vla_heads_pytest.log`) + `schema_examples.py` `53/53` checks pass |
| **`vla_where` CPU Conformance & `P-1..P-4`** | `WhereProvider` (`code_sha: 0cdd6cfb...`), `ClickTranslator` (`T-3`), precheck math | **PASS** | `T-3` `ClickTranslator` returns `['forward']*6`, `distance_m=1.5`, `range_m=2.0833`; synthetic noisy `P-1..P-4` pass (`P-1=1.000`, `P-2=0.0029 m`, `P-3 AUROC=1.000`, `P-4=1.000/1.000`, `work_vla_prechecks/out/vla_where_cpu_smoke.json`) |
| **`vla_where` GPU `T-11` (`P-5`) `bf16` Parity** | `ViewSetG3T` vs `FrozenG3TTower.run` `bf16` on 32 frames | **PASS (`<= 1e-4`)** | Max abs diff on GPU 6 (`bf16`, 32 frames, `28.30s`): **`pose9 = 1.014e-07`**, **`depth_grid51 = 0.0`**, **`conf_grid51 = 0.0`** (`work_vla_prechecks/out/t11_parity_gpu6_bf16.json`) |
| **`dyn_probe` Stage 0 Audit** | 4D Dynamic Evaluation (`DYN_PROBE_KIT_20261111.md`) | **AUDIT COMPLETE (BLOCKED ON `2-18` LOSS)** | Per `RECOVERY_MAP_2_18_OUTAGE_20261115.md`, `trinity-2-18:/scratch/jjyeung/orch_cd/dyn_probe` (47 CPU tests + 7.65 GB TUM/Bonn zips) had no copy outside dead `trinity-2-18`; `kit/libero_render.py` survives in `b15_vla` |

---

## 2. Task 1 Details: `navrun` Environment, Wrapper, CPU Suite & GPU CUDA-EGL Smoke

### 2.1 Environment & Wrapper (`trinity-2-28`)
- Pulled `/scratch/jjyeung/envs/nav_habitat024` (`2.1 GB`) from `trinity-1-18.ib` to `trinity-2-28:/scratch/jjyeung/envs/nav_habitat024` over InfiniBand (`0 MB/s` NFS).
- Created clean wrapper `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_nav_228.sh` (redirects `XDG_CACHE_HOME` and `NUMBA_CACHE_DIR` to `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/cache`, sets `PYTHONPATH` to `b15_vla/navrun`, `ext_where`, and `ext_v2/vla_heads`, and runs `nice -n 19 /scratch/jjyeung/envs/nav_habitat024/bin/python`).
- Froze reproducible episode lists in `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/lists/`:
  - `rand100.json` (`100` episodes, seed `0` from `val_unseen`, `sha256: 35fb340219c30a009093f4c855caef42c96842c82857b4212650b9c004a336ee`)
  - `val_unseen_600_s0.json` (`600` episodes, seed `0` stratified across 11 `val_unseen` scenes, `sha256: 0458f43f3585da01a52ab6074dd93ed011b40d5c89e3c6b9b497d318d8bc4d31`)

### 2.2 GPU 6 CUDA-EGL `rand100` Smoke (`20` Episodes, `oracle-click`, `controller_v2`, `render=True`)
- **Command run:**
  ```bash
  CUDA_VISIBLE_DEVICES=6 /data3/shared/scripts/vnice/vnice.sh \
    /scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_nav_228.sh \
    /scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_rand100_egl_smoke.py
  ```
- **Results (`work_vla_prechecks/out/rand100_smoke20_oracle_click_egl.json`):**
  - **Episodes:** `20/20` completed across 6 `val_unseen` MP3D scenes (`8194nk5LbLH`, `EU6Fwq7SyZv`, `QUCTc6BB5sX`, `TbHJrupSAjP`, `X7HyMhZNoso`, `Z6MFQCViBuw`)
  - **Throughput:** `53.60s` wall (`22.39 ep/min`, `70.58 steps/sec`; extrapolates to **`~4.5 min` for full `rand100`** and **`~27 min` for `val_unseen_600_s0`** plus VLM inference time)
  - **EGL / Frame Integrity:** `0` EGL crashes or context errors; `1,245/1,245` decision observations verified as non-empty `(512, 512, 3) uint8` RGB arrays (`min_std = 26.86 > 0`)
  - **Navigation Metrics (`oracle-click`, quantized 15° turns / 0.25m steps):** `SR = 0.700`, `SPL = 0.700`, `OSR = 0.800`, `NE = 2.259 m`, `nDTW = 0.785`, `SDTW = 0.657`, `path_length = 8.438 m`, `steps = 189.15`, `decisions = 62.25`, `collision_rate = 0.246`, `recovery_triggers = 0.20`, `stationary_tail = 0.0`

### 2.3 Ready-to-Run CLI for Full `rand100` (`100` Episodes) or `val_unseen_600_s0` (`600` Episodes)
```bash
CUDA_VISIBLE_DEVICES=6 /data3/shared/scripts/vnice/vnice.sh \
  /scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_nav_228.sh -m navrun.evaluate \
  --split val_unseen \
  --episode-list /scratch/jjyeung/orch_home_distill/work_vla_prechecks/lists/rand100.json \
  --output-format click --controller v2 --render \
  --policy nav_oracle_factory:make_oracle_click \
  --output /scratch/jjyeung/orch_home_distill/work_vla_prechecks/out/rand100_full_oracle_click.json
```
*(For student VLM checkpoints `CP0`/`CP1`/R1-step400, pass `--policy <module>:<factory>` wrapping `vla_where.nav.ClickTranslator` (`range_source='floor_plane'` or `'g3t_depth'`).)*

---

## 3. Task 2 Details: `vla_where`, `vla_heads`, and `dyn_probe`

### 3.1 `vla_heads` (`kit/ext_v2/vla_heads`) & `vla_where` (`kit/ext_where/vla_where`)
- **CPU Test Suite (`vla_heads`):** Ran 137 pytest items via `/scratch/jjyeung/envs/p1cpu/bin/python` with `sam3_scipy_ovl` + `sam3_capretry_native_v1` site-packages: **`136 passed, 1 skipped in 225.98s`** (`work_vla_prechecks/out/vla_heads_pytest.log`). `schema_examples.py` passed **`53/53`** checks (covering `WhereReadout` 36-D layout, `UniformBins`, `DigitsCodec`, `FastCodec` fit/encode/decode, `OFTHead` forward/loss with `where_dropout_prob=0.10`, and `nav_grammar_v1`).
- **GPU `T-11` (`P-5`) `ViewSetG3T` vs `FrozenG3TTower.run` Parity (`work_vla_prechecks/out/t11_parity_gpu6_bf16.json`):**
  - Ran `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_t11_gpu.sh` on `trinity-2-28` GPU 6 under `vnice.sh` using local pinned weights `/scratch/jjyeung/k1/g3t/{model.safetensors,config.json}` (`weights_sha: d460957bb1c8...`, `config_sha: 5aeb2acd008d...`) and `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872` (`source_sha: df1ea59a73b0...`).
  - Result on 32 `256x256` frames in `bf16` (`28.30s`):
    - `max_abs_diff.pose9 = 1.01449e-07` (gate `<= 1e-4`: **PASS**)
    - `max_abs_diff.depth_grid51 = 0.0` (gate `<= 1e-4`: **PASS**)
    - `max_abs_diff.conf_grid51 = 0.0` (gate `<= 1e-4`: **PASS**)

### 3.2 Inputs & Exact Commands for `vla_where` Real-Student `P-1..P-4` LIBERO Replay
- **Local Pinned Assets Verified on `trinity-2-28` (`0` external fetches needed for towers/student):**
  - Frozen G3T tower: `/scratch/jjyeung/k1/g3t/model.safetensors` & `/scratch/jjyeung/k1/g3t/config.json`
  - Frozen SAM 3 tower: `/scratch/jjyeung/k1/sam3/sam3.pt`, `/scratch/jjyeung/k1/sam3/Load_Receipt.json`, `/scratch/jjyeung/k1/sam3/src`
  - Student export (`T0` / `CP1` full weights): `/scratch/jjyeung/k1/exports/t0_p1a_hs256/full_weights` (`full_weights.json` + 4 safetensors shards + `student_heads.pt`) or `trinity-0-13:/scratch/jjyeung/eval_Cp1_m200_r0dev_013/export_full/full_weights`
  - LIBERO renderer & GT store generator: `/scratch/jjyeung/preserved_20261128/b15_vla/work/orchard_kit/kit/libero_render.py` (`render_suite('libero_spatial', out_dir, episodes_per_task=5)` exports `<suite>_rendered.hdf5` + `gt_store.sqlite` + `hand_eye.json` via `vla_where.scale.fit_hand_eye` using `/scratch/jjyeung/envs/vla_ingle/bin/python` and `/scratch/jjyeung/vla_data/libero_spatial` on `trinity-1-18.ib`, or Orchard `/project/community/jjyeung/45e92888780e/data/libero_rendered`).
- **Exact Python Invocation for `WhereProvider` (`student`) + `P-1..P-4` Evaluation (`vla_where.precheck.evaluate`):**
  ```bash
  CUDA_VISIBLE_DEVICES=6 /data3/shared/scripts/vnice/vnice.sh \
    /scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_t11_gpu.sh -c '
  from vla_where.build import build_provider
  from vla_where.backends.gt import GTStore
  from vla_where.precheck import evaluate
  store = GTStore("/scratch/jjyeung/orch_home_distill/work_vla_prechecks/libero_spatial/gt_store.sqlite")
  prov = build_provider("student", dict(
      full_weights="/scratch/jjyeung/k1/exports/t0_p1a_hs256/full_weights",
      g3t_weights="/scratch/jjyeung/k1/g3t/model.safetensors",
      g3t_config="/scratch/jjyeung/k1/g3t/config.json",
      sam3=dict(checkpoint_path="/scratch/jjyeung/k1/sam3/sam3.pt",
                receipt_path="/scratch/jjyeung/k1/sam3/Load_Receipt.json",
                source_root="/scratch/jjyeung/k1/sam3/src"),
      hand_eye="/scratch/jjyeung/orch_home_distill/work_vla_prechecks/libero_spatial/hand_eye.json",
      hand_eye_sha256="<HAND_EYE_SHA256>",
      device="cuda"))
  print(evaluate(prov, store, episodes))'
  ```

### 3.3 `dyn_probe` Stage 0 Status & Blocker
- **Audit Finding:** Per `/scratch/jjyeung/preserved_20261128/b15_vla/DYN_PROBE_KIT_20261111.md` and `/data2/jjyeung/agent_project_data/distill_design/RECOVERY_MAP_2_18_OUTAGE_20261115.md` (Section 3.3), the `dyn_probe` package (`47` CPU unit tests, `cli.py`, `student_t0.py`, `tower_g3t.py`, `pi3_adapter.py`) and its `7.65 GB` staged TUM RGB-D (8 sequences) + Bonn RGB-D Dynamic (4 sequences) archives existed solely on `trinity-2-18:/scratch/jjyeung/orch_cd/dyn_probe` and were lost when `trinity-2-18` went down on 2026-11-15 (`0` surviving copies on `trinity-2-28`, `trinity-0-13`, `trinity-1-18`, `/data2`, `/data3`, or Orchard).
- **What Survives Locally on `trinity-2-28`:**
  1. Full Stage 0 specification and pre-registered `D1`/`D2`/`D3` decision tree in `/scratch/jjyeung/preserved_20261128/b15_vla/DYN_PROBE_KIT_20261111.md`.
  2. All three underlying model weights/adapters on `trinity-2-28:/scratch/jjyeung/geo_bakeoff_kit/weights/` (`pi3/model.safetensors`, `g3t`, `da3`, `TTT3R`) plus `T0` student export (`/scratch/jjyeung/k1/exports/t0_p1a_hs256/full_weights`).
  3. Thus `navrun` (Test N) and `vla_where` / `vla_heads` (Test L `U0`/`U1`) are **100% unblocked now**, while `dyn_probe` Stage 0 requires either `trinity-2-18` disk recovery or re-creating the 12-sequence TUM/Bonn evaluation harness from `DYN_PROBE_KIT_20261111.md`.
