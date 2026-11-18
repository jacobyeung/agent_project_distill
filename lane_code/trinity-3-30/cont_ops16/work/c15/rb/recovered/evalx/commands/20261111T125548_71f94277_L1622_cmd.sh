<!-- recovered by seal_plan: transcript=71f94277 line=1622 utc=2026-11-11T12:55:48.614Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd && P=/scratch/jjyeung/orch_cd/model_design_review/MODEL_IMPROVEMENT_PLAN_20261111.md && S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad
STAND='## Standing answers (the orchestrator cannot answer a running Codex session)
- You may read this node'"'"'s local disk (/scratch) with one serial process. You write only inside your folder and your private /dev/shm; at most 2 GB under your folder. No GPU, no network, no ssh, no git, no deletion outside your folder, no loopback sockets. /home and /data* are overloaded network storage: open named files only, never search or list recursively there, never write there.
- The newest student code is /scratch/jjyeung/orch_cd/integ_v3/work/tree (read-only; import it through PYTHONPATH or copy the files you need). Its CPU fixtures are tests/cpu_stubs.py and /scratch/jjyeung/orch_cd/integ_v3/scripts/acceptance_cpu_e2e.py (the tiny native Qwen fixture and recorded card generations; they also show which Python environment runs the tree). Evaluation kits and scorers are under /scratch/jjyeung/orch_cd/evalx/work and /scratch/jjyeung/orch_cd/mdg_next/work (read-only; list one level at a time).
- Debug and rerun ordinary failures of your own scripts up to three times. Never hold on a question: decide, and state your assumption in the RESULT.'
mkdir -p rft1_kit/events rft1_kit/work rft1_kit/out diag_kits/events diag_kits/work diag_kits/out
cat > rft1_kit/BRIEF.md <<EOF
# rft1_kit (Codex Sol): build and CPU-test the kit that samples programs from our student, keeps the ones that are right for the right reason, and writes them as training rows (build B4, experiment RFT-1)
Your folder: /scratch/jjyeung/orch_cd/rft1_kit. Read the plan first: $P, sections "RL on top" (from line 219), "Ranked experiment queue" item 7 (line 297) and "Builds to start today" item B4 (line 319), plus "Risks and early signs". The plan is your specification; where this brief and the plan differ, the plan wins, and you say so in the RESULT.

## Why (the user, 2026-11-11)
"we can always do RL on top after to further improve" and "we should preemptively develop all this code and test it! so when it's time to actually run, we don't need to debug and waste time!" The first, cheapest form of RL: sample several programs per training question from a checkpoint that writes head calls, score them against the ground-truth answer, keep only samples that are correct AND whose answer follows from their own tool outputs, and fine-tune on those.

$STAND

## Build (work/rft1/)
1. The sampler: a wrapper around the tree's end-to-end routed decode (headcall/decode.py and the routed generation path the acceptance scripts use) that draws k samples per question with a seed, temperature and nucleus setting from a config, records every generation, tool call and tool output, and resumes after an interruption without redrawing finished questions.
2. The keep rule, as the plan states it: the benchmark scorer's verdict on the final answer; operand provenance (every number used in the final computation traces to an earlier tool output in the same sample); counterfactual replay on CPU (re-execute the sample's computation with perturbed tool values and require the answer to move accordingly); and the report against train-fitted constant answers and ambiguous-question strata, so that guessing the answer prior is not rewarded.
3. Selection and writing: per-type balancing, de-duplication of identical programs, and a writer that emits rows in the current training row format (the v3.13 routed rows; find the writer and schema in the tree and in /scratch/jjyeung/orch_cd/orchard_cp2/events/20261110T2142Z_RESULT_v313_first_batch.md).
4. CPU tests (\`python -m pytest work/rft1/tests -q\`): the sampler on the tiny fixture with recorded generations replayed; the keep rule on hand-built samples (a correct sample; a lucky sample whose operands do not trace; a sample whose answer ignores its tool outputs; a prior-guess); the counterfactual replay; balancing and de-duplication; the row writer's output accepted by the tree's row loader; resume.
5. out/RUN_CARD.md: the exact GPU command for 20,000 programs from CP1 m200, with cards, wall hours and GPU-hours from the plan's measured decode rate, a stall guard on the sampler's output, and the pre-registered rule for using the rows.

## Deliver
- work/rft1/ with README.md, out/RUN_CARD.md, out/RECORD.md (a design record: question, answer, evidence, options considered and rejected, risks and how we would notice, tests that would settle it, status).
- events/<UTC stamp from date -u +%Y%m%dT%H%MZ>_RESULT_rft1_kit.md, at most 12 lines: what is built, the test count and runtime, what each keep-rule test showed, what the GPU run needs, anything unfinished with its reason.
EOF
cat > diag_kits/BRIEF.md <<EOF
# diag_kits (Codex Sol): build and CPU-test two cheap diagnostics that the plan puts before any training (THINK-0 and ARK-1a)
Your folder: /scratch/jjyeung/orch_cd/diag_kits. Read the plan first: $P, "Ranked experiment queue" items 3 (THINK-0, line 274) and 4 (ARK-1a, line 279), "Builds to start today" (line 315, items for THINK-0 if listed and B6 for ARK-1a), "Gap decomposition" (line 95) and "Risks and early signs". The plan is your specification; where this brief and the plan differ, the plan wins, and you say so in the RESULT.

## Why (the user, 2026-11-11)
"how can we improve our current model?" and "we should preemptively develop all this code and test it! so when it's time to actually run, we don't need to debug and waste time!" Two questions can be answered in a few GPU-hours each, with no training: what the model's thinking budget is worth on the question types it answers directly, and whether metric scale on ARKitScenes videos (31% of VSI-Bench items) is right at fixed weights.

$STAND

## Build
1. work/think0/: the kit for THINK-0 exactly as the plan's item 3 defines it (arms, item sets with their counts, frame count, the pre-registered rule with GO, NO-GO and INCONCLUSIVE, cost). Build on the existing evaluation kit rather than a new evaluator: find the cell definitions and the thinking and token-cap settings in /scratch/jjyeung/orch_cd/evalx/work (the aws_vl64o kit is the newest; do not edit it, copy what you need). Deliver cell files, a launch script with a stall guard, a scorer call, and a paired-analysis script that prints the rule's verdict per type and overall.
2. work/ark1a/: the ARK-1a diagnostic script exactly as item 4 and build B6 define it: the scale sources at fixed weights on the ARKit bank and on the ARKit absolute-distance items, CPU first. Find the scale rule in the tree (student_pilot/tower_scale.py and tower_read.py) and the existing scale measurements (the saved result note /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/result-presence-pose-routing-20261110.md reports the own-depth scale ratio on real ScanNet scans and on rendered clips). The script must run today on whatever tower exports already exist on this node's /scratch (say which you found), print the per-scan scale ratio with its gate, and state what a GPU run adds.
3. CPU tests for both (\`python -m pytest work -q\`): the analysis scripts on synthetic paired results with known outcomes (a clear gain, a clear loss, an inconclusive case with too few items); cell files validated by the kit's own checker if it has one; the scale script on a synthetic scan with a known ratio.
4. out/RUN_CARD.md with the exact commands, cards, wall hours and GPU-hours for each diagnostic, and the decision each one changes.

## Deliver
- work/think0, work/ark1a, out/RUN_CARD.md, out/RECORD.md (a design record: question, answer, evidence, options considered and rejected, risks and how we would notice, tests that would settle it, status).
- events/<UTC stamp from date -u +%Y%m%dT%H%MZ>_RESULT_diag_kits.md, at most 12 lines: what is built, test count and runtime, what the ARKit scale script printed on existing exports, what each GPU run needs, anything unfinished with its reason.
EOF
tmux new-session -d -s cx_rft1_kit "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh implement /scratch/jjyeung/orch_cd/rft1_kit /scratch/jjyeung/orch_cd/rft1_kit/BRIEF.md --skip-git-check --label rft1_kit > /scratch/jjyeung/orch_cd/rft1_kit/dispatch.out 2>&1"
tmux new-session -d -s cx_diag_kits "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh implement /scratch/jjyeung/orch_cd/diag_kits /scratch/jjyeung/orch_cd/diag_kits/BRIEF.md --skip-git-check --label diag_kits > /scratch/jjyeung/orch_cd/diag_kits/dispatch.out 2>&1"
printf 'rft1_kit|tmux:cx_rft1_kit||\ndiag_kits|tmux:cx_diag_kits||\n' >> $S/LANES; tmux ls | grep -c '^cx_'