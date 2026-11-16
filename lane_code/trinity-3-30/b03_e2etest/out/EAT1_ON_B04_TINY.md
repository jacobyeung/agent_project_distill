# EAT-1 on lane b04_e2ehook's end-to-end reader (tiny CPU kit) — passes A1, A2 and A5; fails A3 and A4

The b04 reader (`/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader`, read-only import) passes the clauses C8r fails structurally. It loads only artifact files, enters the model once, and writes every response id through the registered `call_hook` module with zero injected tokens. Its heads are causal: perturbing scale_head changed 5/5 naming responses and 0 others, and selector_head changed 3/3 and 0 others. It still fails A3 and A4 on code it inherits from the tree, on hard-coded frame counts, and because its G3T tower is not a registered module.

Run: `work/b04_tiny2/run4/EAT1_REPORT.md`. Adapter: `eat1/adapters/b04_tiny.py`, which mirrors b04's `tests/test_tiny_e2e.py` kit: a tiny Qwen3 LM with the real Qwen3.5 tokenizer, K1 G3T outputs as the tower fixture, and tiny scale and selector heads. It uses a script module on `lm_head` that advances only on sampled tokens. b04's own test forces tokens with a logits processor instead, which EAT-1 would count as injected. The extra allowlist `eat1/adapters/b04_allow.json` marks `artifact.load_tensors` as a loader of artifact files. Items: one each of camera (move, turn, pose), ground (2 grounds + gap), room (unserved) and direct.

| Clause | Status | Evidence |
|---|---|---|
| A1 | PASS | 2 artifact files and 32 code files opened after generate() started; 0 outside data |
| A2 | PASS | 1 model entry per item; 0 injected tokens; responses come from the `call_hook` forward |
| A3 | FAIL | 39 findings. b04 code: 32 frames hard-coded in `e2e_reader/geometry.py:64,67,71,95,96` and `grounding.py:133` (blocks USER ruling 2, 32/64 frames); `MAX_CALL_TOKENS` window `callhook.py:91`. Inherited tree code: the depth stencil estimator (±10 px, P20/P50/P80) at `student_pilot/geometry_profiles.py:178-183`; yaw and turn printed in degrees (`carrier_c1_routing.py:264,300`, `trace_format/box_v313.py:97-98`) |
| A4 | FAIL | Camera and ground responses cite `g3t`, which is not a module registered on the model (the tower runs as a function in `Perception`), so A5 (iii) cannot see it run. Statuses `not seen` and `box unavailable` come from `trace_format/box_v313.py:226-227,518` rather than from a head. `artifact.py:198` (`_guarded`) is flagged by name; the reviewer decides |
| A5 | PASS | (i) The sandboxed rerun is identical. (ii) Scale and selector heads change only the responses that name them. (iii) No declared tower is cited |

Fixes that would move b04 toward PASS:
1. Register G3T (and SAM 3) as tower modules on the model, and cite them.
2. Take the frame count from the read config, and let it drive `geometry.py` and `grounding.py`.
3. Print yaw and turn as the head outputs them, or as a head-defined unit; the model converts to degrees.
4. Make the depth estimator a head parameter, or drop it.
5. Format `not seen` statuses through a head-status formatter.
