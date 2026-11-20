from common import *
from student_pilot.carrier_c1_run import identity
tree=J.load(D/'TREE_CPRIME.json');seals=J.load(D/'SEALS.json');pins=J.load(D/'DEPENDENT_PINS.json')
replace(L/'out/TREE_CPRIME.md',f'''C′ has seal `{tree['after']}`. The tree's own `source_seal.inventory` and `p3_provenance.digest` computed it.

Its base is `{tree['before']}`. The authorized patch has SHA256 `{tree['patch_sha256']}` and was applied with `patch -p1`.

Exactly three files differ:

- `student_pilot/carrier_c1_run.py`
- `launch_r1/entry.py`
- `tests/test_r1_processor_compat.py`

`work/build24m4m/TREE_CPRIME.json` records both inventories' changed-file hashes. `patch.log` records the application. C′ contains no other source changes.

The three compatibility tests pass. The existing single-image, host-admission and carrier-run suites ran 37 tests in total, including those three: 33 passed, two skipped and two failed on incompatible fixtures. The raw failures remain in `tree_tests3.log`. Two external fixture corrections then passed: legacy admission uses null pixel fields; the single-image preparation fixture supplies its missing trace version and source metadata. `TREE_FIXTURE_TESTS.json` records those exact fixture edits. No test source in C′ was edited.

`DEPENDENT_PINS.json` lists the archive, both source records, source maps, decoded config identities, capsule hashes, runtime upload and changed kit files. `PIN_AUDIT.json` authenticates all four embedded archives and verifies that no old C identity remains in their decoded metadata. The runtime source record is uploaded as `u/{pins['n']['runtime_upload']['new']}`.

The tests use CPU fixtures. They do not establish production row equivalence, real tokenizer-asset compatibility, GPU forward behavior or training admission.
''')
replace(L/'out/QD_STEP1.md',f'''Discovery uses N's fresh initialization policy and the same configuration identity. Both decoded `k/c.json` configs and both decoded `k/n.json` configs are equal between qd and n. Their prepared configuration templates differ in zero fields. qd uses `proof_mode=train` because C′'s native policy guard requires it; qd still executes only the proof path and contains no `t.py`, `u.py` or `e.sh`.

The code path is:

- `out/kit_qd/b/a.py:59` calls `production_proof.run` in mode q after planning and staging.
- `work/tree_r1c/student_pilot/r1_persisted.py:24` accepts `step400_export_weights_fresh_v1` only with `proof_mode=train`; the q value refuses with `P_EXPORT_INIT_TRAIN_MODE_REQUIRED`.
- `work/tree_r1c/launch_r1/production_proof.py:108` passes that policy to persisted verification. At line 164 it requires absolute start 0; at line 174 it forwards the same final bound config.
- `work/tree_r1c/launch_r1/production_proof.py:17` calls `first_batch_check` for all four ranks, one step and `cuda:0`.
- `work/tree_r1c/student_pilot/carrier_c1_run.py:3104` uses the prepared store counts and bound sampler; the resume branch at line 3107 is skipped for start 0. `carrier_c1_data.py:466` and `r2_mix.py:197` dispatch to `r1_mix.plans`.
- `carrier_c1_run.py:3143` constructs the processor from that prepared receipt and model manifest. The model enters evaluation mode at line 3151; `check_plan_rows` uses `torch.no_grad()` at line 3039. These bodies are unchanged from C except the authorized constructor patch.

`QD_STEP1_TESTS.json` verifies 288 row selections across four ranks, with the actual pinned card and explicit synthetic prepared stores/indices. It runs the native planner and `first_batch_check` selection, captures the requested `cuda:0` device without accessing a GPU, and confirms that step 1 differs from step 401. Model loading and numerical forward are stubbed. `HANDOVER_TESTS.json` records all eight real decoded configs passing native handover comparison with null pixel fields and 32 frames.

The preparation and handover binders are shared with N. Their runtime paths, prepared stream receipts, population/indices, routing selection, handover mapping and processor metadata must be identical for the identities to remain equal; this build changes none of those inputs between the two templates. Host/review receipts and the preparation pin are identity-exempt. No real prepared outputs were produced locally, so runtime identity equality remains an explicit check for the discovery receipt and launch. The fixture establishes row-selection behavior, not a production forward pass or review approval.
''')
replace(L/'out/RCJ_USAGE.md',f'''The CPU helper supports `b` for P-only reconstruction and `r` for the sealed kit's native regeneration path. Apply `UPLOADS_24M4M.json/.list` against the recorded 24m4j q/n/qd kit seals and 24m4k rcj files. The manifest includes the new source record and four changed/new helper files; `rcj.sh` is byte-identical to its baseline. `UPLOADS_24M4M_GO.json` is a separate overlay on the new n seal.

The operator can submit either mode after the required review:

```bash
cd /project/community/jjyeung/okh7/x_22c714e1/qd
sbatch --job-name=q24l ../rcj/rcj.sh b
sbatch --job-name=q24lr ../rcj/rcj.sh r
```

Submit only the intended mode. Each command requests preempt, one node, 16 CPUs, 128 GB and two hours, with no GPU or requeue. Libraries use at most eight threads. Both launch mount fixes remain: the runtime path exists before binding, and the job namespace is installed before `/tmp` is remounted read-only. The inner producer cannot publish; the shell's EXIT trap publishes outside its sandbox after success or failure.

Mode b reconstructs P with its isolated sealed producer and full `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84` database gate. Mode r invokes `a.py r`, the native planner and both builders. It stages the planner's metadata and row stores, runtime and required export weights. It omits RGB payloads. No SQLite database is uploaded.

Publication attempts native receipts, materialization, import evidence, database hashes/sizes/headers and timings independently. Mode r publishes selection evidence and invokes the pinned `rdiff.py` after the full P gate. Its `rd0` output precedes sampling. A producer or comparison failure retains a failing job status after publication.

`rcj/P_SAMPLE_I.json` is the reviewer's `p_sample_request_v1` request. `ps.py` is the unchanged reference implementation (SHA256 `{J.sha(L/'out/rcj/ps.py')}`). The outside publisher forces the production gate even if `PS_GATE` is inherited. Uniform positions are zero-based positions in P's `ORDER BY i`; the other samples use seeds 20261121 and 20261122 for U_Faithful and the ordered `rd0/rdiff.json.gz` P_absent entries' i values. The reference preserves stored row/target text and writes at most 5,000,000 bytes to `o/<job>/p_sample.json`. A missing request skips sampling. A bad gate writes no sample. Any sample refusal is recorded in timings and changes neither the build nor publisher status in either mode.

After both mode-r databases exist, `pc.py` selects seed-20261123 rows from N: 40 routing plus 40 VQA rows when the staged VQA store is accessible, otherwise 80 routing rows with the reason recorded. It calls `processor_for_receipt` in separate C′ and authenticated P (`b83a8a35…`) children, using each side's config and model metadata. Each tree applies its native routing flag and target renderer before tokenization. The native dense encoder supplies pixel bounds and frame layout; only RGB loading and the final visual encode are replaced by a text probe. The probe records effective tokenizer frame count, frame markers, native prompt/target/combined token IDs, encoder bounds and per-row PASS/FAIL. It loads no model weights and decodes no RGB.

`o/<job>/proc_check.json` includes SHA256 of the sorted `[stream,i,qid]` keys as compact UTF-8 JSON. N must have no `_b7_layout`, P must use DEFAULT_PIXELS, and every compared value must agree. A processor mismatch or unavailable check publishes FAIL and fails the job. Sampling refusal does not suppress this check. Child diagnostics stay job-local; publication records the bounded failure reason.

`RCJ_L_TESTS.json`, `SAMPLE_FINAL_TESTS.json`, `PC_INTEGRATION_TESTS.json`, `MOUNT_TESTS.json`, `RDIFF_MOUNT_TEST.json` and `RCJ_CONTRACT_TESTS.json` document the fixtures, real read-only mounts and hash gates. The isolated processor fixture uses native constructors and encoders with synthetic rows and a tokenizer loader stub; it covers 40+40 PASS, 80-row fallback and deliberate processor mismatch. No production reconstruction, real-row check, Orchard submission or GPU forward ran locally.
''')
s=(L/'out/ARM_ROUTING_USAGE.md').read_text();a=s.index('The armed q/n delta');b=s.index('\n\nThe helper creates',a)
s=s[:a]+'''The armed q/n delta uses the new 24m4l seals in `work/build24m4m/ARM_BASE_SEALS.json` and its matching file inventory. Apply `UPLOADS_24M4M.json` first. The helper explicitly carries `k/c.json`, `k/n.json`, `k/8.json` and `k/s.json`, and its delta replays to complete armed kits. The separate GO overlay is not part of the ordinary upload stream.'''+s[b:]
s=s.replace('/w24k','/w24l').replace('build24m4k','build24m4m').replace('tree C','tree C′')
replace(L/'out/ARM_ROUTING_USAGE.md',s)
print('Wrote C-prime, discovery, CPU and arming documentation')
