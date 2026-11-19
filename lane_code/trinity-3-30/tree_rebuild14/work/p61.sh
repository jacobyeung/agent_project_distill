R=/scratch/jjyeung/orch_n30/tr14_rev24j; date -u +%TZ; mkdir -p $R; cp /scratch/jjyeung/orch_n30/sb_cursor_probe/AGENTS.md $R/AGENTS.md; ls $R
cat > $R/PROMPT.md <<'EOPX'
# Independent review (read-only, once) of a TREE change that produces admission evidence: build 24j of lane tree_rebuild (vehicle N's host receipt, ORCH RULING 1943Z Option T)

You review; you do not fix or design fixes. You are a different model family from the builder, and this change produces the evidence an admission gate reads, so the orchestrator requires your review. You run once, read-only, on trinity-1-18. Report only verified problems, each with file:line and the command or reading that shows it. Your final message is the verdict.

## What changed
- Base tree: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j_back/work/tree_r1_base` (seal 57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7). Changed tree: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j_back/work/tree_r1`. Patch, report and evidence: `x24j_back/out/{HOST24J.patch,BUILD24J_REPORT.md,UNCHANGED24J.json,TREE24J_SEAL.json,ROUTING_SELECTION_PIN.json,KIT_WIRING_24J.md}`. The merged kits are in `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/` (build 24k: `BUILD24K_REPORT.md`, `kit_n_go`).
- Gate: launch_r1/entry.py admit() requires `r1_training.host_receipt` with status PASS, config_identity == identity(cfg), all seven ASSERTIONS (entry.py:9) true and loader_audit.complete. Before 24j only entry.frame_host() (kit mode p) ran those checks, on a config that never trains. 24j makes the production path (launch_r1/production_proof._run, kit mode q) run the tree's own host checks and emit the receipt after the final bind_handover, for the config that trains.

## Ruling conditions to verify
1. The change moves who runs the seven host assertions and when the receipt is emitted; nothing else. admit(), identity(), row legality, exclusions, routing policy, sampling and scoring are byte-identical (recompute the sha256 of every file yourself and compare with UNCHANGED24J.json). frame_host's behaviour in mode p is unchanged and its tests pass.
2. Each of the seven assertions is computed from real evidence at a point where that evidence exists: the fresh job root and namespace before staging, the disk plan, runtime binaries, scene division, the regenerated routing selection against the approved pin, and the directory modes. None is set true by default or copied from another result. Tests make each one false and see a refusal by name; a receipt for any identity other than the final config's is refused; no receipt is written unless bind_handover has completed; the loader audit in the receipt is the final config's.
3. The routing-selection pin: either a digest recorded by P's routing receipt ca0616db, or a regeneration recipe that independently selects the rows P trained (routing base ca0616db, database 4e8e6c04). Say which, and whether the assertion could pass on a different selection.
4. The kit wiring (24k) consumes exactly the native receipt and keeps every h.py refusal. Nothing in the kit writes or edits the receipt. If `w24/out/BUILD24K_REPORT.md` does not exist yet, report item 4 as NOT CHECKED (the lane gets it reviewed separately).
5. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM; use `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` to run the tree's tests if you need to. Write your verdict to `VERDICT.md` in this folder and nowhere else. First line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
EOPX
sha256sum $R/PROMPT.md | cut -c1-16; which agent
cd $R && tmux new-session -d -s tr14_rev24j "OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 timeout 5400 agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh 'Read PROMPT.md in this folder and carry out the task it describes, completely.' > cursor.log 2>&1"
sleep 10; tmux ls | grep tr14; tail -c 300 $R/cursor.log
