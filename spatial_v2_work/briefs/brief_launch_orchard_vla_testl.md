# Lane: launch_orchard_vla_testl (Orchard H100 Launch & Babysit: LIBERO Test L B1 Shake-Down -> B1/B0 Decisive)

## Mission
Claim our user-granted **Orchard full priority** (`4× H100 advanced` + `preempt`) cleanly with SPLIT and launch our **FIRST decisive student VLA runs (`KT-3` / `E02` LIBERO-Spatial `Test L`)**!
Specifically:
1. Coordinate cleanly with SPLIT (`trinity-0-13`) BEFORE submitting/cancelling.
2. Inspect `/project/community/jjyeung/45e92888780e/bind/train_b1_544.sh` and `kit/train_arm.sh` on Orchard (via `0-13 -> ossh.sh` since `2-28` NFS gcloud hangs!) to verify:
   - Exact partition/QoS/GPUs (`advanced`, `4× H100`),
   - All caches (`HF_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR`, `PIP_CACHE_DIR`, `XDG_CACHE_HOME`) write to node `/tmp` (`6 TB` free), NOT `~` (`25 GB`) or `/project/community` (`9.0 GiB` free),
   - In-job OSMesa evaluation runs and saves JSON results (`<50 MB`) even when `/project/community` has `<80 GiB` free!
3. Launch **`B1` shake-down (`1,000` steps, `100` paired eps, ~1h wall-clock on 4× H100 `advanced`)** (`sbatch -J a15_cot_apb1sd01 /project/community/jjyeung/45e92888780e/bind/train_b1_544.sh B1 d5_s0 1000 17`) so we prove the entire Orchard VLA pipeline end-to-end and get real closed-loop LIBERO numbers within 1 hour!
4. Also check `preempt` queue availability: if clean, submit **`B0` base reference (`1,000`-step matched shake-down OR `10k` full)** on `preempt` (`VLL_RULING=user_20261111_base_yes`) — OR wait for `B1` shake-down to hit step 100 cleanly first so we verify zero script bugs before queueing `10k` arms! (YES: verify `B1` shake-down reaches step >=20 cleanly first!)

## Mandatory Launch & Monitoring Cadence (USER-RULING 2026-11-25)
- Catch failures quickly and finish experiments as fast as safely possible:
  - Check **BOTH Slurm/process liveness AND training steps/loss landing in the log** every **1 minute** after launch/start!
  - **Two empty one-minute checks (or any crash/OOM/stuck queue) = debug immediately!**
  - If SPLIT's `176609/176637/176638` haven't auto-yielded within 3 minutes after our submission AND our `advanced` job shows `QOSMaxGRESPerUser` / `Resources`, run the pre-authorized `scancel 176609 176637 176638` via `ossh.sh` and immediately log the exact stop-notice line to BOTH `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_CVPR_ORCH_20261128.md` and `/data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md`!
  - Once `B1` shake-down is stably stepping (`step >= 50` with decreasing finite loss and healthy GPU util), switch to **5-minute checks** (or report back cleanly once step >= 50 is verified with measured `steps/min` and exact ETA so the orchestrator can track/trigger `B1 10k` + `B0 10k`!).

## Hard Cluster, IO & Safety Rules (MANDATORY)
- **ZERO DELETIONS** (`rm_guard`), **NO GIT COMMANDS**, **NO broad NFS scans**.
- **Orchard SSH rule:** NEVER run `ossh.sh` directly on `trinity-2-28` if `/home/jjyeung/google-cloud-sdk` hangs — run 1 batched SSH command via `trinity-0-13`:
  `timeout 75 ssh -o BatchMode=yes -o ConnectTimeout=10 trinity-0-13 "timeout 60 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh '<cmd>'"`
  (Respect SSH rate limit: max 1 call per minute, always batched!)
- **Opaque job names:** ALWAYS start Orchard job names with `a15_cot_ap` + random alphanumeric token (NO underscores after `ap`, NO project/benchmark words like `split`, `libero`, `distill`!).
- **Notification before claiming:** Append a timestamped notice to `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_CVPR_ORCH_20261128.md` and send `lanemsg tell --from "distill_orch@2-28" agy:225c9445-f2b8-43f8-a487-5b19fa068e96@trinity-0-13 "<msg>"` BEFORE submitting!

## Deliverable
Write a verified launch & live-progress receipt to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/launch_orchard_vla_testl.md`
Include: exact Slurm Job ID(s), exact command run, SPLIT yield status, verified step/loss/VRAM/throughput log snippet (step >= 50 if running, or full diagnosis if blocked), and measured ETA. Print a concise <=18-line summary to stdout.
