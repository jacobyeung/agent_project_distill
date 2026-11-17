# Brief 06 (build, not on the launch path): the scale as a registered fixed-math module, and a residual scale head that starts from it

Carrier: Codex gpt-6-astra, effort high, one `implement` dispatch on trinity-1-3 in `/scratch/jjyeung/orch_n30/scale_r1` (cap 4 GB), by a Devin Opus lane there (new Devin sessions start only on trinity-1-3). CPU only; no ssh, no Git, no deletion. First read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. Start it when a builder is free; legs do not wait for it.

## Why
The claimed artifact scales G3T's geometry by median(own depth / G3T depth) (design record `/data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_DECISION_20261117.md`, section 1.2). EAT-1 passes a number only when a registered head, tower or `fixed_math` module returned it, and the user's 11-16 ruling names a learned scale. b04's learned head (ridge, 31 parameters, 29 features, 233 K1 captures) lost to the rule: K1 distance -1.6 [-4.1, +1.1], dev-S1 displacement -9.3 [-14.1, -5.0].

## Inputs
- b04's reader and heads: the copies already on trinity-1-3 under `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/design/` (`b04_v8/` 961295be, `b04_inputs/` with scale run1; read-only), and for what they lack the mirror trinity-1-18 `/scratch/jjyeung/n30_mirror/b04_e2ehook/` (`e2e_reader/stage1.py` with `OwnDepthScale` and `ScaleHeadCall`, `heads/scale/` with `SCALE_HEAD_REPORT.md`, `tests/price_devs1.py`, `out/proofs/PRICE_DEVS1_old.json`, `SCALE_HEAD_DEVS1.json`); record `E2E_READER_B04_20261116.md`.
- The rule: `student_pilot/tower_scale.py`, `tower_scale_rule.py`, `tower_scale_rule.json` in the tree (copy inside b04's kit).
- The K1 harness and tables on trinity-1-18 (`/scratch/jjyeung/orch_n30/geo_k1/`, `/scratch/jjyeung/k1/`), train and held-out split as E3 used them. The dispatching lane fetches only the tables and cached proofs the fit and the pricing read, as one tar over InfiniBand with `tools/tssh.sh` (check the size first; above 5 GB ask the orchestrator).

## Work
1. **`tower_scale` as a `fixed_math` module** (parameter-free `torch.nn.Module`): inputs own depth grid, G3T depth and confidence; the grid size, the confidence quantile and the two depth bounds are registered buffers, so the export hash covers them; output one scale per clip. It equals `tower_scale_rule.estimate` to 1e-9 on every K1 capture and every dev-S1 clip in the cached proofs.
2. **Residual head:** log s = log s_rule + f(x), f a small MLP with its last layer zero at init, x = the 29 existing features plus the rule's own scale and spread, and the pose head's scale-token output where a cached value exists. Two targets, reported separately: the depth-scale ratio (as b04 used) and the trajectory-scale ratio (least squares of GT against G3T translations per clip). Fit on K1 train only, at the tower layout the reader serves (state which layout the cached features use; if only the 64-frame layout is cached, say so and stop at the pricing of step 3 with that caveat).
3. **Pricing on CPU with calls fixed** (`tests/price_devs1.py` reproduces 634 of 634 scores of job 170056): dev-S1 displacement and distance, K1 held-out distance, each against the rule, paired by room (10,000 draws, seed 20261115).
4. **Bar, registered here before any number:** the head replaces the rule only if dev-S1 displacement has a paired lower bound above 0 and K1 held-out distance is at least the rule's point estimate. Otherwise the rule stays and the report says by how much the head missed.

## Gates
Zero-init equality with the rule on all cached clips; deterministic refit (two runs, equal hashes); tests exit 0; EAT-1's static scan of the new module shows no finding outside the declared buffers.

## Outputs
`out/SCALE_R1_REPORT.md`, the module and head with hashes, the pricing JSONs, a mirror on a second node, one RESULT event with the bar's verdict.
