# Distillation orchestrator handoff, 2026-11-04 08:00Z (00:00 PT)

Orchestrator 0e. This file replaces DISTILLATION_HANDOFF_20261103_1200Z.md as the current state. Read memory MEMORY.md first. Its 11-03/11-04 entries hold the rulings below.

## 0. Rulings in force (user, 11-03 night)
1. **AWS is copy-only** ([[aws-down-until-user-says]]): no training or GPU jobs there. Copy everything of value to Mind via GCS. The user runs `AWS_REMOVE.sh` after Mind verification. Don't copy re-downloadable data or the optimizer states of runs we won't resume. The user removes those directly.
2. **No GCP IAD** (removal risk). **Orchard is the only H100 source.** Its compute nodes cannot read GCS (403). The user may run `gcloud auth login` there.
3. Mind: /lab_data/tarrlab has ~17.7 TB free (shared). Cap copies into Mind at 50 MB/s aggregate. /user_data/jjyeung (99%) and /home/jjyeung (89%) are full; no copy uses them.
4. Main (agent-project-9f) has priority on the shared Gemini key. The collector is capped through `MAX_WORKERS_OVERRIDE` (main set it to 8). Timer `sgv2_keyshare_timer` writes 84 at 14:00Z.
5. Trained weights of the best runs matter most.

## 1. Lanes
| Lane | Where | State |
|---|---|---|
| cp4tk_launch (Opus) | Orchard advanced | Waits for prep job 165075 and F17_OK (`/scratch/jjyeung/cp4tk_build/logs/f17_to_orchard.log`, tmux `tk_f17` starts after `fs2_up` ends). Then smoke, submit `rt/SUBMIT_TK.sh --submit`, babysit. Docs: `/scratch/jjyeung/cp4tk_build/{HANDOFF,PRELAUNCH}.md`. 160,586 traced rows + 39,872 head rows, init f17, ~785 steps, ~170 H100-h. GO ≥65.8 official with gap categories ≥69.1; NO-GO <64.8. m2800 is the dev reference |
| aws_return_copy2 (Opus; succeeded aws_return_copy at 08:50Z, which used `/scratch/jjyeung/aws_return_copy/HANDOFF.md`) | AWS→GCS `gs://cmu-gpucloud-jjyeung/aws_return/`, GCS→Mind `aws_evac/` | **Update 08:50Z:** tunnel restored. The dr2 directors on AWS (23395-23397) upload by themselves and survive tunnel loss. ~2.4 TB is in GCS (1.2-1.4 GB/s). Mind has 8 objects verified and runs ~28 MB/s, which needs checking. The user removed batch 1 (874 files, 81 GB). Copy rule (user): copy what needs GPU compute to rebuild, or can't be rebuilt; skip public data, duplicates, CPU-rebuildable data and resume states. t6 goes to GCS only; t7 prestage is not copied. `ssh orchard` now works from Trinity nodes (alias added to ~/.ssh/config). Earlier state: | Tier 1 (m2800 AF000_00.tar, FT-X-E2 m1200 AF001_00.tar) is in GCS and the Mind fetch is running. The other 11 weights, records and e7a are uploading via AWS-side jobs. The **Mac tunnel stalled at 07:37Z**; the user must restart it. Then the lane starts its self-driving AWS uploader. Workdir `/scratch/jjyeung/aws_return_copy/` (LANDED.tsv, AWS_REMOVE_READY.tsv, AWS_REMOVE.sh, EXCLUDED_FINAL.tsv). AWS is now cluster aws-iad-slurm-1; data at `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap`; the tunnel lands on 3-30 with a forward on the 0-13 master |
| finals upload (tmux `fs2_up`, no agent) | 0-13 → GCS `finals_2nd/` → Mind `aws_evac/trinity_finals/` | f17 first, then f15, f12, e3, f18, f19, f03, at ≤6.96 MB/s. Log `/scratch/jjyeung/finals_secure/gcs/run_all.log`. Second copies of f17/f15/f12/f18/e3 are on 0-13 `/scratch/jjyeung/finals_2nd/`. f19 and f03 are single copies on 3-30 until uploaded |
| orchard_data2 (Opus, ~206K tokens, rotate soon) | Orchard + 0-13 GPUs 0-2 (tmux od2_render*) | ProcTHOR v3: Objaverse box check, gen_pipe on renders_o5/w1, Trinity renders. Reports v3 counts |
| Mind storage survey (Opus) | Mind | Free space reported. Still measuring /user_data; removal list to `/scratch/jjyeung/mind_storage/REPORT.md` |
| SPLIT-Gemini collector | 0-13 tmux -L v3 sgv2_collector | ~61.4K ok, 80.7% strict. 8 workers until 14:00Z |

## 2. Key facts
- The AWS loss audit is `/scratch/jjyeung/aws_loss_audit/REPORT.md`. Every score survives. CPDM m2800 and FT-X-E2 m1200 were recovered on the AWS return. DATA_MAP line 134 was corrected.
- The no-AWS compute plan is `/scratch/jjyeung/noaws_plan/NOAWS_PLAN.md`. Orchard advanced gives ~85 GPU-h/day; the preempt queue is useless (32 GPUs ~11-09); the general slot has 12 h jobs.
- The GCP probe is in `/scratch/jjyeung/gcp_setup/` (paused by the user). The code-gcp ProxyCommand opens a head-node ssh, which agents must never do.
- 0-13 /scratch is at ~128 GB free. After Mind verifies f17/f15/f12/f18/e3, give the user the command to remove `/scratch/jjyeung/finals_2nd/` (~89 GB).
- The next run after CP4T-K should add ProcTHOR v2/v3 (53K+) and Hypersim v3 (37.7K) rows, with the synthetic share capped.

## 3. Open questions (ours)
- Orchard `gcloud auth login` by the user (default: f17 over the tunnel; checkpoints on Orchard NFS + local disk).
- Does "no more training" also stop Orchard? Default: no, Orchard continues.
- GCS egress cost (~$300 to Mind). Default: use GCS for speed and clear it after Mind verification.
