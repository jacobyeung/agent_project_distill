Discovery uses N's fresh initialization policy and the same configuration identity. Both decoded `k/c.json` configs and both decoded `k/n.json` configs are equal between qd and n. Their prepared configuration templates differ in zero fields. qd uses `proof_mode=train` because C′'s native policy guard requires it; qd still executes only the proof path and contains no `t.py`, `u.py` or `e.sh`.

The code path is:

- `out/kit_qd/b/a.py:59` calls `production_proof.run` in mode q after planning and staging.
- `work/tree_r1c/student_pilot/r1_persisted.py:24` accepts `step400_export_weights_fresh_v1` only with `proof_mode=train`; the q value refuses with `P_EXPORT_INIT_TRAIN_MODE_REQUIRED`.
- `work/tree_r1c/launch_r1/production_proof.py:108` passes that policy to persisted verification. At line 164 it requires absolute start 0; at line 174 it forwards the same final bound config.
- `work/tree_r1c/launch_r1/production_proof.py:17` calls `first_batch_check` for all four ranks, one step and `cuda:0`.
- `work/tree_r1c/student_pilot/carrier_c1_run.py:3104` uses the prepared store counts and bound sampler; the resume branch at line 3107 is skipped for start 0. `carrier_c1_data.py:466` and `r2_mix.py:197` dispatch to `r1_mix.plans`.
- `carrier_c1_run.py:3143` constructs the processor from that prepared receipt and model manifest. The model enters evaluation mode at line 3151; `check_plan_rows` uses `torch.no_grad()` at line 3039. These bodies are unchanged from C except the authorized constructor patch.

`QD_STEP1_TESTS.json` verifies 288 row selections across four ranks, with the actual pinned card and explicit synthetic prepared stores/indices. It runs the native planner and `first_batch_check` selection, captures the requested `cuda:0` device without accessing a GPU, and confirms that step 1 differs from step 401. Model loading and numerical forward are stubbed. `HANDOVER_TESTS.json` records all eight real decoded configs passing native handover comparison with null pixel fields and 32 frames.

The preparation and handover binders are shared with N. Their runtime paths, prepared stream receipts, population/indices, routing selection, handover mapping and processor metadata must be identical for the identities to remain equal; this build changes none of those inputs between the two templates. Host/review receipts and the preparation pin are identity-exempt. No real prepared outputs were produced locally, so runtime identity equality remains an explicit check for the discovery receipt and launch. The fixture establishes row-selection behavior, not a production forward pass or review approval.
