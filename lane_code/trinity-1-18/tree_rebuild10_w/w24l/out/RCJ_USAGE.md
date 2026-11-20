The CPU helper supports `b` for P-only reconstruction and `r` for the sealed kit's native regeneration path. Apply `UPLOADS_24M4L.json/.list` against the recorded 24m4j q/n/qd kit seals and 24m4k rcj files. The manifest includes the new source record and four changed/new helper files; `rcj.sh` is byte-identical to its baseline. `UPLOADS_24M4L_GO.json` is a separate overlay on the new n seal.

The operator can submit either mode after the required review:

```bash
cd /project/community/jjyeung/okh7/x_22c714e1/qd
sbatch --job-name=q24l ../rcj/rcj.sh b
sbatch --job-name=q24lr ../rcj/rcj.sh r
```

Submit only the intended mode. Each command requests preempt, one node, 16 CPUs, 128 GB and two hours, with no GPU or requeue. Libraries use at most eight threads. Both launch mount fixes remain: the runtime path exists before binding, and the job namespace is installed before `/tmp` is remounted read-only. The inner producer cannot publish; the shell's EXIT trap publishes outside its sandbox after success or failure.

Mode b reconstructs P with its isolated sealed producer and full `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84` database gate. Mode r invokes `a.py r`, the native planner and both builders. It stages the planner's metadata and row stores, runtime and required export weights. It omits RGB payloads. No SQLite database is uploaded.

Publication attempts native receipts, materialization, import evidence, database hashes/sizes/headers and timings independently. Mode r publishes selection evidence and invokes the pinned `rdiff.py` after the full P gate. Its `rd0` output precedes sampling. A producer or comparison failure retains a failing job status after publication.

`rcj/P_SAMPLE_I.json` is the reviewer's `p_sample_request_v1` request. `ps.py` is the unchanged reference implementation (SHA256 `6945292e167d9f602a5aa94f86e8070c28bca6770df5886c34b0d3ee66ac1eda`). The outside publisher forces the production gate even if `PS_GATE` is inherited. Uniform positions are zero-based positions in P's `ORDER BY i`; the other samples use seeds 20261121 and 20261122 for U_Faithful and the ordered `rd0/rdiff.json.gz` P_absent entries' i values. The reference preserves stored row/target text and writes at most 5,000,000 bytes to `o/<job>/p_sample.json`. A missing request skips sampling. A bad gate writes no sample. Any sample refusal is recorded in timings and changes neither the build nor publisher status in either mode.

After both mode-r databases exist, `pc.py` selects seed-20261123 rows from N: 40 routing plus 40 VQA rows when the staged VQA store is accessible, otherwise 80 routing rows with the reason recorded. It calls `processor_for_receipt` in separate C′ and authenticated P (`b83a8a35…`) children, using each side's config and model metadata. Each tree applies its native routing flag and target renderer before tokenization. The native dense encoder supplies pixel bounds and frame layout; only RGB loading and the final visual encode are replaced by a text probe. The probe records effective tokenizer frame count, frame markers, native prompt/target/combined token IDs, encoder bounds and per-row PASS/FAIL. It loads no model weights and decodes no RGB.

`o/<job>/proc_check.json` includes SHA256 of the sorted `[stream,i,qid]` keys as compact UTF-8 JSON. N must have no `_b7_layout`, P must use DEFAULT_PIXELS, and every compared value must agree. A processor mismatch or unavailable check publishes FAIL and fails the job. Sampling refusal does not suppress this check. Child diagnostics stay job-local; publication records the bounded failure reason.

`RCJ_L_TESTS.json`, `SAMPLE_FINAL_TESTS.json`, `PC_INTEGRATION_TESTS.json`, `MOUNT_TESTS.json`, `RDIFF_MOUNT_TEST.json` and `RCJ_CONTRACT_TESTS.json` document the fixtures, real read-only mounts and hash gates. The isolated processor fixture uses native constructors and encoders with synthetic rows and a tokenizer loader stub; it covers 40+40 PASS, 80-row fallback and deliberate processor mismatch. No production reconstruction, real-row check, Orchard submission or GPU forward ran locally.
