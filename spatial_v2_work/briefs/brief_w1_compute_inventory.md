# Lane: w1_compute_inventory (Read-Only Compute & Cluster Inventory)

## Goal
Survey our FULL available compute footprint so we can immediately maximize **Orchard** (we now have user-granted PRIORITY over Orchard!), **Trinity** (we can take half or more of `trinity-0-13`'s unwrapped 49GB GPUs while leaving some for SPLIT, plus `vnice.sh`-wrapped 49GB GPUs on other Trinity nodes), and the **Gemini API key** (no cost limit).

## Hard Cluster & Safety Rules
- READ-ONLY! Do NOT kill any jobs, do NOT edit repo code, do NOT delete files, do NOT run `git` commands, do NOT run broad NFS scans (`find`, `du`, `ls -R`, `grep -r`, bare `rg` over `/home` or `/data*`).
- Respect SSH limits: at most 1 batched SSH command to `orchard`, and at most 1 batched SSH command to `trinity-0-13` (and if needed 1 to `trinity-1-18`). Always use `timeout 15 ssh -o BatchMode=yes -o ConnectTimeout=8`. NEVER SSH to Trinity head node `trinity`.

## What to Check
1. **Orchard (1 batched SSH call to `orchard`):**
   - `squeue -u $USER -o "%.10i %.14P %.24j %.8T %.10M %.6D %.12b %R"` (what is running/pending right now for jjyeung?)
   - `sinfo -o "%20P %10a %10l %6D %10t %20G %15C"` (available partitions, GPUs, idle nodes!)
   - Check `ls -1 /tmp` or our Orchard workspace/home directory (`pwd; ls -lt ~ | head -n 30`) to see what kits/scripts are staged on Orchard.
   - Check `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/ORCHARD_LEDGER.jsonl` (tail -n 20) and `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_FROM_MAIN_orchard_gpu_slot_released_20261121T1310Z.md`.
2. **Trinity GPUs:**
   - Local `trinity-2-28`: `nvidia-smi` + `ps` on GPUs 0-3 (what is using them right now?) and confirm GPUs 4-7 free + `/data3/shared/scripts/vnice/vnice.sh` exists.
   - `trinity-0-13` (1 batched SSH call): `nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader`, `nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader`, `df -h /scratch`, and check who owns running GPU processes so we know which GPUs SPLIT uses and how to cleanly take >=half without breaking SPLIT!
   - Also check `/data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md` (tail -n 20) and `/home/jjyeung/agent_project/agent/config/sites/` (list files) for Trinity node inventory (which Trinity nodes have 49GB RTX 6000 Ada / A6000 / L40S GPUs).
3. **Storage & Data Readiness:**
   - Check `/scratch` free space on `trinity-2-28` and `trinity-0-13`, and list top-level `/data3/jjyeung/distill_archives` (if exists) and `/data2/jjyeung/agent_project_data` (maxdepth 1 only!) so we know where checkpoints, frames, and training streams sit.

## Deliverable
Write a crisp, actionable compute map (max ~150 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_compute_inventory.md`
Include exact GPU counts (Orchard H100s, Trinity 49GB GPUs on `0-13` unwrapped and `2-28`/other nodes under `vnice.sh`), running jobs, free capacity we can claim IMMEDIATELY, and coordination protocol with SPLIT on `trinity-0-13`.

Print a concise <=15-line summary to stdout when done.
