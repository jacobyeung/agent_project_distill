<!-- recovered by seal_plan: transcript=71f94277 line=28112 utc=2026-11-14T03:27:19.410Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_TASK_packed_four_worker_job_feasibility_first.md heredoc_quoted -->
# ORCH task: a packed four-GPU job after the leg ends; feasibility RESULT first, then build on my word

## Why

Orchard's one-GPU partition is jammed: our two queued jobs there (the step-200 evaluation read, job 169367, and the IF-P0 baseline arm P0, job 169413) are forecast for 16:33Z and 17:59Z. The production leg's allocation ends at 15:25Z (trainer stop about 14:25Z), which frees our cap on the `advanced` partition: four GPUs on ONE node per user, so only one job can run there at a time. To use all four cards, one job must run four single-GPU workers side by side: the step-200 read, the step-400 read, the final-step read, and P0.

## The design I want (simplest that can work; no shared staging)

One `advanced` job (1 node, 4 H100) whose script is a small outer controller. Each worker is an existing, already accepted single-job script run unchanged in its own job step: `srun --exact --gres=gpu:1` with its own CPUs and memory, its own private folder under the job's `/tmp`, its own token and its own bounded result return. Workers stage their own inputs (duplicate staging is accepted; it is about 90 GB of extra reads and saves a shared-path design). The controller only: checks the allocation and the job's private mount once, starts the steps, records each step's GPU UUID, enforces a per-worker deadline, waits for all, and writes one small controller record. A worker's failure must not touch another worker; the controller never writes into a worker's folder.

The evaluation lane's own plan is `/scratch/jjyeung/orch_cd/evalx/work/milestone/PACKED_ADVANCED_PLAN.md` (38 lines; read it). It proposes shared staging; I am not taking that part. Take its isolation rules (items 10 to 13) and its measured budgets.

## Step 1 (now): feasibility RESULT, at most 40 lines, no build

Read, read-only:
- the evaluation launcher that produces a single-read job: `/scratch/jjyeung/orch_cd/evalx/work/milestone/orchard_launcher.py`, `orchard_job.py`, `orchard_stage.py`, `orchard_results.py`, and one real submission folder, `/scratch/jjyeung/orch_cd/evalx/work/milestone/submissions/b719d20dd/` (the step-100 read);
- the IF-P0 packet and kit: `/scratch/jjyeung/orch_cd/if_p0/out/P0_SUBMISSION/` and `/scratch/jjyeung/orch_cd/if_p0/out/tree_provenance_v3/kit_ifp0_orchard_job_8d5bdd730bebb9b3/` (`orchard_job.py`, `orchard_job_contract.py`, `orchard_launcher.py`), and `out/SUBMIT_P0_FOR_OPERATOR.md`.

Answer:
1. What each worker script checks about its allocation and environment that would refuse inside a step of an `advanced` four-GPU job: partition name, GPU count, CPU and memory variables, job id use in paths, `SLURM_JOB_GPUS` against CUDA device 0, the `/tmp` mount proof, scheduler output redirection, signals (`--signal=B:USR1@300`), and anything that assumes it is the batch step. Give file and line for each.
2. The smallest change in each owner's code that admits "one step of the packed job" beside "its own general job" (I will order those from the owners and confirm their diffs; you change neither kit).
3. The controller: the exact `sbatch` request (CPUs and memory per worker within the node's 208 CPUs and 1.8 TB; `advanced`, 24-hour limit, no requeue), the `srun` line per worker, how each step gets exactly one distinct card and sees it as device 0, the per-worker deadline, what happens to the others when one fails or when the job receives its end-of-time signal, and where the controller's own record goes (not the project filesystem beyond a few KB).
4. What you would test on CPU here (four fake workers, one failing, one overrunning its deadline, distinct cards, no cross-writes) and what only the real job can show.
5. Your estimate of build time, and what review it needs.

Post the RESULT. I then order the owners' admissions and give you the word to build. No ssh, no network, no agents; nothing in this task touches the running production job or the queued jobs.