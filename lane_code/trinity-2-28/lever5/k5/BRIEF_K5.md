# Build K5: tower-alone history/determinism job on the 60 rank 1 captures (lever5; ORCH RULING 2026-11-21T18:48Z item 4)

You are a build subagent of lane lever5 on trinity-2-28. Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`.

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states. For you: NO stream, NO ssh, NO Orchard call, NO Git, NO GPU, no deletion. If you need an Orchard fact, stop and list the exact read-only command in your final message; lever5 runs it.
- No recursive grep/find/du/ls -R on /home or /data*. Write only under /scratch/jjyeung/orch_n30/lever5/k5. Python: /scratch/jjyeung/envs/p1cpu/bin/python, threads <= 8, nice -n 10. Do not modify anything under lever1_c (it is sealed and placed on Orchard).
- Orchard opacity: no project, benchmark, dataset, model or method word in any file shipped to Orchard or in any job name; job names `a15_cot_ap` + a new opaque hex token; numeric filenames; keep the existing kits' opaque-word scan and extend it to your files.

## Starting point
The rank 1 depth-dump package: /scratch/jjyeung/orch_n30/lever1_c/r1 (REPORT.md, PLACE.md, DEBUG.md, build_depth.py, runtime/, orchard/o_*.sh, SHA256SUMS). It ran as Orchard jobs 174135/174200/174208 (token a3b73b53d92a7 = same code as a4282fee306d6), each bit-identical on two nodes. It dumps the served G3T geometry for 60 captures in production order (ScanNet/ScanNet++ 64 frames, ARKit 32). The tower call is in the payload (tower_read.py; bf16 autocast on CUDA at tower_read.py:246). Evidence of the effect to test: /scratch/jjyeung/orch_n30/lever5/out/HISTORY_DIAG.txt. The served tower's output depends on prior call history in the process: capture 0 matches T1 bit for bit, and later captures differ (up to 0.117 m on ARKit).

## What K5 must do (one GPU job, general, 1 H100, <= 50 min)
Tower alone, with no language model, on the same 60 captures, inputs, weights and environment as the rank 1 package. Four arms, each in a FRESH Python process started in sequence by the job:
- A1: production order, default settings (exactly as served).
- A2: reversed order, default settings.
- D1: production order, deterministic settings.
- D2: reversed order, deterministic settings.
Each arm also recomputes capture 0 (production index 0) once more at the end of its sequence, which tests history inside the arm.
Deterministic settings: name every switch in the report and set each before the first CUDA call: torch.backends.cudnn.benchmark=False, torch.backends.cudnn.deterministic=True, torch.use_deterministic_algorithms(True) with CUBLAS_WORKSPACE_CONFIG=:4096:8, and whatever else the tower code leaves to chance (inspect it: TF32 flags, SDPA backend selection, cuDNN or cuBLAS workspace, allocator, any seeded or random op). Keep bf16 autocast as served; it is part of the served numerics, not chance. If use_deterministic_algorithms raises on an op, record which op, and run that arm with warn_only=True. Say so.
Record per arm and capture: K, camera_to_world_metric, camera_to_world_unscaled, scale, a sha256 of each output array's bytes, seconds for the tower call, and peak GPU memory. Record arm wall time.

Scorer (local, CPU; write the rules into the report before any run):
- Bit-equality and max deviation (translation m, rotation deg, K, scale) per dataset (ScanNet, ScanNet++, ARKit): A1 vs A2 and D1 vs D2 per capture; each arm's final capture-0 recompute vs its first.
- A1 vs the rank 1 dump (lever1_c/r1/returned/0.gz) per capture, which validates that tower-alone reproduces the dump.
- A1 vs D1.
- Cost: per-capture tower seconds, D vs A (mean, median, max) per dataset.
- Answers: (1) do the deterministic settings make the two orders agree bit for bit? (2) what do they cost in time per capture?

Job terms (same as rank 1): the Orchard CPU check runs the REAL first unit on CPU (capture 0 through the real tower in the pinned environment, finite outputs; on CPU G3T runs fp32) plus staging of all inputs, before the GPU job. Follow the rank 1 kit's write-test, guard, error-record, sacct-fetch and return-authentication conventions. Use --exclude=orchard-community-4 and --mem=200G, never advanced, and a 50-min limit, with forecast x 1.5 under it (rank 1 measured about 10 s per capture after the first; first capture ~105 s incl. load). New bytes on /project <= 50 MB. Reuse the inputs the rank 1 package already placed on Orchard if possible (say how). Return the per-arm records (small JSON, no depth arrays needed) through the existing return path; say whether the return is under 20 MB.

Tests (local CPU): the scorer on synthetic records (equal, perturbed, missing capture), a stub-tower dry run of the 4-arm driver (fresh process per arm, ordering, capture-0 recompute, switches set before CUDA), installer and placement tests, opaque-word scan, shell syntax.

Deliverable: /scratch/jjyeung/orch_n30/lever5/k5/kit/REPORT_K5.md (<= 70 lines: arms, switches, scorer rules, bytes, forecast, tests with results, lane commands in order: place, CPU check, submit, fetch, score), SHA256SUMS_K5, all kit files under k5/kit. Final message: commands, bytes, forecast, Orchard facts needed. Do not narrate history in the report.
