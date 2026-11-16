# Build brief 09: RL kit (GRPO-style with reward-filtered rounds), correctness plus a chain-length term; built now, run later

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. A build to have ready; no run without ORCH's GO and a registered card.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU, no Orchard job without a GO. Lane folder `/scratch/jjyeung/orch_n30/rl_kit`; events `B/events/rl_kit/`.

## Why
User, 2026-11-16: SFT gives the foundation (long chains that use the model's own heads); RL then rewards correctness and shorter chains, so the model becomes efficient once it knows how to use its heads. Published evidence on our base: Video-ORA-9B goes from 68.1 to 73.1 on VSI-Bench between 9K and 100K RL prompts after SFT; ConsiSpace gains 5.4 over its SFT (`SOTA_SURVEY_GEOMETRY_VLMS_20261109.md`, `MODEL_IMPROVEMENT_PLAN_20261111.md` section G). The earlier kit RFT-1 was lost with trinity-2-18; its record is `RFT1_KIT_20261111.md`.

## Design (fixed here; deviations go in the record)
- **Rounds, not an online loop.** Round r: sample K rollouts per prompt from export r on single cards; score; update on Orchard's four H100 with the sealed trainer; export r+1. This matches the hardware: sampling is single-card, read-only and resumable, so it fills Trinity 48 GB cards under vnice and Orchard general; updates need the four-GPU trainer.
- **Two update modes from the same rollouts.** (a) Reward-filtered rows: keep the best-rewarded rollout per prompt when it is correct, write it as a training row, train with the SFT trainer unchanged. (b) GRPO: group-normalised advantages over the K rollouts, policy-gradient loss on the model's own tokens (response spans carry no loss), KL to the SFT export. Build (a) first; (b) needs a loss path in the trainer and its own review.
- **Path forcing for exploration.** Half of each prompt's rollouts start from a forced first span: the type's head call, or the direct opening. Forced tokens carry no policy-gradient term; the choice is learned from which path earned more. Without forcing, a path with under 5% probability is almost never sampled in a group of 8.
- **Reward.** r = c x g - lambda x max(0, n - n_min(path)) / n_ref, where c is the benchmark's own score (MRA for numbers, exact match for options), g is 1 if the trace passes the grammar validator and its answer follows from the values it cites (RFT-1's provenance and counterfactual-replay checks) and 0 otherwise, n counts tokens the model generated (printed responses are free), and n_min is the shortest valid trace of the path taken. The length term applies only when c x g > 0, so a shorter wrong answer never beats a longer right one. Since responses are free, a correct head call is cheaper than a long verbal estimate: the length term favours head use where the head is right.
- **Open point for the user (asked once in the queue record):** a length reward with no floor ends at empty thinking wherever a direct answer ties. Default: the floor n_min keeps one Locate or Call line, in line with the trace ruling's no-answer-only rule.
- **Prompt pool.** Ground-truth questions on reserve scenes (brief 10) that no SFT stream of the lineage trained, benchmark rooms excluded. Reason: on training scenes the direct path has memorised answers, so reward there would prune head use for the wrong reason. Types weighted to the gap: counting, appearance order, object size, route planning, relative distance, direction including away, absolute distance, room.
- **No-information baselines, reported every round.** Reward of the train-fitted constant answer per type; reward of rollouts on shuffled videos; share of kept rollouts per path and per answer bin against the pool's histogram (collapse check).
- **Stop rule for a run (registered before it).** After round 1's update, the dev-S1 direct read and the guard read against the round's init: stop if F1 fails, if reward rises while the dev read falls, or if any type's grammar-pass rate drops below 95%.

## Compute shape (estimates; measure in the dry run)
- Sampling: a direct rollout takes about 0.5 s on an H100 at today's 57-token median chain (4,008 items in 35 minutes, job 170008) and 1 to 2 s with longer chains; a head-path rollout about 7 s with towers live (job 170056), 1 to 2 s with per-clip tower outputs cached. 10K prompts x 8 rollouts is about 35 H100-hours or about 80 A6000-hours: eight Trinity cards for ten hours under vnice, resumable per draw. 100K prompts is ten times that.
- Update: the SFT trainer on Orchard advanced, about 146 GPU-hours per 1,000 steps (four H100, 131 to 140 s per step). A round of 300 steps is about 45 GPU-hours.
- A first run of two rounds at 10K prompts: about 70 H100-hours of sampling (or 160 A6000-hours) plus 90 of updates. The published gains used 9K to 100K prompts.

## What to build
1. Sampler on the native decode path with path forcing, seeds derived from prompt and draw index, atomic per-draw commits, resume, per-clip tower cache; runs on one 48 GB card and on Orchard general.
2. Reward module with the validator, provenance and replay checks, the length term and its floor; constants-baseline and shuffled-video tools.
3. Selector and row writer for mode (a), in the current row schema; the mixture stays inside the trainer's admitted families.
4. GRPO loss for mode (b) as a patch to a copy of the next-leg tree (never the sealed tree), with CPU tests on a tiny model: advantage normalisation, masked forced and response tokens, KL term, exact resume.
5. `RUN.md`, a draft registration card, and a dry-run packet (200 prompts, one card, one hour) that measures seconds per rollout for both paths.

## Tests
Reward unit tests with planted cases (correct long, correct short, wrong short, answer detached from its trace, empty think); sampler interruption and resume; a tiny-model round end to end on CPU (sample, score, select, one optimiser step, export, reload); the every-rank CPU first batch of mode (a) rows through the trainer's full forward.

## Do not touch
D0 job 170111, the VSTI read, K1, sealed kits and trees, the registered records. ReVSI and every benchmark item stay out of sampling and fitting.

## Deliver
`out/RL_KIT_READY.md`, hashes, the dry-run packet, mirror on a second node, a design record in `distill_design/` with one INDEX line, STATUS.md, RESULT events. Review: one independent refute review (another model family) of the reward and the GRPO loss.
