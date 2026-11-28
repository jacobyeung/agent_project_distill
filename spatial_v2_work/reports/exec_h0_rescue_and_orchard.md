# Hour-0 Asset Rescue & Orchard Launch-Readiness Packet (`exec_h0_rescue_and_orchard`)
**Timestamp:** `2026-11-28T13:20Z` (`05:20 AM PT`) | **Home:** `trinity-2-28` (`1.8 TB` `/scratch` free)

---

## 1. Nov-29 `/scratch` Rescue (Compute `.ib` Tar Pipe — `0 MB/s` NFS)
Pulled **14.7 GB (`27,829` files)** from expiring `trinity-1-18` (`97%` full, `107G` free) and `trinity-3-30` (`98%` full, `45G` free) to `trinity-2-28:/scratch/jjyeung/preserved_20261128/` over InfiniBand (`172.16.1.x`), resetting 7-day mtimes with zero NFS IO.

| Source Host & Path | Local Rescued Path (`trinity-2-28`) | Size | Files | Verified Seal / Notes |
|---|---|---:|---:|---|
| `1-18:/scratch/jjyeung/orch_n30/b15_vla` | `preserved_20261128/b15_vla` | `5.6G` | `874` | Complete `navrun` (`159M`), `navrun_inputs` (`5.1G`, 72 MP3D scenes + official VLN-CE GT + `rand100`), `work` (`351M`), `kit_bind/train_b1_544.sh`, `out/VLA_KITS_STATUS.md` |
| `1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w35` | `preserved_20261128/tree_rebuild10_w/w35` | `480M` | `7,487` | `s35_n_go.tar` sha256 `3c3b91ebda00a427...1f2b404` (**exact match** to sealed `w35 ea058fed`) |
| `1-18:/scratch/jjyeung/n30_mirror/tree_rebuild30` | `preserved_20261128/n30_mirror_118/tree_rebuild30` | `79M` | `275` | Contains `resume36` (Vehicle N resume kit `dc38194d`) |
| `3-30:/scratch/jjyeung/n30_mirror` | `preserved_20261128/n30_mirror_330/n30_mirror` | `8.3G` | `8,663` | Full `3-30` mirror (`k1_ops3` `6.0G`, `r1_ops` `1.1G`, `contracts_rebuild` `593M`, `b14_k1towers` `515M`, `native_r4` `42M`, `tree_rebuild29` `39M`, `e3_geom` `29M`, `tree_rebuild28` `23M`) |
| `3-30:/scratch/jjyeung/orch_n30/{n_review1l,n_review1n,n_ops8,n_ops10,n_ops1,tree_rebuild30}` + `y_24m4z10.json` + `mint.py` | `preserved_20261128/n_ops_kits_330/` | `251M` | `10,530` | Critical Vehicle N gate (`gate.py`/`run_gate.sh`), session minter (`sess2.sh`/`sess_job.sh`/`mint_n.py`), `o_confirm35.sh`, `y_24m4z10.json` (`9ce25396...`), `mint.py` (`b7388f55...`) |

**Remaining on Remote `/scratch` (Not Copied — Exact Sizes):**
- `1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w` (~`118G` total across historical `w12..w34`; largest: `w24` `20G`, `w24z12` `9.2G`, `w24z11b` `8.0G`, `work` `7.6G`, `w24z11` `7.1G`, `w24z10` `6.1G`, `w21` `5.1G`). Active `w35` (`480M`) is already rescued; older iterations need no pull.
- `1-18:/scratch/jjyeung/n30_mirror` (`76G`, 39 older mirrors incl. `b09_rlkit`, `b04_e2ehook`, `rows_a2/r1/r2`). Selectively pull `b09_rlkit` or `rows_*` over `.ib` if needed before Nov 29.
- `1-18:/scratch/jjyeung/envs/nav_habitat024` (required by `b15_vla/navrun/run.sh`; pull over `.ib` to `2-28:/scratch/jjyeung/envs/` before running `navrun` locally on `2-28`).
- **Optional durable NFS archive (`<=4 MB/s`):** Tar `w35/s35_n_go.tar` (`6M`), `resume36`, and `b15_vla/navrun/out/navrun_src.tgz` (`93K`) to `/data3/jjyeung/distill_src_archive/` via `rsync --bwlimit=4000` (under 20 MB, no governor friction).

---

## 2. GCS `gs://cmu-gpucloud-jjyeung/ae/` Lifecycle & Inventory
Verified directly via GCS JSON REST API (`2026-11-28T13:16Z`) using `/data2/.../gcloud_config/credentials.db`.
- **Bucket Policy:** `location=US-CENTRAL1`, `storageClass=STANDARD`, **`lifecycle: null`**, `retentionPolicy: null`, **`softDeletePolicy.retentionDurationSeconds: 0`**, `versioning: null`.
- **Verdict:** **No automatic GCS lifecycle deletion fires on Dec 01.** Because `softDeletePolicy=0`, any manual/billing sweep of `ae/` is irreversible.
- **Actual `ae/` Contents (`13` objects, `53.87 GB` total — NOT 610 GB; all created `2026-11-09T23:02Z–23:34Z`):**
  - **E05 / 4D Teacher Weights ALREADY in US-CENTRAL1 GCS:** `ae/b2__f7d2a9c4__newbench_dyn4d__weights__point4d__point4d_final.pt` (`5.797G`; duplicate `b5__...point4d_final.pt` `5.797G` & `ae/w/14e44e06c6c2` `5.797G`), `ae/b5__fourdv__external__ckpt__any4d_4v_combined.pth` (`7.727G`), `ae/b5__fourdv__external__ckpt__moge_vitl_model.pt` (`1.257G`).
  - **Evac & Partial Shards:** `ae/b7__evac_jy_20261104.tar` (`11.182G`), `ae/c346__shards__rank003..006.pt` (`4 × 3.358G = 13.432G`), `ae/b3__...full_relay_20261108T080237Z.tar` (`2.034G`), `ae/b3__...dense96_inputs_v1.tar` (`0.844G`), `ae/b6__fourdv__env.tar` (`0.000G`).
  - Other verified prefixes: `q8/` (`349G+`, `step-544` / `R1` exports), `q9/` (Vehicle N test uploads), `q10/` (`5.14G`).
- **Zero-Egress Cloud-Side Protection Command (run from Orchard if an external Dec-01 sweep is expected):**
  ```bash
  export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
  gcloud storage cp -r 'gs://cmu-gpucloud-jjyeung/ae/*' gs://cmu-gpucloud-jjyeung/durable_20261128/ae/
  ```

---

## 3. Orchard Live State & Critical Disk / SSH Alerts (`2026-11-28T13:18Z`)
- **SSH Diagnostic (`trinity-2-28` vs `trinity-0-13`):** On `trinity-2-28`, `/home/jjyeung/google-cloud-sdk/bin/gcloud` hangs >20s on `/home` NFS Python imports, causing `ossh.sh` IAP tunnel to time out (`rc=255` banner exchange). On `trinity-0-13`, `gcloud --version` runs in `1.1s` and `ossh.sh` succeeded in one batched call. **Workaround:** Run `ossh.sh` from `trinity-0-13` (existing ControlMaster) or stage a local `/scratch/jjyeung/google-cloud-sdk` copy on `2-28`.
- **Live `squeue -u jjyeung`:**
  - `advanced` (`adv_4gpu_qos`): `176609` (`orw_gd2`, 1 GPU, 10h27m), `176637` (`orw_aq4`, 1 GPU, 1h51m), `176638` (`orw_aq5`, 1 GPU, 1h51m) on `orchard-community-3` (**3/4 `advanced` GPUs held by SPLIT**).
  - `general` (`general_qos`): `176641` (`orw_gq2`, 1 GPU, 1h50m) on `orchard-community-4` (**1/1 `general` GPU held by SPLIT**).
  - `preempt` (`preempt_qos`): `174491` (`lv_pre0`), `174492` (`lv_pre1`) — 1 GPU each, `PENDING (Priority)`.
- **CRITICAL DISK BLOCKER (`/project/community` = `9.0 GiB` FREE, `100%` USED):**
  - `10.73.0.66:/nfscommunity`: `10T` used, **`9.0G` avail (`100%`)**; `/home`: `4.7T/5.0T` (`99%`, 25 GB quota); login `/tmp`: `2.8G` free (compute-node `/tmp` has `~6.0 TB`).
  - **Impact on `Vehicle N`:** Stages to compute `/tmp` and uploads to GCS (`<50 MB` written to `/project`). **Runnable at `9.0G`**, but risks `ENOSPC` if `/project` drops to `0 B` during `sess_<JOB>.json` or `review.json` install.
  - **Impact on `LIBERO Test L`:** Trains & evaluates on compute `/tmp` (`preflight.sh` requires `340 GiB` on `/tmp` — passes!), **BUT `train_arm.sh` refuses to copy `final_model` (`~20G`) unless `/project` has `>80 GiB` free and refuses `resume_state` (`~125G`) unless `/project` has `>=250 GiB` free.** Add a GCS upload hook (`gs://cmu-gpucloud-jjyeung/vla_libero/<id>/`) at job end before submitting, or final weights will vanish with `/tmp`!
- **Verified Staged Kits on Orchard:**
  - `okh7/x_22c714e1/n`: `SHA256SUMS.txt` = `ea058fed0495be92...551591` (**EXACT**), `jn8.sh` = `2de401bd4370b13e...388c684` (**EXACT**), `n_r/` is **EMPTY (`mode 700`)**, `u/c672ad47...` & `u/da19bb3a...` present.
  - `45e92888780e`: `kit/KIT_SHA256` = `e6bccd3deea4d7ab...a5fb775` (**EXACT**), `bind/train_b1_544.sh` + `kit/{train_arm.sh,eval_plan.sh}` + `okh7/i_bb09a77d/m.tar` (`step 544`, 21.6G) intact.
  - Official eval pools intact: `okh7/x27ret` (VSI-5130), `okh7/313db5a47f11ff0c` (ReVSI-999 mp4s), `okh7/d9c35d0a` (VSTI-450 `a/b/c.tar` + `FAMILY.json`), `/project/community/jjyeung/gcloud`.

---

## 4. Exact Ready-to-Submit Launch Commands & Preflight Checklists

### Prerequisite Before ANY Orchard Claim (SPLIT Yield Protocol)
1. Notify SPLIT first (do **not** cancel unannounced): append notice to `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_CVPR_ORCH_20261128.md` and `/data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md`, or message `agy:225c9445-f2b8-43f8-a487-5b19fa068e96@trinity-0-13`.
2. SPLIT's Lane R1 auto-cancels on submission; if immediate slots are needed, pre-authorized command: `scancel 176609 176637 176638` (frees `advanced`) / `scancel 176641` (frees `general`).

### 4.1 `E01` — Vehicle N (`w35` `ea058fed`, 4× H100 `advanced`, `~10.5h` wall-clock)
**Blockers:** (1) Requires user/orchestrator GO + SPLIT `advanced` yield; (2) Must mint fresh `X/n_s/sess_<NEW_JOB>.json` (112 GCS sessions) BEFORE releasing held job; (3) Watch `/project/community` (`9.0G` free); (4) Pauses at `WAITING_REVIEW` (`S+4h24m`) requiring gate run + `n_r/review.json` install.
```bash
# Step 1 (Orchard via ossh.sh): verify n_r empty & submit HELD
sbatch --hold /project/community/jjyeung/okh7/x_22c714e1/jn8.sh
# -> captures NEW_JOB (e.g. 176700)

# Step 2 (Trinity w/ verified Orchard mux): mint & install 112 GCS sessions for NEW_JOB
# Note: sess2.sh/sess_job.sh/mint_n.py are rescued under /scratch/jjyeung/preserved_20261128/n_ops_kits_330/
bash /scratch/jjyeung/orch_n30/n_ops10/work/sess2.sh mint <NEW_JOB>
bash /scratch/jjyeung/orch_n30/n_ops10/work/sess2.sh install <NEW_JOB>

# Step 3 (Orchard via ossh.sh): byte-verify kit + confirm n_r empty + release
timeout 60 bash .../ossh.sh 'bash -s' < /scratch/jjyeung/preserved_20261128/n_ops_kits_330/n_review1n/work/o_confirm35.sh
# Require: ALL_MEMBERS_OK, unlisted/missing empty, only t_db42866fd9e8d009.tar, n_r empty, sess_<NEW_JOB>.json mode 600
scontrol release <NEW_JOB>

# Step 4 (at WAITING_REVIEW, ~S+4h24m): run gate & install X/n_r/review.json
bash /scratch/jjyeung/preserved_20261128/n_ops_kits_330/n_review1l/work/gate/run_gate.sh <NEW_JOB> /tmp/gate_<NEW_JOB>
python3 /scratch/jjyeung/preserved_20261128/n_ops_kits_330/n_review1n/work/make_review_n1n.py /tmp/gate_<NEW_JOB> ea058fed0495be92fd22c71546fd1bbab449970c566319fc857ddd2a6a551591 /tmp/gate_<NEW_JOB>/review_<NEW_JOB>.json
# Install review_<NEW_JOB>.json -> /project/community/jjyeung/okh7/x_22c714e1/n_r/review.json (mode 600)
```

### 4.2 `E02` — LIBERO Test L (`45e92888780e`, `B1`/`B0`/`U1`, 4× H100 `advanced` or `preempt`)
**Pre-Checks & Blockers:**
- **Disk Warning:** With `/project/community` at `9.0G` free, `train_arm.sh` evaluates in-job (`eval_plan.sh` runs in same allocation) but **will skip saving `final_model` (`<80G`)**. Wrap or pass GCS export step (`gs://cmu-gpucloud-jjyeung/vla_libero/`) before job exit, OR run `EVAL_IN_JOB=1` so the 500-ep + 376-ep `+Cam` scores land in `$V/runs/<id>/` (`<50 MB` JSONs)!
- **`U1` Blocked:** `train_arm.sh` refuses `U1` without `WHERE_CACHE`. Requires single-GPU `vla_where` `T-11` (`P-5`) + `P-1..P-4` LIBERO replay pre-checks + `d5_s0` frame cache (`~3–6 GPU-h` on `general`) first.
- **Exact Commands (Orchard via `ossh.sh`; override `-p preempt --qos=preempt_qos` to run on `preempt`):**
```bash
# B1 shake-down (1k steps, 100 paired eps, ~3.6 H100-h) — step-544 heads dropped:
sbatch -J a15_cot_apb1sd01 /project/community/jjyeung/45e92888780e/bind/train_b1_544.sh B1 d5_s0 1000 17

# B1 decisive (10k steps, 500 paired + 376 +Cam eps, ~21 H100-h):
sbatch -J a15_cot_apb1d501 /project/community/jjyeung/45e92888780e/bind/train_b1_544.sh B1 d5_s0 10000 17

# B0 base reference (user-approved VLL_RULING=user_20261111_base_yes; can run on preempt):
sbatch -J a15_cot_apb0d501 -p preempt --qos=preempt_qos --export=ALL,VLL_RULING=user_20261111_base_yes \
  /project/community/jjyeung/45e92888780e/kit/train_arm.sh B0 d5_s0 10000 17

# U1 (ONLY after WHERE_CACHE built via vla_where P-1..P-5 + cache_frames.py):
sbatch -J a15_cot_apu1d501 --export=ALL,WHERE_CACHE=/tmp/where_cache_d5_s0 \
  /project/community/jjyeung/45e92888780e/kit/train_arm.sh U1 d5_s0 10000 17
```

### 4.3 `E02` — R2R-CE `navrun` Test N (`preserved_20261128/b15_vla/navrun`)
**Pre-Checks & Blockers:**
- **Env Sync Required on `2-28`:** Pull `1-18:/scratch/jjyeung/envs/nav_habitat024` over `.ib` to `2-28:/scratch/jjyeung/envs/nav_habitat024` (and update `cd` / `PYTHONPATH` in `run.sh` to `/scratch/jjyeung/preserved_20261128/b15_vla`).
- **GPU Gate Before Decisive Test N:** `navrun` rendering (CUDA EGL) + depth-occlusion oracle-click ceiling + real tokenizer/model path on `rand100` (`~5 GPU-h` on `2-28` `vnice` or Orchard `general`), plus applying `student_pilot_nav_mode.patch` for prompt parity.
```bash
# Step 1 (trinity-2-28, 0 MB/s NFS): pull habitat env over .ib
ssh trinity-1-18.ib 'tar cf - -C /scratch/jjyeung/envs nav_habitat024' | tar xf - -C /scratch/jjyeung/envs

# Step 2 (CPU verify on 2-28 after pointing run.sh to preserved_20261128/b15_vla):
./run.sh -m unittest discover -s tests && ./run.sh -m navrun.audit --output out/tables/scene_audit_cli.json

# Step 3 (GPU CUDA-EGL rand100 smoke & val_unseen_600_s0 N1/NU eval, wrapped in vnice.sh on 2-28):
/data3/shared/scripts/vnice/vnice.sh ./run.sh -m navrun.evaluate --config configs/N1.json \
  --list out/lists/rand100.json --policy <local_adapter:make_policy> \
  --journal out/n1_rand100.jsonl --output out/n1_rand100_results.json --render
```

### 4.4 `E05` — `DA3` / `Point4D` Teacher Cache Readiness Note
- **`Point4D` (`5.797G`), `Any4D` (`7.727G`), and `MoGe-ViT-L` (`1.257G`) weights are already verified in `gs://cmu-gpucloud-jjyeung/ae/` (`US-CENTRAL1`)**, ready to pull directly onto Orchard `preempt` compute-node `/tmp` at `0 MB/s` Trinity internet cost (remember to redirect `HF_HOME`/`TORCH_HOME`/`XDG_CACHE_HOME` to `/tmp` on Orchard).
