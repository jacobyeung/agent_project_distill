Package `c3cc59fb4aae0` is resealed with an Orchard CPU check for both first items. **Local checks pass; submission requires the real Orchard CPU receipt.** No remote action or GPU run occurred.

The token stays unchanged because all 928 payload members and `0.tgz` remain byte-identical. Only operator files and their enclosing seals change. `OPERATOR_ONLY_AUDIT.json` records this comparison; `HASHES.json` records the final hashes.

| Implementation | File and line |
|---|---|
| Room admission | `out/src/h1eval/room134.py:6` |
| Mixed frame binding | `out/src/h1eval/room134.py:33` |
| Manifest dispatch | `out/src/h1eval/items.py:116` |
| Frame-root extraction admission | `out/src/orchard_h10/job.py:42` |
| Durable type binding | `out/src/h1eval/h10/launch.py:192` |
| One read and settings | `out/tower_sequence.py:5` |
| Allocated full-reader check | `out/tower_sequence.py:81` |
| CPU receipt validation | `out/node_check.py:13` |
| Scoring and pairing | `out/room_pair.py:15` |

The allocated helper stages authenticated archives and restores the export before rehearsing `room_scene0155_00` and `r0_015bd4aaf6870d79bade`. It uses W5's allocation recipe: `general`, eight CPUs, 200G, `04:00:00`, and no GPU.

Both items run through real launch, mixed native mapping, frame SHA256 verification and PNG decoding, capped ParityGenerator, CallHook, the decode loop and official scoring. Weights, model forward, tokenizer, prompt tensors, audit enforcement and decode budget use explicit CPU stubs.

The helper embeds both finished records in `a/c/CPU.json` under `full_reader.records` and sets `full_reader_passed=true`. It also writes `FULL_READER.json`. Any failure aborts the check. The bootstrap requires both pass flags and matching payload, plan, input and operator hashes.

The first dev-S1 item has distinct native-answer and evaluation-ground-truth labels. The check records both official scores without changing either label. Stub scores establish execution, not model quality.

| Evidence | Result |
|---|---|
| `LOCAL_CPU_CHECK.json` | Both records finish on an initially empty local root with the real R0 tar and synthetic dev-S1 PNGs. |
| `LOCAL_NATIVE_CPU_CHECK.json` | The same check finishes with native `d1/scene0155_00` frame paths. |
| `CPU_HELPER_TEST.json` | The helper enforces stage/restore/rehearsal order and writes both records; failures publish no passing receipt. |
| `W5_BINDING_EQUIVALENCE.json` | All 36 dev-S1 room bindings match W5. |
| `OPERATOR_ONLY_AUDIT.json` | All 928 payload members remain identical; the same token is valid. |

The local fixture uses the production extractor and admitted `d` and `d/f` destinations. It reads the authenticated R0 tar in place. The synthetic dev-S1 fixture preserves the native `d1/<scene>` key and tests both native paths and the pinned metadata's content-addressed PNG paths. Synthetic digests exist only in fixture settings; no digest verifier is bypassed.

Local preparation stubs unavailable export weights, artifact construction and runtime versions. The helper orchestration test also stubs the allocation, namespace and storage proof. These tests validate the check implementation; the allocated Orchard run must validate the actual archives, restore and namespace.

The W5 comparison runs each source tree in an isolated interpreter. Native tasks, resolved anchor/dense paths, pinned SHA256 values, indices, slots, mapping digests, effective types, settings and finished journal types match for all 36 rows. W6 explicitly persists the effective type list; W5's settings and journals establish the same selection.

The plan still contains one development-only room read: 36 dev-S1 and 98 R0-dev items, tower, mode none, null_argmax, G3T memo on, no verification IDs, and no own-depth output. The item-set digest is `381717700a175d54fe9fa8f19194c9b04366feceb99f278a733f611b853fd7ac`. No fitting ran.

The payload retains the reader, scorer, step-544 export, frame binding and input descriptors. `PATCH.diff` compares source and operator files against W5. `PAYLOAD_AUDIT.json` records the payload's W5 comparison separately from the operator-only reseal audit.

Latest suite results: **87 passed, 0 failed**. `TESTS.txt` preserves the execution ledger; this table reports each suite's latest result. Unchanged reader/memo suites retain their passing evidence.

| Gate | Latest result | Tests | Log |
|---|---|---:|---|
| `out/tests/test_package.py` | PASS | 13 | `test_package_1794955130446362633.log` |
| `work/test_sequence.py` | PASS | 5 | `test_sequence_1794955134882603114.log` |
| `work/test_full_room.py` | PASS | 5 | `test_full_room_1794955069217927285.log` |
| `out/tests/test_constraints.py` | PASS | 9 | `test_constraints_1794955131960771781.log` |
| `work/test_room_contract.py` | PASS | 5 | `test_room_contract_1794955139633575382.log` |
| `work/test_room_pair.py` | PASS | 2 | `test_room_pair_1794955145365929158.log` |
| `work/test_memo.py` | PASS | 8 | `test_memo.log` |
| `work/test_memo_binding.py` | PASS | 4 | `test_memo_binding_1794955151443883946.log` |
| `work/test_module_selection.py` | PASS | 3 | `test_module_selection.log` |
| `work/test_operator_memory.py` | PASS | 2 | `test_operator_memory_1794955229499121965.log` |
| `work/test_fixes.py` | PASS | 5 | `test_fixes_1794955160491951737.log` |
| `work/test_return_cli.py` | PASS | 1 | `test_return_cli_1794955160767042664.log` |
| `work/test_b1.py` | PASS | 8 | `test_b1.log` |
| `work/test_select_stubs.py` | PASS | 6 | `test_select_stubs_1794955160858906807.log` |
| `work/test_tower.py` | PASS | 7 | `test_tower_1794955163928261928.log` |
| `work/test_w5_binding.py` | PASS | 1 | `test_w5_binding_1794955173792532685.log` |
| `work/test_cpu_helper.py` | PASS | 3 | `test_cpu_helper_1794955227159436247.log` |

Production walltime remains `02:30:00`; the CPU check uses `04:00:00`. The read estimate is 3662.6 seconds. The return estimate is 10,428,800 bytes, below the 89.9 MB archive allowance and 100 MB pool cap. Production throughput, RSS and pool occupancy remain unmeasured.

`OPERATIONS_ROOM.md` gives exact placement, metadata-check, allocated CPU-check, pass-flag inspection, submit, fetch, unpack and scoring commands. It requires the passing Orchard receipt before submission.

All writes stayed inside W6. Tests used the supplied CPU Python with at most eight workers. No SSH, Git, network, submission, process kill or deletion ran. Rebuild the operator delivery with `out/build_operator.py` and `out/build_delivery.py`; verify it with `work/audit_operator_only.py` and `work/final_check.py`.

The report applies the no-archaeology and summary skills. The W5 comparison and reseal baseline remain because the requested equivalence and token checks require them.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `0.tgz` | 5036924 | `3ba30302eeeeca9f4257c16ecf2d94120e95a09f610b00f1602066933f6a052b` |
| `1.tgz` | 5046155 | `741a362d5abd06124f3cff004123396ba43e8446e51883f0af955455f4b40d97` |
| `PACKAGE.json` | 626 | `40d91fb965bfc9703b6b49d369a269d8e55e251e18ba21c48468c155914732d1` |
| `READ_PLAN.json` | 5839 | `ec1be0bb31f30e5ebf7273096b6e5c40c57c939ebaf0d26a23fc4301e5d4dbed` |
| `inputs_tower.json` | 6405 | `206f81ec51f0ce38113b14289f9cf9896baded0e8a950e88ac6653764b24ac04` |
| `export_544.json` | 1498 | `798111bc92c146f64a1c031827a38381be022ae44304f864cc51f880d2fc754b` |
| `tower_sequence.py` | 14284 | `f8e2b7661e2114f366be731bd06278865d23747aa80632b409330252abda6856` |
| `tower_bootstrap.py` | 2006 | `d7777f35850db09819494a98748c460b3a19b3ee77e99ec827eae6648a9f2280` |
| `node_check.py` | 6108 | `135a12ee54bab3c32bcb6eba0b845145f5134384821b81e4ed23998f1968f76c` |
| `room_pair.py` | 6011 | `0e8e5921a5fa7091015e93f7ded290e22de1e0d2b6b1c516bb9b2c8bd41a4d4b` |
| `unpack_return.py` | 2963 | `7bb3e2972e387d7f659a171626597ba4b9f07eaacfab50987a9372bd03bddb64` |
| `src/items/room134.json` | 486709 | `607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7` |
| `src/inputs/room_captures.json` | 828159 | `f84f9b25df9de0f4dc73861b38ecb3bec0fd1adc5a412893f2f795f09cd985fd` |
| `LOCAL_CPU_CHECK.json` | 51072 | `2a7ea247c102be4c3cbec35178a741d25558c5b69fd48ba1831c42068f0bc172` |
| `LOCAL_NATIVE_CPU_CHECK.json` | 48807 | `4c01755979f5af6bb7f4fa6f3d36fc3f3ff7a809fbf01eafdee4b537c58dae4d` |
| `CPU_HELPER_TEST.json` | 451 | `4a29f65a912e4c2ac55a8495a061f0e1029dd0ffdb0916b53743a1f8bf80d7bc` |
| `W5_BINDING_EQUIVALENCE.json` | 785 | `c922532d68a0872ca3a090c8d8522d133d6fc7297c364fcec2915a3bf6a1e7c5` |
| `OPERATOR_ONLY_AUDIT.json` | 400 | `52fa59af5d5eccec615b3d6ad4bd5a5541edcf233236f939df4b2db6307dd1e5` |
