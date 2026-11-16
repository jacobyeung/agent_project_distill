# RL kit ready (rlkit-v1, brief 09): built, CPU-tested, not run

Location: trinity-3-30:/scratch/jjyeung/orch_n30/b09_rlkit (L). How to run: L/RUN.md. Hashes: L/out/HASHES.txt.
Tests: `bash L/rltests/run_grpo.sh rltests.test_sampler rltests.test_reward rltests.test_floor rltests.test_grpo rltests.test_select rltests.test_baselines rltests.test_e2e rltests.test_prompts rltests.test_grpo_rows`: 43/43 OK on CPU. On the patched tree copy, the tree's own suites test_carrier_c1_final, test_carrier_c1, test_carrier_c1_routing, test_batched_routed_decode and test_e2e_routing_rows give 46 OK and 8 skipped, and test_carrier_c1_run gives 13 OK, as on the original tree.

## What exists
| Part | File | State |
|---|---|---|
| Sampler on the native decode path; path forcing; per-draw seeds; atomic commits; resume; per-clip cache | rlkit/sampler.py, forcing.py, store.py, towercache.py, towerfactory.py | built, tested on the tree's tiny model |
| Reward: c (MRA, exact match) x g (termination, validator a41ba191, provenance, replay) minus a capped length term | rlkit/score.py, gate.py, reward.py | built, planted cases pass |
| Length floor from held-out rollouts (user ruling) | rlkit/floor.py | built; FLOOR.md prints how each n_min was set |
| Baselines: constants, shuffled videos, collapse table | rlkit/baselines.py | built |
| Mode (a) selector and row writer | rlkit/select.py | built; direct winners admitted by the tree's grammar |
| Mode (b) GRPO loss as a patch to a copy of tree build 5 | grpo_tree/student_pilot/grpo_loss.py, carrier_c1.py; bridge rlkit/grpo.py, round.py | built; CPU tests cover advantages, masks, KL, sampler parity and exact resume |
| Mode (b) rows in the trainer's stream databases | grpo_tree/student_pilot/grpo_rows.py, hook in carrier_c1_run.Rows.get; rlkit/grpo.py to_row, write_stream_db | built; through the trainer's own fetch and check_row, the batch and loss equal the kit's; tampered rows are refused |
| Prompt pool builder, 32 or 64 frames | rlkit/prompts.py | built; waits for brief 10's R0-rl rows |
| Dry-run packet (200 prompts, one card, one hour) | out/dryrun_packet/ | ready; rehearsed on CPU; export, pool and card unbound |
| Draft card | out/CARD_DRAFT_RL_DRYRUN.md | draft |

## Findings
1. The decoder masks `<tool_response>`, `</tool_response>` and the carrier id before choosing a token. The GRPO loss masks the same ids, so its policy equals the sampling distribution. Without the mask, log probs differ by about 0.05 per token.
2. The trainer admits program rows only with ground-truth responses (`r2_contract.event_row`). A sampled head rollout prints tower responses, so mode (a) cannot train head winners as sampled. They go to program_candidates.jsonl for a ground-truth re-render of the same calls.
3. Only object_abs_distance has a head path in the artifact today. On every other type the forced head slot samples free, so the dry run measures head-path cost on one type only.

## Open before a run
- Bind the export pin and the R0-rl pool (brief 10), then pick a card. The dry run needs an ORCH GO.
- Mode (b) also needs a membership manifest for its GRPO stream databases (r2_contract.Admission refuses unlisted rows), a check on the real processor that grpo_rows.prompt_batch equals the reader's canary prompt, and its own review.
- Mode (a) rows go through the intake (frame pins) and the every-rank CPU first batch on the real export.
- An independent cross-family refute review of reward.py, gate.py and grpo_loss.py.

## Defaults in force
- The length term is capped at 0.5 x c x g, so a right answer always scores above a wrong one. This deviates from the brief's formula.
- A categorical option answer in a program trace fails the gate unless allow_stated_option is set.
- Selection keeps rollouts with c >= 1.0 and never falls back from a head winner to a direct one.
