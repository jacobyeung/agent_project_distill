# Mixed gate (C1 final mode, self-routing): training-critical review

Reviewer: Claude Opus subagent, read-only, 2026-11-08 13:01-13:25Z, on trinity-2-18.

Code reviewed: kit `t_6097446ba8d5ff99574a687be42dd995a4aa0952.tar` (sha256 `87870313…ebea9`, verified), extracted to a scratch copy. 6097446 equals 48a85ca plus the final-mode warning demotions; 48a85ca equals 614cfe4 plus mixdata's pointing patch and the routing frame-root binding. Line numbers below refer to 6097446. Configs: `out/gate/v3/gate_b.template.json`.

## Verdict: GO

I found no blocking item, meaning nothing that changes targets, masks, injected values, contamination or scoring. The non-blocking list is short; items 1 and 2 are cheap and worth doing before step 100, which is when own values first enter training.

## Evidence I added (CPU)

- I checked that the values injected during training match the values the decode loop prints. On the tiny native Qwen fixture (`tests/test_carrier_c1_final.py::final_fixture`), the training path (prefix readout, packed `query_tensor` and slot lookup, `row_geometry`, `rerender`) and the decode path (`HeadState` with `encode`/`query` per click, plus `respond`) were byte-equal on every tool and calculator response of 6 pool-v1 rows, under placements a and b (12/12 rows, 8-12 responses each). The existing test (test_carrier_c1_final.py:163-184) checks only that the target changed. Script: `/tmp/claude-25409/-home-jjyeung-agent-project-distill/cdb578de-f6e0-4670-982e-5058bffd9c5c/scratchpad/scripts/parity.py`.
- I measured call lengths on the real Qwen3.5 tokenizer over pool v1. The longest calculator command is 18 tokens; the decode loop's 24-token tail window (carrier_c1_decode.py:239) covers it. The longest head call is 32 tokens; the limit is MAX_CALL_TOKENS 96.

## The 6097446 demotions remove no correctness check

These five checks now warn instead of refusing: the source seal (carrier_c1_run.py:82), the prep config and commit identity (:297), admission (:331), the allocation pin (:927, :995) and the artifact config identity (:1001).

These checks still block:
- `validate`: mode, stream set, init base, FSDP, all-frames and the `depth_fov_source` pose head (:48-66).
- Stream pins equal to the prep's, plus a re-pin of every database with its count (:299-325).
- Placement, mode, depth_enabled, recipe = prep recipe = `recipe_for(cfg)`, layout, skip_lm, depth_fov_source and depth_init (:299-308).
- Base identity at readout (:999).
- Artifact placement, mode, layout, position policy and depth checks in `load_artifact` (:971-984).
- Every mask assertion.

Every cfg field that affects training is either one of these checks or part of `recipe`: mix, steps, milestones, weights, world size and scheduled_sampling.

## Checks that passed
