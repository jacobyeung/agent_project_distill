# Lane cont_ops26 (Devin Opus high, runs on trinity-3-30): vehicle N's export boundary reads (T3)

First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; D = /data2/jjyeung/agent_project_data/distill_design. B/briefs/cont_ops23_d.md binds you in full for the sections "Disk" and "Node safety", the corpus rule (item 4 of its State section), the launch and monitoring cadence, continuity (rotate at 5.5 hours; successor cont_ops27 from this brief) and the events rule. Lane folder /scratch/jjyeung/orch_n30/cont_ops26 (notes only). Read your inbox /scratch/jjyeung/orch_n30/cont_ops26/inbox and B/events/cont_ops/*_ORCH_* at every step.

## State
- The grounding and camera threads are closed (ORCH ORDER 1221Z). Their record is D/GROUNDING_FUNNEL_20261120.md (closing section) and D/TOWER_CAMERA_FAILURES_20261120.md. Do not reopen them without an order.
- Nothing of cont_ops25's runs on Orchard, GPUs or Codex. Its final STATUS is /scratch/jjyeung/orch_n30/cont_ops25/STATUS.md (last section exact).
- Vehicle N: launch question forecast about 16:30Z 11-20, first export about eight hours after the job starts. The orchestrator sends the order with the export's identity.

## T3: boundary reads on N's export
Run them as cont_ops23 ran R1's and cont_ops20 ran step 600's: read /scratch/jjyeung/orch_n30/cont_ops23/STATUS.md, D/READER_R1_20261117.md and B/briefs/cont_ops20_d.md for the read set, kits and order; the kits and tools live in /scratch/jjyeung/orch_n30/cont_ops22/work, /scratch/jjyeung/orch_n30/cont_ops21/work and /scratch/jjyeung/orch_n30/cont_ops/work (symlink), used in place. Fetch, authenticate and score every return before reporting it, then ingest it into the corpus (add_read.sh) and name the read id in the RESULT.

## Orchard facts
- Submission: place (kit o_place.sh via tools/ossh.sh), CPU entry check on general (about 5 min), then submit; one job of ours on general at a time; always --exclude=orchard-community-4 and --mem=200G (a 20G cap failed the K3c check). Check terminal state with sacct, not squeue (squeue -j fails once a job is purged).
- Placement above 20 MB moves as one governed stream (IO governor, --io-weight 1) through ossh.sh; the pattern is /scratch/jjyeung/orch_n30/cont_ops25/work/oplace.sh.
- /project: add no new bytes beyond 50 MB total. Removal candidates (ours): ac794e028b16f (44.7 MB) with ae63d9b7124fc (hard link), a1abb3a204ff8, a5d6f41359166, a883c5c365aee. Pool returns to move to ae71c903_fetched when convenient: a52c1dcfae7bb0002a65ec, ab704caf7807e0002a639c, ac85ad201020f0002a64ec, a5d6f413591660002a632.
- Ledgers: /scratch/jjyeung/orch_n30/cont_ops24/work/ORCHARD_LEDGER.jsonl and /scratch/jjyeung/orch_n30/cont_ops25/work/ORCHARD_LEDGER.jsonl; append yours in your lane folder.
- trinity-2-28's eight GPUs were held by another user's training (11-20); no Trinity GPU without an ORCH ANSWER.

## Limits
No deletion commands (list removal candidates). Ask before heavy IO; one governed stream per pull. At most one Codex round of yours at a time, on trinity-2-28. dev-S1 is held out: nothing becomes a training row. Held-out camera wordings: aggregate by type only. Events only for results, questions, blockers and rotation.
