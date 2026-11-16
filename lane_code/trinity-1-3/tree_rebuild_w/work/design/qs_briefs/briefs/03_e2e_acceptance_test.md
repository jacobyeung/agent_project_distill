# Build brief 03: the end-to-end acceptance test (EAT-1) for any leg we claim

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. CPU build; the test's GPU run needs a card and ORCH's word.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU and no Orchard submission without an ORCH GO. Read named files only. Lane folder `/scratch/jjyeung/orch_n30/e2e_test`; events `B/events/e2e_test/`.

## Why
User, 2026-11-16: the product is one trained model that runs its own train of thought and uses its own heads; it calls no external tool and has no agent loop. Today's routed calls are served by a Python runtime: SAM 3 proposals read from a cache, a fitted logistic selector, an alias table, G3T lifting with `tower_scale_rule.json`, a depth cut and a fitted box policy, a gravity guard, a room rule and fallback rules, printed back as `<tool_response>`. That runtime is harness. Every leg we claim must pass a test that says so mechanically.

## The test (pass means every clause passes on the exact artifact and reader of the claimed read)
- **A1, one artifact.** An audit hook records every file opened after `generate()` starts. Every data file is inside the checkpoint artifact by sha256: language model, vision encoder, heads, connectors, frozen towers. Code files are listed by sha256 and fall under A3. Any other data file fails.
- **A2, one call.** `generate(frames, question)` returns the answer. The model is entered once; no prompt is rebuilt from parsed output; a call is handled by a module registered on the model that writes the response into the running sequence while the key-value cache continues.
- **A3, fixed math only between heads and tokens.** The call handler may use a reviewed allowlist: unprojection with the head's intrinsics, rigid transforms, norms, minimum or argmin over point sets, unit conversion, rounding and number formatting. A static scan fails on any loaded table of numbers (JSON, NPZ, pickle), any constant outside a short reviewed list of format constants, and any branch on a threshold chosen on data. Selectors, alias and phrase tables, scale rules, vote and box policies, depth-cut constants, proposal settings, room rules and heading rules must be parameters of a head in the artifact, or absent.
- **A4, no guard and no outside fallback.** No response is produced by a rule that refuses or substitutes. A status such as "not seen" may appear only as the formatted output of a head. What follows a status is the model's own continuation. The scored answer is the generated one.
- **A5, ablation proof.** (i) With every directory outside the artifact unmounted, outputs are identical. (ii) Perturbing one head's weights changes the responses that name it and no others. (iii) Towers run inside the call; a cache may speed a read only after a recorded equality proof against the live path on at least 50 items, and a claimed number comes from a live run.
- **A6, report.** Per type: call rate, the head behind each response field, seconds per item; PASS or FAIL per clause with the offending file and line.

## Inputs
- The current reader, as the failing baseline: kit C8r at `B/events/native_r2/c8r_kit/` (code_c8r.tar sha256 f4535bc0..., PIN_TABLE_C8R.md, GUARD_CALL_SITES.md); `distill_design/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`; `B6_GROUNDING_DESIGN_20261115.md` section 4.1 (the backend's parts and settings); `POLICY_AUDIT_20261115.md` (every choice in the routed path); `CONTRACTS_REBUILD_20261115.md` (guard, heading policy, phrase normalizer, candidate universe, box bridge in the next-leg tree); `REFREEZE_PREREGISTRATION_20261115.md` (C1 to C5).
- The next-leg tree for the A2 audit: package `tree_rebuild_b5_ba346bd9.tar` on trinity-1-3 `/scratch/jjyeung/orch_n30/tree_rebuild_w/out/` and trinity-1-18 `/scratch/jjyeung/n30_mirror/tree_rebuild/` (build 6 when it lands; `B/events/tree_rebuild/STATUS.md`).

## What to build
1. `eat1/`: the audit hook (file opens with sha256, model-entry counter), the static scanner with its allowlist file, the ablation runner, and the report writer. It wraps any reader that exposes one `generate` entry.
2. `BASELINE_C8R.md`: EAT-1 run statically and on a tiny model against C8r, listing every violation by clause, file and line. Expected from the records: A1 fails on the selector tables, `tower_scale_rule.json`, the alias table, the box policy, the mask cache, and towers outside the export; A3 on the selector, depth cut, box policy, room rule, proposal settings, phrase normalizer and heading rule; A4 on the gravity guard, the reader's fallback arm and threshold statuses; A5 on the cache. A2 is unverified: establish it.
3. `BASELINE_A2_TREE.md`: the same static audit of the next-leg tree's inference and export paths. GF-1 runs the tower inside the forward and should pass; state what the routed types inherit.
4. `RUN.md`: how an operator runs EAT-1 on a GPU against a real artifact (200 items covering every type that emits a call), with the time estimate.

## Tests
Unit tests per clause with a passing toy reader and one planted violation each (a loaded table, a second model entry, a fitted threshold, a guard, a cache read); the scanner must flag all five and pass the clean toy. A CPU run on a tiny model end to end.

## Do not touch
Running jobs (D0 170111, the VSTI read, K1), sealed kits (audit copies only), the registered records.

## Deliver
`out/EAT1_READY.md`, both baseline reports, a mirror on a second node, STATUS.md, one RESULT event. Review: one refute review by another model family of the clause definitions and the allowlist; the user's wording decides any dispute, so quote it.
