# Compute, Storage & Cluster Inventory (`w1_compute_inventory`)
**Snapshot:** `2026-11-28T12:20Z` (`04:20 AM PT`) | **Home node:** `trinity-2-28`

## 1. Executive Summary: Capacity Claimable IMMEDIATELY
| Tier / Resource | Claimable NOW | Coming Soon | Wrapper / QoS | Primary Best Use |
|---|---:|---:|---|---|
| **Orchard `advanced`** | **4 x H100 80GB** | — | Slurm `adv_4gpu_qos` (24h, 1 node, non-preempt) | 4-GPU 9B/27B SFT & RL legs (Vehicle N / bluesky training) |
| **Orchard `general`** | **1 x H100 80GB** | — | Slurm `general_qos` (12h, non-preempt) | Official VSI-5130 / ReVSI-999 / VSTI-450 evals |
| **Orchard `preempt`** | **Up to 32 x H100 80GB** | Queue-dependent | Slurm `preempt_qos` (48h, 4 nodes, 2m grace) | Checkpoint-resumable training / data-gen shards |
| **`trinity-0-13` (unwrapped)** | **2 x 6000 Ada 49GB** (`0,2`) | **+1** (`6` in ~45m) | **UNWRAPPED** normal priority | Non-preemptible SAM3/G3T towers, fast head/routing probes |
| **`trinity-2-28` (local)** | **4 x 6000 Ada 49GB** (`4,5,6,7`) | — | **`vnice.sh` REQUIRED** | Local 4-GPU dev/eval/training with **1.8 TB** local `/scratch` |
| **SPLIT-reserved other 49GB** | **5 x 49GB** (`0-18:4-7`, `0-8:5`) | **+4** (`1-18:4-7` in ~4h) | **`vnice.sh` REQUIRED** (see policy note §3) | Parallel eval shards, teacher inference, pseudo-labeling |
| **Google Gemini API Key** | **Unlimited $** (`24/7`) | — | `gemini-agent` (`neon`/`carbon`/`argon`/`hydrogen`/`flash`) | Trace rewriting, 2D point/box labeling, cross-family audits |

**Immediate Guaranteed GPU Footprint:** **5 non-preemptible H100 80GB** (Orchard `advanced` 4 + `general` 1) + **2 unwrapped 49GB Ada** (`0-13:0,2`, rising to **3** in ~45m) + **4 local `vnice` 49GB Ada** (`2-28:4-7`) + **5–9 remote `vnice` 49GB** = **16–21 large GPUs** (+ up to 32 `preempt` H100s).

---

## 2. Orchard Cluster Status & Priority Protocol
- **Priority Ruling (`2026-11-28 04:12 AM PT`, `INBOX_TO_DISTILL_ORCH_20261128T1209Z_gpu_split.md`):** User granted **Distillation FULL PRIORITY over Orchard**. Main also released its general slot earlier (`INBOX_FROM_MAIN_orchard_gpu_slot_released_20261121T1310Z.md`).
- **Live Queue State (`jjyeung`, account `mt01`):**
  - **Distillation jobs:** `0` running / `0` pending (last job `174444` cancelled `2026-11-22T12:11Z` at `WAITING_REVIEW` before step 1).
  - **SPLIT (CVPR Rebuttal) jobs:** `4` single-H100 inference jobs running (`176609` Gemma `:28941`, `176637` Qwen `:28931`, `176638` Qwen `:28932`, `176641` Qwen `:28935`).
  - **Auto-Yield / Preemption Protocol:** SPLIT halted new Orchard submissions and has Lane R1 watching `squeue` to auto-`scancel` its 4 jobs the moment Distillation submits. Distillation is **pre-authorized** to run `scancel 176609 176637 176638 176641` directly if immediate slots are needed (append notice to `INBOX_TO_CVPR_ORCH_20261128.md` or `/data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md`).
- **SSH Connection Note (Why `ConnectTimeout=8` Tripped):** Our 1-shot `timeout 15 ssh -o ConnectTimeout=8 orchard` hit `Exit code 255` during banner exchange because `Host orchard` spawns `gcloud compute start-iap-tunnel` over NFS (~12–20s cold start). **Always use:**
  `timeout 60 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh '<cmd>'`
  (`ConnectTimeout=60`, `ControlMaster` at `/tmp/cm-n30-orchard-%r`, `ControlPersist=60m`; subsequent calls take `<0.5s`).
- **Orchard Staged Kits & Disk Guardrails:**
  - Staged pools live under `/project/community/jjyeung/okh7/` and `gs://cmu-gpucloud-jjyeung/q8/`:
    - **Vehicle N training kit `w35`** (`ea058fed`, tree `db42866f`, milestones `[100,200]`, `jn8.sh`, init P step-400 `6ed2c7aa`, passed 8/8 gate checks): `/project/community/jjyeung/okh7/x_22c714e1/n` (ensure `x_22c714e1/n_r/` is empty before releasing a held job).
    - **Direct/Native eval kits:** `okh7/x27ret` (VSI-5130 `f42aa1a4`), `okh7/313db5a47f11ff0c` (ReVSI-999 `ea1a1b2d`), `okh7/d9c35d0a` (VSTI-450 `native_r4`).
  - **CRITICAL DISK WARNINGS on Orchard:**
    - `~` (`/home/jjyeung`): **25 GB quota** — redirect `HF_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR`, `PIP_CACHE_DIR`, `XDG_CACHE_HOME` to `/tmp`!
    - `/project/community`: **Only ~22–25 GiB free** at last `PROJECT_FS_FREE.txt` log (shared 10 TB NFS, 2-week purge). Stage heavy inputs/checkpoints on **node-local `/tmp` (~6.0 TB free)** and stream durable artifacts to `gs://cmu-gpucloud-jjyeung` (`export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud`).

---

## 3. Trinity 49GB GPU Map & SPLIT Coordination Protocol
- **`vnice.sh` Verified:** `/data3/shared/scripts/vnice/vnice.sh` (`-rwxrwxr-x`). Mandatory on **all** Trinity GPUs outside `trinity-0-13` (and for any usage >16 GPUs cluster-wide). Jobs under `vnice.sh` receive `SIGTERM` if preempted — always checkpoint per-step/per-question.

| Node | Hardware | Total | Free NOW for Distill | Occupied / Other Users | Rules & Notes |
|---|---|---:|---|---|---|
| **`trinity-0-13`** | RTX 6000 Ada (49GB) | **7** (`0..6`) | **2 FREE (`0, 2`)** at `2 MiB`, `0%` (+**`6`** in ~45m) | `1,3,4,5`: `mehark` (`train_flow.py`, ~17GB, 100% util); `6`: SPLIT `sam3_daemon` (`23.6GB`, ~45m left) | **UNWRAPPED normal priority.** **WARNING: `/scratch` has only 69 GB free (96% used)!** |
| **`trinity-2-28`** | RTX 6000 Ada (49GB) | **8** (`0..7`) | **4 FREE (`4, 5, 6, 7`)** at `2 MiB`, `0%` | `0,1,2,3`: `mgaur` (`len9_vla`, ~36GB each, 2d9h) | **Home node. Wrap in `vnice.sh`.** `/scratch` has **1.8 TB free**, `/dev/shm` **463 GB free**. |
| **`trinity-0-18`** | RTX A6000 (49GB) | **8** | **4 FREE (`4, 5, 6, 7`)** *(SPLIT `12:09Z`)* | `0,1,2,3`: SPLIT Lane R4 (Qwen-27B + Gemma-31B) | Reserved for Distill in SPLIT's 50/50 split; **wrap in `vnice.sh`** *(note: `11-10` memory said leave `0-18` free; verify if needed beyond `2-28`+`0-13`)*. |
| **`trinity-0-8`** | RTX 6000 Ada (49GB) | **8** | **1 FREE (`5`)** *(SPLIT `12:09Z`)* | `0,4,6,7`: `yusuf`; `1,2,3`: SPLIT Lanes R2/R3 SAM3 | Reserved for Distill in SPLIT's 50/50 split; **wrap in `vnice.sh`** *(note: `11-03` memory avoided `0-8`)*. |
| **`trinity-1-18`** | RTX 6000 Ada (49GB) | **8** | **0 now** (**+4 (`4..7`) in ~4h**) | `0..3`: `mgaur`; `4..7`: SPLIT Lane R1 (`r3687`, ~4h left) | `timeout 15 ssh` hit `rc=124` in `ssh_rate_gate.sh` (`<=2 new conns/62s`); use `timeout 90` first SSH. |
| **`trinity-0-23`** | RTX 6000 Ada (49GB) | **8** | **0** | `0,2..6`: `adamhung`; `1,7`: SPLIT Think3D/Gemma | Off-limits (`trinity-gpu-priority-rules.md`) + full. |
| **`0-3`, `0-28`, `1-8`** | 6000 Ada / A6000 | **24** | Unscanned (1-SSH budget) | Check `1-8` `/scratch` (was full `11-15`) | Wrap in `vnice.sh` if scanned later via `check_large_gpus.sh --brief`. |
| **`1-13`, `1-3`, `3-23`** | A6000 / 6000 Ada | **24** | **DO NOT USE** | `3-23` other owners; `1-13` GPU hold (`11-16`); `1-3` SSH hung (`11-27`) | Strict off-limits (`1-13` CPU builds only; `1-3` dead to SSH). |

- **Bonus Free Small GPUs (per SPLIT `12:09Z`):** `trinity-2-18` (`7 x RTX 3080 Ti 12GB`), `trinity-3-30` (`4 x RTX 2080 Ti 11GB`, check `/scratch` free first).
- **SPLIT Coordination Protocol (`trinity-0-13` & Cluster):**
  1. Claim `trinity-0-13` **`CUDA_VISIBLE_DEVICES=0,2`** immediately (unwrapped) and `trinity-2-28` **`CUDA_VISIBLE_DEVICES=4,5,6,7`** immediately (under `/data3/shared/scripts/vnice/vnice.sh`).
  2. Do **NOT** touch `0-13` GPUs `1,3,4,5` (`mehark`) or GPU `6` until SPLIT notifies that `r3697c` (`:23697`) has exited (~45m) and confirms whether `2-28`'s `r3694d` (`capped_daemon.py`) is done. Never run broad `pkill`/`pgrep` on `sam3` or `research_proxy_v2.py` on `0-13`.
  3. Two-way coordination with SPLIT orchestrator:
     - Live message: `lanemsg tell --from "distill_orch@2-28" agy:225c9445-f2b8-43f8-a487-5b19fa068e96@trinity-0-13 "<msg>"`
     - Inbox file: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_CVPR_ORCH_20261128.md`

---

## 4. Gemini API Key Readiness (No Dollar Cost Limit)
- **Wrapper & Env Ready on `trinity-2-28`:** `/home/jjyeung/.local/bin/gemini-agent` + local proxy venv `/scratch/jjyeung/envs/gemini_proxy_v1` verified present; **no `OVER_CAP` block** in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/gemini_subagents/`.
- **Live Models Verified:** `gemini-4-neon`, `gemini-4-carbon` (default), `gemini-4-argon`, `gemini-4-hydrogen`, `gemini-3.8-flash` (`gemini-3.1-pro-preview` reserved for Main/SPLIT if 429s occur).
- **Guardrails:** Unlimited dollar budget — scale out trace generation, perception/point labeling (`argon`+`carbon` agreement filter = 96.9% acc), and cross-checks. Watch `proxy.log` for HTTP 429s; keep Gemini File API project storage `<20.5 GB` (prefer inline frame JPEGs over raw MP4 File API uploads).

---

## 5. Storage, Envs & Data Asset Map
- **Node Local Disks:**
  - `trinity-2-28:/scratch`: **1.8 TB free** (`43%` used) + `/dev/shm` **463 GB free** — **stage all active builds, datasets, and checkpoints here.**
  - `trinity-0-13:/scratch`: **69 GB free (`96%` used)** — **DO NOT stage bulk data/checkpoints here;** stream outputs over `.ib` (`172.16.1.x`, exempt from 30 MB/s NFS cap) to `2-28:/scratch`.
  - **7-Day `/scratch` Cleaner Alert:** Vehicle N's Nov 22 sealed tree/resume kits on `1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w` and `3-30:/scratch/jjyeung/n30_mirror/` turn 7 days old on **Nov 29** — archive kept tars to `/data3` (`rsync --bwlimit=4000`, registered with `io_governor` if >20 MB).
- **NFS (`30 MB/s` cluster cap; writes count 2x; register >20 MB streams with `io_governor`):** `/data2` (`977 GB` avail), `/data3` (`17 TB` avail).
- **Ready Environments & Assets:**
  - **Local `2-28` `/scratch/jjyeung/envs/`:** `gemini_proxy_v1`, `planner_local_v1`, `sam3_capretry_native_v1`, `sam3_scipy_ovl`, `k6cv2`, `p1cpu`.
  - **Shared `/data2/jjyeung/envs/`:** `planner`, `sam3`, `vllm`, `mapanything`, `g3t`; offline cache `/data2/jjyeung/huggingface` (141 GB).
  - **Repos:** `/home/jjyeung/agent_project_distill` (distill), `/home/jjyeung/agent_project` (shared runtime/benchmarks).
  - **Videos, Frames & Dense 3D:** `/home/jjyeung/agent_project/map-anything/{vsibench_videos,g3t_scaled_con_dense_outputs,mapanything_dense_373_32_outputs,unik3d_dense_outputs,cutr_dense_373_32_outputs}`, `/data2/jjyeung/agent_project_data/{extracted_frames,frames_cache_restored_20260911}`, `/data3/jjyeung/agent_project_data/{vsiext_frames_20260926,vsiext_media_20260926}`.
  - **Checkpoints & Traces:** `/data3/jjyeung/distill_final_ckpts/` (`f01.tar`, `f02.tar`, `m02..m04.tar.gz`), `/data3/jjyeung/distill_src_archive/`, `/data2/jjyeung/agent_project_data/distill_trace_corpus/` (`INDEX.jsonl`, `reads/`), `/data2/jjyeung/agent_project_data/distill_design/`.
