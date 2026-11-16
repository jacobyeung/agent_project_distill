# b09_rlkit STATUS (successor resumes from this file alone)
Updated 2026-11-16 12:12Z by the headless Claude Opus lane on trinity-3-30. About 30% done.
L = /scratch/jjyeung/orch_n30/b09_rlkit (lane folder, node-local). E = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b09_rlkit/.
Brief: orch_n30/briefs/b09_rlkit.md, which points to orch_n30/briefs/qs/09_rl_kit.md (the build brief; read it). Rules: ~/.claude/CLAUDE.md "Key Trinity Cluster Rules", orch_n30/tools/CLAUDE_LANE_RULES.md, orch_n30/tools/LANE_RULES.md. Finish or rotate by 22:30Z.

## Goal
Build, not run, the RL kit: a sampler on the native decode path with path forcing; the reward (c x g minus a floored length term); the mode (a) selector and row writer; the mode (b) GRPO loss as a patch to a COPY of the next-leg tree; tests; RUN.md; a draft card; a dry-run packet (200 prompts, one card, one hour). No GPU, no Orchard, no Git, no deletion.

## Done (all in L; CPU only)
- Next-leg tree build 5 copied over IB from trinity-1-18:/scratch/jjyeung/n30_mirror/tree_rebuild/: L/work/tree_b5/tree_rebuild_b5_ba346bd9.tar, sha256 bc31a06dd37e742dbf8bad493cbe5d90c18b2bf1dbb6b9f7ef992137a0b33726 (equal at both ends). Extracted read-only at L/work/tree_b5/x/work/tree_r1.
- Kit package L/rlkit:
  - common.py: hashing, atomic writes, derive_seed(run seed, prompt id, draw).
  - store.py: per-draw atomic commits with checksum and config hash; resume refuses a changed config or a corrupt commit.
  - forcing.py: draw_path (half the draws forced, alternating head and direct); SamplingChoice (forced first span, then seeded temperature/top-p, then a token budget); align (per-token kinds f/s/b/r); sampling_hooks, which let the tree's public carrier_c1_decode.generate accept the choice object.
  - sampler.py: CLI `python -m rlkit.sampler --config --prompts --out --shard i/n --max-seconds`. NativeBackend binds evalpath.runtime.load_model and prompt_batch of the tree named in the config. The base sealed tree b01ce449 has a working evalpath; tree build 5 disables evalpath (r2_policy.unsupported_entry). The prompt schema is rlkit-prompt-v1. Benchmark sources and excluded scenes are refused.
  - towercache.py: per-clip memory and disk cache for frozen-tower outputs.
  - score.py: MRA (VSI-Bench arithmetic) and option exact match, using the vendored parser.
  - gate.py: termination; the vendored validator a41ba191 (sha pinned in rlkit/vendor/__init__.py); provenance (a numeric chain from printed values, the gap argmin/argmax, the nearest numeric option, a direct detached-answer check); counterfactual replay (printed values x1.37, or a candidate swap).
  - reward.py: r = c*g - min(lam*max(0,n-n_min)/n_ref, 0.5*c*g); r = 0 when c*g = 0.
- Tests in L/rltests: run `bash L/rltests/run.sh rltests.test_sampler rltests.test_reward`. 13/13 pass. The tests cover determinism, batched equals sequential, interrupt and resume, config change refused, benchmark prompts refused, and the planted reward cases.

## In flight
Nothing. There are no tmux sessions, Codex dispatches, governor streams or Orchard jobs.

## Next steps (in order)
1. rlkit/floor.py, per the user's ruling (ORCH NOTE 1155Z item 5). For each type and path, sweep the length L on held-out rollouts. n_min is the shortest L whose cumulative accuracy stays within delta of the type's best, floored at the tokens of the required head calls (head path) or one Locate line (direct path). Print the table, which shows how the floor is set.
2. GRPO patch: copy L/work/tree_b5/x/work/tree_r1 to L/grpo_tree. Add student_pilot/grpo_loss.py, plus a hook in carrier_c1.py forward (routing/vqa streams) used when the batch carries aux_pg_advantage, aux_pg_mask, aux_old_logp and aux_ref_logp. Tiny-model tests (base on tests/test_carrier_c1_final.py final_fixture) cover advantage normalisation, the masked forced and response tokens, the KL (k3) term and exact resume.
3. rlkit/select.py, mode (a): keep the best right rollout per prompt and write the row in the current schema. Direct rows go to the VQA schema (see work/tree_b5/x/fixtures/rows/slices_v3/d0_retrace_*.jsonl). Program rows use the ground schema of the routing family. Head rows on direct-majority types go to a quarantine file until brief 08's validator amendment passes.
4. rlkit/baselines.py: train-fitted constants per type, a shuffled-video manifest builder, and the collapse table. Then a tiny end-to-end round on CPU (sample, score, select, one optimiser step, export, reload).
5. RUN.md, the draft card, the dry-run packet, a design record in distill_design/ with an INDEX line, a mirror on a second node, and a RESULT event that asks ORCH for a cross-family refute review of reward.py, gate.py and the GRPO loss.

## Rulings and defaults in force
- USER 2026-11-16 ~12:00Z (ORCH NOTE 1155Z): ReVSI first; frame count must be a parameter (32 and 64). The sampler takes frames from the prompt row and the kit config, so the count is a parameter. SFT first, and RL kits are built ahead, not run. No post-processor converts answers. Add a method that sets the length-reward floor.
- Default: the length term is capped at 0.5*c*g, so a right answer always stays above a wrong one. This is a deviation from the brief's formula and is recorded in reward.py.
- Default: categorical option answers in program traces fail the gate (unsupported_projection) unless allow_stated_option=true.

## Notes
- The rm_guard hook queued two false-positive lines in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md: a python edit that removed an unlink call, and a heredoc that wrote STATUS.md. Neither deletes anything, and neither needs action.
