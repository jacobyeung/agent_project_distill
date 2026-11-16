# RL kit ready (rlkit-v1, brief 09): built, CPU-tested, not run

Location: trinity-3-30:/scratch/jjyeung/orch_n30/b09_rlkit (L). How to run: L/RUN.md. Hashes: L/out/HASHES.txt.
Tests: `bash L/rltests/run_grpo.sh rltests.test_sampler rltests.test_reward rltests.test_floor rltests.test_grpo rltests.test_select rltests.test_baselines rltests.test_e2e rltests.test_prompts rltests.test_grpo_rows rltests.test_headuse rltests.test_review_refute`: 66/66 OK on CPU, including the reviewer's 13 refute tests. On the patched tree copy, the tree's own suites test_carrier_c1_final, test_carrier_c1, test_carrier_c1_routing, test_batched_routed_decode and test_e2e_routing_rows give 46 OK and 8 skipped, and test_carrier_c1_run gives 13 OK (59 OK and 8 skipped in all), as on the original tree.

## What exists
| Part | File | State |
|---|---|---|
| Sampler on the native decode path; path forcing; per-draw seeds; atomic commits; resume; per-clip cache | rlkit/sampler.py, forcing.py, store.py, towercache.py, towerfactory.py | built, tested on the tree's tiny model |
| Reward: c (MRA, exact match) x g (termination, validator a41ba191, provenance, replay) minus a capped length term | rlkit/score.py, gate.py, reward.py | built, planted cases pass |
| Length floor from held-out rollouts (user ruling) | rlkit/floor.py | built; FLOOR.md prints how each n_min was set |
| Baselines: constants, shuffled videos, collapse table | rlkit/baselines.py | built |
| Mode (a) selector and row writer | rlkit/select.py | built; direct winners become native VQA rows admitted by the tree's grammar; head winners whose responses all come from inside the artifact become exact-token own rows (rlkit-own-row-v1, trained by CE on the routing stream with responses masked); others go to barred.jsonl with the reason |
| Head-use tracking at every eval checkpoint (USER 05:00 PT) | rlkit/headuse.py | built: call rate, heads, placement against the expected sequence, estimate-before-call, counterfactual usage (re-decode with printed values x1.37), reward split by called and not called, curve across checkpoints |
| Mode (b) GRPO loss as a patch to a copy of tree build 5 | grpo_tree/student_pilot/grpo_loss.py, carrier_c1.py; bridge rlkit/grpo.py, round.py | built; CPU tests cover advantages, masks, KL, sampler parity and exact resume |
| Mode (b) rows in the trainer's stream databases | grpo_tree/student_pilot/grpo_rows.py, hook in carrier_c1_run.Rows.get; rlkit/grpo.py to_row, write_stream_db | built; through the trainer's own fetch and check_row, the batch and loss equal the kit's; tampered rows are refused |
| Prompt pool builder, 32 or 64 frames | rlkit/prompts.py | built; waits for brief 10's R0-rl rows |
| Dry-run packet (200 prompts, one card, one hour) | out/dryrun_packet/ | ready; rehearsed on CPU; export, pool and card unbound |
| Draft card | out/CARD_DRAFT_RL_DRYRUN.md | draft |

## Findings
1. The decoder masks `<tool_response>`, `</tool_response>` and the carrier id before choosing a token. The GRPO loss masks the same ids, so its policy equals the sampling distribution. Without the mask, log probs differ by about 0.05 per token.
2. The trainer's program-row family admits only ground-truth responses (`r2_contract.event_row`), so sampled head rollouts need their own family. The kit adds one: exact-token own rows read by `grpo_rows.py` inside `carrier_c1_run.Rows.get`. The selector admits a head winner only when its recorded response sources (pose source, mask source, ground backend and query backends, call kinds, no donor) all lie inside the artifact (`select.ARTIFACT_POLICY`).
3. Only object_abs_distance has a head path in the artifact today. On every other type the forced head slot samples free, so the dry run measures head-path cost on one type only.

## Review
review_rl (Devin Opus, cross-family) returned GO AFTER FIXES on the 1327Z tar: events/review_rl/REVIEW_VERDICT_RL.md. Every fix landed, each with the reviewer's failing test, which now passes (rltests/test_review_refute.py, sha 5a03c1cc):
1. The gate refuses any <tool_response> span that the decoder did not force, in order and byte-equal (gate.forced_mismatch).
2. GRPO rows pass select.artifact_policy and carry response_sources, and the trainer re-checks them (grpo_rows.check_sources).
3. Draws and rows record the sampling temperature and top_p. The loss default is 0.7, the sampler's. aux_pg_temperature is required and must equal the loss setting.
4. A trace whose every call failed takes the path 'recovery': it is charged against the direct floor, trains as an own row only under the artifact policy, and never counts as head use (headuse.head_call).
5. Draws record grounding provenance (geometry_source, geometry and mask-source identities, query provenance, presence sources, verify/reread/tower state). The policy admits only same-checkpoint geometry and the native MDG source of the same artifact, and admits the own grounding head without a backend.
6. Rows keep their own source and dataset. Sources are normalised before matching (revsi, vsibench, vstibench, vsti, devs1, dsibench, official999). The pool builder, the floor's DEV set and the baselines' fit set are all checked.
7. floor --pool is required, and FLOOR.json records the held-out and pool sha256.
8. Numeric options project only the final derived value, and its x1.37 replay must move the option.
9. The constant baseline's r scores the cheapest constant trace through the same gate and reward, taking the best over the objects the question names.
Minor fixes: the reward cap claim is restated; usage decodes greedily on both arms and counts unparsed answers apart; sampling.max_calls is gone (decode.max_calls rules); check_own re-checks the sources.

## Open before a run
- Bind the export pin and the R0-rl pool (brief 10), then pick a card. The dry run needs an ORCH GO.
- Mode (b) also needs a membership manifest for its GRPO stream databases (r2_contract.Admission refuses unlisted rows), a check on the real processor that grpo_rows.prompt_batch equals the reader's canary prompt, and its own review.
- Mode (a) rows go through the intake (frame pins) and the every-rank CPU first batch on the real export.
- A confirmation pass of the fixes by the reviewer (ordered; see STATUS.md).

## Defaults in force
- The length term is capped at 0.5 x c x g, so a right answer always scores above a wrong one. This deviates from the brief's formula.
- A categorical option answer in a program trace fails the gate unless allow_stated_option is set.
- Selection keeps rollouts with c >= 1.0 and never falls back from a head winner to a direct one. Head winners on direct-majority types train too (no quarantine unless --quarantine-direct-majority).
- The length floor is set per path, so a head path's n_min already includes its required call tokens, and the length term charges only the excess. headuse's reward split shows whether the term still pushes the policy off its heads.
