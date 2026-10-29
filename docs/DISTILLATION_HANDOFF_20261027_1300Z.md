# Distillation handoff, 2026-10-27 13:00Z (10-27 06:00 PT)

This handoff replaces `DISTILLATION_HANDOFF_20261025_0230Z.md`. The writer is orchestrator agent-project-distill-52 (Claude session 48e156e2, trinity-0-13). Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; R2 = `/lustre/fsw/portfolios/av/users/jyeung/ap/c4f1a9e2` (AWS). Times are PT.

## 1. User rulings in force (newest first)

- **04:00 10-27:** "200 tonight until 6:30" is agent_project's TOTAL, so distillation takes at most 168 until 06:25. Day rule after 06:25: agent_project at most 32, distillation 16. Trinity is the long-term store; Mind is optional overflow. Allowed Trinity nodes: 0-13, 2-18, 2-23, 3-3, 3-30.
- **04:00 10-27 (try everything):** perception heads, both training-only and called inside reasoning (no point-cloud head; depth per patch or region); an open-model cascade (Gemma 4 / Qwen with our tools, k=3, keep traces that agree with the released answer, escalate to Argon); GT re-answering of all VSI-590K; Gemini (Argon) keeps running. Answer-only GRPO is filler, or a baseline when needed.
- **03:05 10-27:** one throttled copy at a time may run while live jobs read /data*, inside the IO governor's tier limits.
- **03:00 10-27:** released answers (VSI-590K and other datasets) are legal targets ("they are the correct answers"), but every training example must carry a trace; no answer-only fine-tuning. The freeze ablation is LoRA-on-vision versus frozen. Warm start is r1835. Quality bar: an open-source per-row checker on AWS, chosen by accuracy against frontier-labeled traces. The 80% audit bar is dropped.
- **~01:10 10-27:** "aws should def do all the training - we only have 4 weeks left with access to aws" (access ends about 11-24). Orchard only finishes what is queued there. At 00:05: "are we training on aws? gpus are free!" Also: "just change the name of the file ... I'm telling you you can use these GPUs. Just don't have a split in the name."
- **Goal 10-27:** fine-tune our VLM to SOTA or close on VSI-Bench and generalize across spatial benchmarks, using GT traces to supervise the visual quantities a question needs. References: sim2reason.github.io, arXiv 2608.02980.
- **Standing:** Trinity admin rules (10 MB/s per user, writes count double, SSH caps); questions never block; no deletion; legality and admission changes take one independent review.

## 2. Results

- **SELF_V4 s17 (Orchard):** arm 56.24 vs control 59.67 on VSI-500, -3.43 [-6.53, -0.31]; VSTI -4.53 [-8.43, -0.55]; counting -14.8. Thinking hurts: thinking minus no-thinking is -3.81 on VSI.
- **Oracle (`L/perchead_20261027/out/ORACLE_TABLE.md`, SELF_V4 s17):** model-only 56.86/55.37. GT values swapped into the model's own trace: 64.51 (+7.65 [6.15, 9.00]) on VSI, counting 36.8 -> 98. GT premises with model reasoning: 95.92/97.20. Perception is the bottleneck. Query slots must precede decisions (appearance order needs times before ordering; relative distance needs per-candidate distances); angle-to-label is a reasoning gap.
- **Literature review** (`/scratch/jjyeung/litreview_20261027/LITREVIEW_SOTA.md`, trinity-0-13). Levers ranked: task-balanced GT data; pose/geometry auxiliary; geometry encoder; curriculum; frames; grounded boxes. A frozen encoder is fine. VSI-500 is not comparable to full VSI-Bench (5,130).
- **Control:** 59.67 = r1835 warm start (93,655 rows, 22.6% VSI-590K questions) plus 384 steps on 12,270 rows. r1835 alone scores 59.51.
- **AWS throughput:** the frozen trainer ran `scontrol show job` on every rank per microbatch; closure fd333954a589 caches it, giving 15-19 s/step (Orchard 16.6). No divergence from Orchard; eval 20/20 identical (`L/awstrain_20261027/EQUIVALENCE.md`). Runbook: `L/awstrain_20261027/AWS_TRAINING_RUNBOOK.md`. sbatch: `--gres=gpu:4 --cpus-per-task=32 --mem=256G`, never `--exclusive`. Multi-node 2x8 over TCP sockets ran 32.4 s/step (no NCCL net plugin); the EFA test and a single-node world-8 test are queued by the rung1 builder.
- **Checker pilot (`L/perrow_checker_20261027`):** best is Qwen3.5-397B FP8: held-out precision 0.928, recall 0.80, yield 0.609 (gate 0.65), with a post-hoc config caveat. Frozen in `FROZEN_CHECKER_v1/`; fresh validation on Argon v1.1 is running (`VALIDATION_STATUS.md`): at least 34/40 GO, 30-33 HOLD, under 30 NO-GO.
- **Gemma template defect:** the served `prithivMLmods/gemma-4-31B-it-FP8` ships an old chat template; the google rev 842da37 template (sha256 ae53464b...) fixes ```json tool calls that never execute. The Qwen3.6 template is byte-identical to upstream.
- **Data collected:**
  - S2V self-sampled verified traces c3: 25,700 questions / 63,005 samples at `R2/v/out/c3r1`, pulled to trinity-0-13 `/scratch/jjyeung/s2vnext_20261027/pulled/c3r1`; archive copy to `/data3/jjyeung/aws_lane2_20261025/pool/s2v_c3_k1/` queued. A CPU pass on 3-30 for the 181 scenes missing from the AWS pack is approved.
  - Gemini (`vsi590k_gemini_20261027`): 27,273 kept of 36,054 answered by 05:31; audits 34-39/40. Robotics camera 17,581 done; Hypersim hyp1 about 15k/h; room 63 IO-limited. Exclude the 777 Hypersim relative-direction and absolute-distance rows at admission.
  - VSI-590K GT re-answer (`vsi590k_gt_20261027`): 225k answerable from GT, agreement 92-100% by type; ARKit 45,965 traced rows built. ADT is blocked on the user's Project Aria signup.
  - Open-model cascade (`vsi590k_cascade_20261027`): pilot audit 24/40, then 39/40 after `trace_filter.py`; binary questions need 3/3 agreement.

## 3. Lane map

| Lane | Where | State | Check | Next |
|---|---|---|---|---|
| awstrain_20261027 | code-aws; `eval_sched.py` pid 811882 on 0-13 | 2222 x4 published 05:11-05:18; SELF_V4 s17 pair about 05:45; MIX about 06:10-06:35 | `results/SUMMARY.tsv` | Evals in order 2222, SELF_V4, H-aux, MIX; readouts (arm minus control, paired CI); the vision-frozen control needs an AWS install of e343b549 |
| perchead_20261027 | code-aws | H-aux s17/s18 training (8379519/20) about 06:05; H-reason2 prepped | head accuracy probes | H-reason2 runs on the day share or after 18:30 |
| rung1_build_20261027 | 3-3 runner | Last input stageC_list_c2 (152.7 MB, governor priority 10) waits; trainer batch branch 6e7786b5 (batch 256 needs microbatch 8) | build log on 3-3 | Full build, then AWS prep of A1 (GT-template traces), A2 (vision frozen), A3 (perception targets), a small yardstick; launch 18:30 at world 32 / batch 256 if EFA works |
| selfv_20261025 | Orchard via 2-23, tmux `selfv_lane` | SELF_V4 s18 control evaluating; MIX hb jobs queued at nice 100 | `orchard/FAMILY_READOUT_SELF_V4_S18.log` | Readouts land by themselves |
| vsi590k_gemini | 2-18, unattended | Hyp1 running; STOP file `/scratch/jjyeung/v590g_20261027/STOP` | lane HEARTBEAT | Next media after hyp1: ProcTHOR (6.5 GB), approval pending |
| vsi590k_gt | 3-30, tmux `-L v590kgt` | Waits on governor copies | lane log | Runs when copies land |
| vsi590k_cascade | 3 nodes | Scaled until 06:25 | lane log | Resumes after 18:30 |
| d8_tranche | 3-30 | Cut queued behind the governor; count overlay (value_unrounded) prepared | `PIPELINE.log` | On "copy done", resume the d8 lane for admission review and `apply_d8.py` |
| tracebank r38 reader | 2-18, tmux `tracebank_r38` | Paused for d8 (CONTROL=hold) | `L/tracebank_20261021/work/restart_2-18_20261027/CONTROL` | Write "run" to resume |
| selfv final checkpoint copy | paused | 9.4 GB to `/data3/jjyeung/distill_final_ckpts` | governor | Resume later through the governor |

## 4. Survives versus dies at session close

- **Survives (detached):** Orchard jobs; AWS jobs and `eval_sched.py`; the Gemini run on 2-18 (STOP file stops it); tmux runners on 3-3 and 3-30; the cascade.
- **Dies with this session:** the Claude lane babysitters, the heartbeat cron and the queue watcher. A successor re-creates the heartbeat, resumes the AWS cap rule (16 by day), and re-reads `results/SUMMARY.tsv`.

## 5. Open user decisions

- ADT signup links.
- ProcTHOR download approval (default yes when hyp1 drains).
- The n13 question on replacing the lanemsg-tell-all rule (orchestrator-n13's saved question).
- The main-repo questions in `SAVED_USER_QUESTIONS.md`.

## 6. Footguns

- IO governor at `/data3/jjyeung/orch_n13_20261026/io_governor` (`REGISTER.md`). Register every copy with a stopped reader, pv_pid, expected_bytes and priority. Never park pv at `-L 1`. Slot-exempt downloads need kind "download".
- Never SIGSTOP an ssh client on the shared code-aws master (it hung the master 05:00-05:10; fix: kill the master).
- Process cap on trinity-0-13: user total about 200; keep distillation under 24 there; lanes run no background sleep-waiters and do only AWS-touching work.
- AWS caps: at most 16 for distillation by day, a night share from the main orchestrator (agent-project-90). Count pending jobs too (an eval batch once pushed us to 215/168). `eval_sched.py` is the single eval submitter.
- No lanemsg broadcasts (each scans 2,800 files on /data2); message agent-project-90 by SendMessage.
- The rm guard queues false deletions in `/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md` (a junk `rm -rf /dev/null`, pycache, partial files): dismiss them.
