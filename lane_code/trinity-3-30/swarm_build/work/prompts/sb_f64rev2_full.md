# Task sb_f64rev2: re-review of the 64-frame kit after code fixes (sb_f64fix, Cursor build), read-only
Workspace: /scratch/jjyeung/orch_n30/sb_f64rev2 (write here only). Your first review and scripts: /scratch/jjyeung/orch_n30/sb_f64rev (out/REVIEW_VERDICT.md NO-GO; behavior_check.py, resume_audit.py, anchor_order_check.py, forward_check.py, regression_check.py): rerun them against the fixed kit.
Under review: /scratch/jjyeung/orch_n30/sb_f64fix (out/FIX_REPORT.md, out/sb_f64fix.tar da6405ae..., 45 kit tests, regression logs).
Check each of your 8 findings CLOSED or OPEN with evidence; the store-conversion and token-audit counterexamples now refuse; the MISSING real inputs are listed honestly with owners; the GPU pilot script is sound (FSDP, FP32 masters, Adam, checkpointing, longest rows); claims not backed by files.
Deliver out/REVIEW_VERDICT.md (at most 40 lines): GO (for CPU-side readiness; GPU still waits for real inputs), GO AFTER FIXES or NO-GO.

## Standing rules and answers (read first; you will get no replies, so do not wait for any)
- You run on trinity-1-18 (CMU Trinity cluster), CPU only, no GPU, no network. Never ssh, never kill a process, never touch tmux sessions, no Git, no deletion outside your workspace.
- /home and /data* are an overloaded NFS server: never search, list recursively or bulk-read there. Read only files this prompt names, each once. /scratch is local disk: bounded `rg --files`/`find` under the directories named here is fine.
- Write only inside your workspace. Every path outside it that this prompt names is read-only to you (other lanes own it).
- Local-disk IO needs no approval. Ordinary failures: debug and rerun. The sandbox has no loopback sockets. Stay under 40 GB RAM per process. CPU manners (orchestrator order): at most 8 cores per job; start every heavy process with `nice -n 10` and OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 (torch.set_num_threads(8)); never run parallel worker pools above 8 processes.
- Legality: never invent a mapping, a manifest, a scene list or a proof. A missing input is reported by its exact name and expected location; the affected output says MISSING, never a guess.
- Every output JSON records sha256 of each input it rests on, and your report states the command that produced each number. Write a STATUS.md in the workspace after each stage (one paragraph) and a final report named in the task.
