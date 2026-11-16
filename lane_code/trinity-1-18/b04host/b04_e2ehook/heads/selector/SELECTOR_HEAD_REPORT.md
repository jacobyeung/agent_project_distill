# Stage-1 selector head on K1: report (lane b04_e2ehook, 2026-11-16)

**Verdict: PASS on the B6 kill bar for the shipped head (run_raw), on candidates that SAM 3 found for the name as written.** The head matches the K1-refit logistic on AUC and on top-1.

K1's SAM 3 cache was built under the `dense_aliases` prompt contract: 26% of its instances came from alias prompts (table -> desk, chair -> seat, lamp -> light, tv -> television; 58 captures counted). A reader that prompts the raw name never sees those instances, so the shipped head is trained and judged on raw-prompt tables (alias instances dropped, presence = the raw prompt's own presence). The alias-table result is kept below as the price of dropping aliases.

| K1 held-out | candidates / objects / rooms | AUC | AP | top-1 |
|---|---|---|---|---|
| **raw-name tables** | 1,541 / 157 / 43 | | | |
| SelectorHead run_raw (1931446b..., no name input) | | 0.9404 | 0.693 | 60.5% |
| K1-refit logistic (unchanged setsel fit.py, portable_np) | | 0.9422 | 0.683 | 59.9% |
| deployed selector (MODELS.json cdf19409) | | 0.9205 | 0.649 | 61.8% |
| head - refit, paired room bootstrap (10,000, seed 20261116) | | -0.002 [-0.012, +0.009] | | +0.6 [-2.7, +4.0] |
| head - deployed | | +0.020 [+0.001, +0.041] | | -1.3 [-4.8, +2.3] |
| **alias tables (dense_aliases)** | 1,942 / 158 / 43 | | | |
| SelectorHead run1 (09c1e6ba..., trigram name) | | 0.9337 | 0.679 | 58.9% |
| K1-refit logistic | | 0.9365 | 0.658 | 62.7% |
| head - refit | | -0.003 [-0.022, +0.014] | | -3.8 [-7.5, 0.0] (FAIL) |

Bar: AUC >= refit - 0.02 and top-1 >= refit - 2 points. run_raw passes both. With its null slot, run_raw's argmax is right on 66.2% of held-out objects (43 of 157 have no positive candidate).
Train-only CV (5 room-grouped folds, same folds for both arms; raw tables): head 0.915 AUC / 66.7% top-1, logistic 0.927 / 67.9%.
Dropping aliases costs the logistic 2.8 top-1 points on held-out (62.7% -> 59.9%; the candidate sets differ, so this is not paired). The head on raw names (60.5%) recovers 0.6 of them.

## Inputs
- Tables: kit_k1a's unchanged `build_tables.build_capture` (extract + label: y=1 when at least half of a candidate's members match a named GT instance at IoU > 0.5), run on trinity-1-18 by `sl118/sl_tables.py` (`--raw-prompts-only` for the raw tables; 1-18 `/scratch/jjyeung/orch_n30/b04_e2ehook_sl/full` and `full_raw`). Geometry: frozen G3T at E3's S4 per-capture scale with G1 gravity (K1's own phase has not run); both arms read the same rows.
- Population: 296 GT captures; 266 tabled (215 train / 51 held-out), 18 excluded (E3 G1 refused), 12 failed `Metadata exceeds bounded reader` (candidates.json above 20 MB); both arms lose the same captures.
- Head inputs: `sl118/selector_inputs.py`, 58 fixed-math values per candidate (the 28 portable_np features with log1p on counts, plus 30 SAM 3 and geometry statistics). The name enters as written (lowercase and strip); CV chose no name input for run_raw (the proposals are already conditioned on the name).
- Frozen SAM 3 text embedding of the 65 names (sam3.pt 9999e234): `data/emb/NAME_EMB_SAM3.safetensors` (a3d48931...); CV picked it in neither table.

## Head
`selector_head.py`: DeepSets MLP. phi(x) -> h (32); context = mean and max of h plus the name vector; candidate logit from [h, context]; null logit from the context. Sockets `mask_tokens` [N,256] and `vit_feats` [N,1024] enter through zero-initialised projections (zeros leave the output unchanged; tested). `with_null()` returns N+1 slots for the reader's argmax.
Training (`train_selector.py`): BCE per candidate plus BCE of the null logit on "no positive candidate"; AdamW lr 3e-3, 16 objects per step, seed 20261116, one thread, deterministic algorithms. Grid: name {sam3, trigram, none} x hidden {32, 64} x wd {1e-3, 1e-2} x epochs {15, 40}; rule fixed before training: max OOF AUC + OOF top-1. run_raw: none, hidden 32, wd 1e-3, 15 epochs. Each held-out table was read once per head.
In the reader: `e2e_reader/stage1.py` (StageOne) runs the same producers on the in-call tower's detections; on a K1 capture it reproduces both tables' head inputs to < 1e-9 (`tests/test_stage1_k1.py`).

## Files (sha256 prefixes)
selector_head.py d783e646; train_selector.py 8a2cb707; common.py adf00b91; logistic.py cfd3d97e; logistic_cv.py b7154c2f; eval_selector.py db3f97c7; retrain_final.py bc8c8148; sl118/selector_inputs.py 9f7c0baf; sl118/sl_tables.py 770858a1; sl118/name_emb.py 8e4b862b.
Weights: work/run_raw/selector_head.safetensors 1931446b20f4ecd4ec41916bd2ca61238f23d43039c07a7ac64b5cb323d929cb (retrain bit-identical: work/run_raw_retrain); work/run1/selector_head.safetensors 09c1e6ba134b3c45a1224d1295180048f4074a01da1ce4f03a8262d338ea2d5e (alias tables; retrain identical).
Results: work/SELECTOR_HELDOUT_raw.json bcbd0242, work/SELECTOR_HELDOUT.json 81ba485c, work/logistic_heldout_raw.json c4cee5a1, work/logistic_heldout.json e90d3360. Tables: data/pull_raw.tar 4831304f, data/pull1.tar ce2f2403.

## What might not work, and what would settle it
- The in-call tower keeps proposals at the K1 contract (joint >= 0.05, at most 100 per frame); the raw tables come from the alias cache with alias instances dropped, so per-frame ranks and caps can differ from a raw-only SAM 3 run. One dev-S1 or K1 capture run through the in-call tower on GPU against the filtered cache would measure it.
- 157 objects make top-1 noisy (one object = 0.64 points); the interval vs the logistic spans [-2.7, +4.0].
- CV chose the grid's lowest epoch count (15); a train-only grid over {5, 8, 15} would show whether shorter training helps.
- The candidate producers (`routed_features`: lift floor 0.3, linking radii, accept_features) keep their fixed constants; only the selector is learned. `selector_inputs.py` has one threshold (score >= 0.3 in `name_frames_frac`).
