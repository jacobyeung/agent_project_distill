# K1 refit inputs recovered after the trinity-2-18 loss (2026-11-16)

Status: complete 2026-11-16 02:15Z (lane recover_k1, trinity-3-30). Recovery only; nothing built, nothing run on GPU.

## Question
The K1 refit (kit_k1a `work/refit/train.py`) needs three inputs that lived only on trinity-2-18: `grd_selector/work/setsel/setlib.py`, the deployed selector's `devs1_masks/out/kit/work/vendor/MODELS.json` with its sklearn bundle, and the scikit-learn version. Where do copies survive, and how do we know they are the deployed versions?

## Answer
- **setlib.py: recovered.** sha256 `d9271cc98d1f17f7259287f0795fdaf2f8c679f694e7c2cc73ebdd0a5609492a`, 7,610 B. Copy: `events/recover_k1/files/setlib.py` and `/scratch/jjyeung/orch_n30/recover_k1/files/setlib.py` (trinity-3-30). This is the vendored copy (`vendor/setlib.py`), not the `setsel/` original. Every copy we found has these same bytes, and kit_k1a's own `out/DEPENDENCIES.json` pins this sha for `native_kit/vendor_sam/vendor/setlib.py`.
- **MODELS.json: recovered.** sha256 `cdf19409fa0427dbd243c1b2c49fc418a12245af93373615ac06e8365c835dfc`, 5,728 B. Copy: `events/recover_k1/files/MODELS.json` and the lane `files/`. Every vendored copy has the same bytes. The kit_combo3 seal pins it (SHA256SUMS sha `cc475240…` equals `SEAL.json.sha256sums_sha256`), and its `source`/`source_sha256` fields name the setsel DEPLOY pickles (`probs2/deploy_portable_np_logistic.pkl` 325397c5…, `pairs_fit/deploy_pairs_logistic.pkl` 79dfed08…).
- **sklearn pickle bundle: not recovered, and the refit does not need it.** `train.py` never loads a pickle. Lines 74-76 *write* new pickles for the price2 consumer, and line 60 compares the refit against MODELS.json's NumPy fields. Only fixture proof `proof_p2.py` unpickles the two deploy .pkl files, and P2 also needs `setsel/data/dev_tab.jsonl` and `dev_pairs.jsonl`, which were lost too.
- **scikit-learn version of the bundle: not recovered.** The best available interpreter is `/scratch/jjyeung/envs/planner_local_v1` (sklearn 1.5.2, numpy 2.2.6, Python 3.12.13). It exists on trinity-1-18, 1-13 and 3-30, and `proof_p2.py` names it as "the authorized planner_local_v1 interpreter". k1_ops4's blocker checked only p1cpu and sam3_capretry_native_v1. No record shows which version pickled the deploy bundle.

## Evidence
- GCS `gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/model_8005668fc14ce5ee.tar` (sha 8005668f…, 10,240 B) holds one file, `fsw/ap/e84d901c/arm/frozen/6f27ae81/model.json` (1,621 B). It is a base-VLM weight manifest (schema `p3-model-input-v1`, kind `base`, safetensors shas), not the selector.
- GCS `…/evalx_native/code_4d05c37b29479787.tar` (newest, 3,584,000 B, sha 4d05c37b…) holds `native/out2/mask_kit/kit_combo3.tar.gz` (sha b3fa05c6…). That kit_combo3 holds `work/vendor/{setlib.py, MODELS.json, features.py, pair_features.py, set_features.py, …}`. FORK_NOTE: kit_combo3 is the evalx fork of mask_recall_kit (sha 30ebe415) via kit_combo2 (0d2f2c14), and the vendor modules are byte-identical to kit_combo2.
- trinity-1-18: `vendor/setlib.py` = d9271cc9 and `vendor/MODELS.json` = cdf19409 in `devs1_mask_run/kit`, `mask_recall_run/{kit,kit_combo,kit_combo2}`, `own_ground_gpu/kit_{A,B}/work/upstream`, `geo_bakeoff_kit/work/reference_policy/setlib.py`, and kit_k1a `native_kit/vendor_sam/vendor/setlib.py`. No other bytes exist under those names.
- trinity-1-13: `native_r2/work/code9/…/kit_combo3.tar.gz` has the same sha b3fa05c6. The tree has no sklearn dist-info and no selector pickle.
- Compatibility check (planner_local_v1 on 3-30, import and attribute check only): the recovered setlib defines every name that fit.py, fit_pairs.py, build.py, train.py, proof_p2.py, proof_p5.py and build_tables.py use (FEATS, GROUPS, PFEATS, load, name_prior, room). `FEATS['portable_np']` and `PFEATS` equal MODELS.json's accept and pairs feature lists in order. `fit.model('logistic')` builds StandardScaler+LogisticRegression. build.py does not import setlib.
- The native read uses NumPy coefficients (`price_masks.py` loads `vendor/MODELS.json`; DEVS1 record line 12 says "No sklearn install"), and its RUNTIME_TREE.json has no sklearn. I therefore made no Orchard call.

## Places searched and what they held
| place | how | held |
|---|---|---|
| GCS q8/8865619b/evalx_native | recover_map2 listing `recover_map2/work/GCS_q8_20261115.txt`; fetched model_8005668f and code_4d05c37b | 14 code tars, geometry, masks, metadata, model (VLM manifest). The other 13 code tars were not opened (single-file rule; the newest already holds the kit) |
| GCS q7 | same listing | no setsel/vendor/selector names |
| trinity-1-18 | one ssh 02:03Z, bounded finds in k1_ops3/{kc,work}, orch_cd/grd_selector (3 files), orch_cd/devs1_masks (1 file), mask_recall_run, devs1_mask_run, k1, own_ground_gpu, geo_bakeoff_kit | above; the deploy .pkl files and dev_tab/dev_pairs are absent; the k1_ops3 `codex_gtset/tests_8cc4f9ec` .pkl/MODELS.json/setlib (53 B stubs) are test fixtures |
| trinity-1-13 | one ssh 02:10Z, bounded find in native_r2/work | kit_combo3.tar.gz (same sha); tree/requirements.txt (147 B, not read) |
| Codex receipts | one listing of agent/scratch/codex_runs (1,751 entries) | no run labelled setsel, grd, selector, devs1_masks or setlib; the nearest are 20261110T0514Z ground_backend/ground_rows, which predate setsel (11-11), so I opened no sessions |
| Design records | INDEX "selector"; named greps in GRD_SELECTOR_KIT_20261111.md, DEVS1_PREDICTED_MASKS_ROUTE_TABLE_KIT_20261112.md, B6_GROUNDING_DESIGN_20261115.md | recipe (DEPLOY fit on all 84 dev scans, portable_np logistic, pairs logistic, tau 0.15, merge 0.2). None states an sklearn version or setlib sha |
