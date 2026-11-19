# Review and defect regression map

| Review finding | Regression | Outcome |
|---|---|---|
| 1 | test_01_surface_scope_and_argv | Visible surfaces only; planted name, argv and environment rejected. Optional trap normalization removes literal head. |
| 2 | test_02_all_checks_precede_transport; test_07b_native_source_drift_blocks_release | Implemented local gates and all phase scripts precede transport; raw D source drift blocks release. Remaining unimplemented native predicates are listed in the inventory. |
| 3 | test_03_timeout_short_calls_and_state_machine | Every call is bounded; CPU submit and polling use separate calls. |
| 4 | test_04_delivery_is_tested_tree; patch replay | Manifest binds the canonical tested sources and delivery bytes. |
| 5 | test_05_adapt_cpu_identity_everywhere | Old job token disappears everywhere; foreign path/token and walltime rejected. |
| 6 | test_06_defect1_real_rows_null | Nonzero real-package rows; null top-level frame count fails the actual probe. |
| 7 | test_07_adapter_leaves_native_files_unchanged; test_native.py | Additive patch preserves sources. Raw native checker fails before and after on supplied scorer drift; coherent fixture passes both. Literal raw-tree pass remains unmet. |
| 8 | test_08_real_python36_place_and_fill | Place, native fill and entry check run under real Python 3.6.8. |
| 9 | test_09_defect2_isolated_import_gate; test_09b_defect3_fill_drops_env | Planted sibling import and native fill slot replacement fail their actual isolated probes. |
| 10 | test_10_terminal_states_and_transport_failure | Failure states and transport failure stop; exactly three consecutive accounting errors stop. |
| 11 | test_11_extra_terms_reach_path_argv_env | Extra terms reach paths, fill argv and native environment. |
| 12 | test_12_transport_limit | Local transport stub receives stdin through pv 8,000,000 bytes/s; timeout kills a bounded stub without SSH. |
| 13 | test_13_ledger_reuse_before_builder | Ledger reuse rejected before native builder call. |
| 15 | test_15_orchard_contract_inventory | Live queue, pool, token, state, private-mode and signal limits documented. |

Recorded defect 4 is planted into the encoded batch descriptor and detected by structure/old-identity gates. Defect 5 removes the EXIT trap and fails the exact shell-trap probe. Defect 6 breaks USR1 forwarding and the native read-runner stop handler and fails both probes. The B4 failure cause remains unknown, and the trainer-rank USR1 incident is not repaired by a read-runner test.
