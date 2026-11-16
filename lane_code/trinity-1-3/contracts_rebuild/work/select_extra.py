from pathlib import Path
import json
L=Path(__file__).resolve().parents[1]
original='''test_tower_read_v2 test_s1_native_replay test_sam3_validate test_e2e_shared_rows test_s1_pool_admission test_tower_read test_acceptance_cpu_e2e_r13 test_rescue_claims_r2 test_trace_format313_decode test_ground_backend test_native_selector84 test_s1_grounding_runtime test_own_vit_reread test_s1_candidate_policy test_s1_routing test_verify_r2 test_review_r2_integration test_integration_r2 test_ground_r3 test_e2e_open_vocabulary test_grounding_decode test_stageb_mdg test_ground_review_v2 test_mdg_features test_live_adapter_r3 test_integ_v314_r2 test_decode_parity_r9 test_native_selector_profile test_grounding_features test_svp_stages_r2 test_integ_v314 test_room_v314 test_gxp_mix test_sam3_reference_r10 test_sam3_tower test_ground_r2 test_carrier_c1_final test_batched_routed_decode test_acceptance_parity_rules test_hrp_reread'''
old={f'tests/{n}.py' for n in original.split()}|{'generator/derivgen_v7/test_render_gaps.py'}
extra=sorted(set(json.loads((L/'work/base_tests.json').read_text()))-old)
(L/'work/base_tests_extra.json').write_text(json.dumps(extra,indent=2))
print(extra)
