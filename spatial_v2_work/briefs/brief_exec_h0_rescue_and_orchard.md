# Lane: exec_h0_rescue_and_orchard (Hour-0 Asset Rescue + Orchard Priority Readiness & Launch Prep)

## Mission
Execute the urgent Hour-0 asset protection and live Orchard launch-readiness verification so ZERO expiring kits are lost tomorrow (Nov 29 / Dec 01) AND we can claim our Orchard H100 priority (`4 advanced + 1 general + preempt`) immediately!

## Hard Cluster, IO & Safety Rules (MANDATORY)
- **ZERO DELETIONS:** Never run `rm`, `rmdir`, `unlink`, `shred`, `truncate`, `git clean`, or python deletions. Use `mv` into a backup subdir if clearing a stale file.
- **NO GIT COMMANDS.**
- **SHARED 30 MB/s NFS/INTERNET CAP** (shared with `trinity-0-13` SPLIT orchestrator):
  - All node-to-node copies MUST use compute InfiniBand `.ib` tar pipes (`172.16.1.x` — 0 MB/s NFS cost!). NEVER `rsync`/`scp` between nodes over NFS/eth.
  - NEVER run broad NFS scans (`find`, `du`, `ls -R`, `grep -r`) on `/home` or `/data*`.
  - Use `timeout 60 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh '<cmd>'` for ALL Orchard SSH calls (1–2 batched calls total, never loop!).
  - Do NOT cancel SPLIT's Orchard jobs yet without verifying our exact launch command and notifying `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_CVPR_ORCH_20261128.md` first — this lane's job is to **RESCUE expiring assets** and **PREPARE & VERIFY exact ready-to-submit commands** for `E01` (Vehicle N `w35`), `E02` (`LIBERO Test L` `45e92888780e` + `navrun Test N` + `vla_where` `P-1..P-5`), and `E05` (`DA3`/`Point4D` teacher cache)!

## Exact Tasks
1. **Nov-29 `/scratch` Cleaner Rescue (via `.ib` tar pipe -> `trinity-2-28:/scratch/jjyeung/preserved_20261128/`, `0 MB/s` NFS):**
   - Check sizes and presence on `trinity-1-18` (1 batched SSH call with `timeout 90` to clear `ssh_rate_gate.sh`! Check `du -sh /scratch/jjyeung/orch_n30/b15_vla /scratch/jjyeung/orch_n30/tree_rebuild10_w` and `ls -la /scratch/jjyeung/orch_n30/b15_vla`) and `trinity-3-30` (1 batched SSH call checking `du -sh /scratch/jjyeung/n30_mirror` and top subdirs).
   - If `b15_vla` (`navrun`, `vla_where`, `vla_heads`, `dyn_probe`, etc.) is <= 150 GB and fits cleanly in `trinity-2-28:/scratch` (1.8 TB free!), **immediately pull `b15_vla` over `.ib` (`trinity-1-18.ib` -> `trinity-2-28:/scratch/jjyeung/preserved_20261128/b15_vla`)** using `tar cf - ... | tar xf -` so our VLA kits are safe AND locally available on `trinity-2-28`! (For any directory >150 GB, report its exact size & subdirs first without copying yet!)
2. **Dec-01 GCS `gs://cmu-gpucloud-jjyeung/ae/` Cloud-Side Check (1 batched Orchard SSH via `ossh.sh`):**
   - Using `export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud`:
     - Check `gcloud storage ls -l gs://cmu-gpucloud-jjyeung/ae/` and `gcloud storage buckets describe gs://cmu-gpucloud-jjyeung --format='value(lifecycle)'` to verify exact lifecycle / expiry dates and exact object list!
     - Check Orchard live `squeue -u $USER`, `df -h /project/community ~`, and verify the EXACT files inside:
       - `/project/community/jjyeung/okh7/x_22c714e1/n` (Vehicle N kit `w35` `ea058fed`, `jn8.sh`, `n_r/` state!)
       - `/project/community/jjyeung/45e92888780e` (`LIBERO Test L` kit `e6bccd3d`, `bind/train_b1_544.sh`, `B0`/`U1` scripts!)
       - `/project/community/jjyeung/okh7/` eval kits (`x27ret`, `313db5a47f11ff0c`, `d9c35d0a`).
     - Check if `/project/community` free space (22 GiB) blocks `Vehicle N` or `Test L` submission (both should write heavy checkpoints to `/tmp` + `gs://`!).
3. **Deliverable — Exact Readiness & Launch Packet:**
   Write a crisp report (max ~180 lines) to:
   `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/exec_h0_rescue_and_orchard.md`
   Containing:
   - What was rescued over `.ib` (exact paths, sizes, sha/file counts) and what still needs rescue (with sizes).
   - GCS `ae/` lifecycle verification & exact cloud-side copy command (if needed before Dec 01).
   - Verified exact `sbatch` / launch commands + preflight checklist for:
     1. **`E01` Vehicle N (`w35`, 4× H100 `advanced`)** — exact command & any blockers
     2. **`E02` LIBERO Test L (`45e92888780e`, `B1`/`B0`/`U1` on `preempt`/`advanced`)** — exact command & pre-checks
     3. **`E02` R2R-CE `navrun` Test N (`b15_vla`)** — exact command & pre-checks

Print a concise <=18-line summary to stdout when done.
