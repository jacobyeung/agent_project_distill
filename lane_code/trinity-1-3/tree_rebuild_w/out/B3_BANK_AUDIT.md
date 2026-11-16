# Bank-entrypoint audit

Unsupported legacy formats refuse outright in this derived tree. The only admitted bank reader is `student_pilot.r2_policy.read_bank`, which owns the read and binds item identities plus its reader hash. Gates do not trust a caller-provided bank label.

The inventory covers native inference, grounding/MDG runtime, evaluation workers, development-bank loaders, scoring/export commands and legacy command-line wrappers. Pure item metrics, tensor helpers, frame decoders, artifact validators and training-only row producers are not bank entrypoints. The refused wrappers cannot route around the listed gates.

The inventory contains 84 entrypoints (`out/B3_BANK_ENTRYPOINTS.json`). Refusal tests are generated from that inventory in `tests/test_r2_build3.py:EvaluationEntrypoints`; final run snapshots also retain the inventory.

| Entry | Boundary |
|---|---|
| `student_pilot/carrier_c1_run.py:inference` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/carrier_c1_run.py:probe` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/carrier_c1_run.py:evaluate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/carrier_c1_canary.py:run` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/decoupled_v_run.py:evaluate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/decoupled_v_run.py:probe` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/grounding_eval.py:load_runtime` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/grounding_eval.py:run_worker` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/grounding_eval.py:merge` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/grounding_eval.py:to_ground` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/mdg_eval.py:load_runtime` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/mdg_eval.py:run_export` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/mdg_eval.py:run_pointing` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/mdg_eval.py:run_w10` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/runtime.py:load_model` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/items.py:load_items` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/run.py:load_request_items` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/run.py:run_worker` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/routed_dev.py:load_tasks` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/vqa_direct.py:load_tasks` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/vqa_direct.py:run_worker` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/pointing_candidates.py:run_worker` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/pointing_markers.py:load_tasks` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/pointing_markers.py:run_worker` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/heldout_loss.py:run_worker` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/official.py:score_official_vsibench` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/official.py:score_our_cell` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/parity.py:run_suite` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `verifykit/prepare.py:prepare_dev` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `verifykit/prepare.py:prepare_pointing` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `verifykit/score.py:evaluate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `step0_runtime_v1/run_cell.py:run` | module-refuse: Refuse before external or script-local legacy imports |
| `step0_runtime_v1/diag_worker.py:run` | module-refuse: Refuse before external or script-local legacy imports |
| `tools/stage1_dev_metrics.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `tools/run_gate_eval_pdg.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `tools/headcall_eval_summary.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `headcall/gate_eval.py:load_rows` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `headcall/gate_eval.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/report.py:main` | module-refuse: Refuse before external or script-local legacy imports |
| `scripts/tracecold_read_native.py:readout` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `scripts/orchard/eval_job.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `scripts/gpu_native_selector.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/diagnostic.py:evaluate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/gate_driver.py:run_gate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/gate_driver.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/trace_readout.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/shakedown.py:evaluate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/shakedown.py:score` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/run_live_parity.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/mdg_runtime.py:load_runtime` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/sets.py:_dev_rows` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/sets.py:_revsi_rows` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/sets.py:dev_items` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/sets.py:revsi_items` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/sets.py:answers` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/sets.py:cache_revsi` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/sets.py:scene_labels` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `rk/programs.py:run` | module-refuse: Refuse before external or script-local legacy imports |
| `rk/programs.py:main` | module-refuse: Refuse before external or script-local legacy imports |
| `tools/hc_v3_decode_check.py:check` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `tools/hc_v3_decode_check.py:probe` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `tools/hc_v3_decode_check.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `scripts/head_probe.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/benchmark_eval/generate.py:generate_run` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/benchmark_eval/prepare.py:prepare` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/benchmark_eval/score.py:score_run` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/benchmark_eval/score.py:compare_scores` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/benchmark_eval/score.py:export_bank` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/benchmark_eval/contracts.py:load_generation` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/orchard_eval/generate.py:generate_run` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/orchard_eval/prepare.py:prepare` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/orchard_eval/score.py:score_run` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/orchard_eval/score.py:compare_scores` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/orchard_eval/score.py:export_bank` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/orchard_eval/contracts.py:load_generation` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `evalpath/kit_inputs.py:official_rows` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `tools/pdg_v3_gate.py:load_pqs` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `tools/pdg_v3_gate.py:load_questions` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `tools/pdg_v3_gate.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `headcall/eval_hook.py:evaluate_head_vs_shuffled` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/all_frame_readout.py:evaluate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/gate_eval.py:evaluate` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/benchmark_eval/__main__.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
| `student_pilot/orchard_eval/__main__.py:main` | refuse: Legacy format lacks an authenticated item-identity adapter |
