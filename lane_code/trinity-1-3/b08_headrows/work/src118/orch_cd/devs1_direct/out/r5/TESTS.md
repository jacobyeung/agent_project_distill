PASS: eight full-journal integration cases, three paired reports, an f17 merge through the production CLI, and the real CP1 merge. All commands use `/scratch/jjyeung/envs/p1cpu/bin/python -I -s`; no GPU, SSH, Git, network, or shared-storage access is required.

The missing test was a call to `merge()` with all dev types. Pass-3 tested `score_item()` for all 11 types, and those tests correctly passed: that function already handles both dev-only multiple-choice types. Dry binds stop before reading any generation journal. They never call `benchmark_summary()`, whose official scorer rejects the two extra names. The new tests reproduce that original exception before installing the wrapper, then run the whole merge.

| Synthetic case | Source tasks | Types | Arms merged |
|---|---:|---:|---|
| aws_vl64rt, duplicate, main | 1,525 | 11 | ON16k, B2048, B4096 |
| aws_vl64rt, spread, main | 1,525 | 11 | ON16k |
| aws_eval_gaps, duplicate, main | 1,525 | 11 | ON16k |
| aws_eval_gaps, spread, main | 1,525 | 11 | ON16k |
| aws_vl64rt, duplicate, facing-away | 150 | 3 | ON16k, B2048, B4096 |
| aws_eval_gaps, spread, facing-away | 150 | 3 | ON16k |
| aws_vl64rt, duplicate, forward twins | 150 | 3 | ON16k, B2048, B4096 |
| aws_eval_gaps, spread, forward twins | 150 | 3 | ON16k |

Cross-layout cases exercise the merge interfaces, not alternative approved checkpoint protocols. Production remains CP1 duplicate and f17 spread. Every fixture uses its cell's complete pinned task set. Synthetic token IDs and parity receipts test CPU behavior; they make no claim about actual pixel or GPU parity. Fixtures remain under `work/r5/synthetic_final`.

| Step not exercised by a dry bind | Added test and result |
|---|---|
| Existing-request admission | `test_merge.py:109` validates normal requests, refuses a changed binding, compares copied code inventories, and runs the f17 production merge CLI. The real CP1 command verifies its original request, payload, code archive and tokenizer manifest. |
| Full journal admission and item rescore | Eight merges read actual JSONL fixtures. Negative checks reject changed layout, score and GT in both kits; CP1 additionally rejects changed model/thinking. Every type includes correct, wrong, empty, unclosed, invalid-option and capped rows. |
| CP1 token and 4,096-token-prefix authentication | Negative checks reject changed token IDs and changed stored prefix score. Main and prefix summaries retain all completed rows. f17 keeps its reviewed, narrower checks and original interface. |
| Parity gate | A merge with the wrong attempt has no matching parity receipt; numbers stay ineligible and the report refuses it. |
| CP1 budget receipts, reconstruction and projection | `test_merge.py:69` writes both arms and their authentic synthetic receipts. Original `BudgetContext` and `merge_budgets` validate them. Fixtures include forced close, stopped-unclosed output, failed derivation, capped parsed answers, and byte-preserved early-close reuse with more than 64 answer tokens. Altered receipt hashes are refused. |
| Benchmark and prefix summaries | Tests reproduce the old unknown-type exception, then check every per-type count and mean and the item-weighted overall against journal-row oracles. Empty/unparsed answers stay in the denominator. |
| Report extraction and label views | Every case exports all arms through `report.export_merged`. It checks exact task membership, ordered frame expansion, fps, total frames, timestamps, released-label remapping, own-GT rescoring, and counts. A changed timestamp is refused. All 11 types remain in main report tables, including zero-item strata. |
| Paired checkpoint comparison | `test_merge.py:228` compares CP1 ON16k/B2048/B4096 with f17 for main, away and forward families. A four-item/two-room hand oracle gives delta 100 pp and CI [100,100]; missing paired keys are refused. Synthetic reports use 200 replicates; production defaults to 10,000, seed 17. |
| Export integrity | The comparator checks completion receipts and export hashes. A modified score in an exported report is refused. |

Official preservation passes in both kits and both main layouts. `official5130`, `vsi500`, and `vsi500_slice` summaries compare equal before and during the wrapper. Other non-dev branches delegate to the identical original callable. The item scorer and official registries remain unchanged. Both reviewed runtime inventories and copied inventories compare byte-for-byte before and after the tests; see `BYTE_IDENTITY.json`.

The exact suite command was:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/r5/test_merge.py suite --dest work/r5/synthetic_final
```

Evidence: `TESTS_final.log`, `TEST_RESULTS.json`, `BYTE_IDENTITY.json`, and `work/r5/synthetic_final/{main,DEV_BACKDIR,DEV_FORWARD_TWINS}_PAIRED.json`. The final real CP1 command and its required paths are in `RUNCARD.md`; `MERGE_RESULTS.md` reports its measured scores. No empirical f17 or pass-4 generations were supplied for this pass; their merge/report coverage is synthetic.
