# R3 routed packages A and B

Findings 1–3 are fixed. Finding 4 reproduces the authentic baselines and passes self-comparison; its accepted-source bootstrap check remains blocked because `room_bootstrap.py` is absent from W. No failing assertions remain. This is not a claim that all four findings are closed.

Deliverables are [A](A/) and [B](B/). `out2/` is untouched. Both payloads remain byte-identical; both deliveries changed. Tokens `d72cdcff1e22a` and `b9188e9225a85` remain because neither package was placed or submitted. No payload member changed.

## 1. Complete export identity

`A/fill_export.py:11` and `B/fill_export.py:11` seal the object, byte count and full digest as constants; each delivery's PACKAGE.json pins this helper at `a/4.py`. `receipt_review:146` rejects a different receipt before scanning. `bind_review:152` rejects different actual whole-archive bytes or digest, even if a caller also mutates the supplied binding. The inherited `scan` and `preparation` functions remain AST-identical.

Both READ_PLAN files record the complete binding (`A:25`, `B:34`). `A/o_pullfill.sh:33` checks the exact receipt before transfer. The required values are object `q8/8865619b/673bc60f_m200.tar`, **21,583,032,320 bytes**, SHA256 `795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b`.

Both helpers reject a wrong digest with the correct prefix, a wrong prefix, wrong bytes, and a wrong receipt object. The three real preparation files pass. Two integrated checks use those exact files and unchanged production payloads with a small synthetic artifact; only disposable test helpers substitute its archive constants. The full 20 GiB export is not local and still requires the Orchard scan.

## 2. Return provenance inside fetch

`A/fetch_return.py:19` and `B/fetch_return.py:19` enforce plan, exact requested token, synthetic=false, bytes, digest and completion status. `validate_receipt:35` checks the pool receipt and its file pins; `fetch:72` checks job identity before creating output and authenticates copied bytes again. Authentic partial returns remain fetchable.

Both `o_fetch.sh:13` use the sealed `a/7.py`. Both delivery `package/3.py:6` wrappers route `3.py fetch` through the same helper. Neither entrypoint reaches the unchanged payload's weaker fetch function. The tests reject wrong plan/token/synthetic flag/bytes/digest/status through the helper and Python 3.6 wrapper for each package. `unpack_return.py:30` also checks token, plan, job and bytes.

## 3. Transfer retries

`A/o_pullfill.sh:39` sets `Boto:num_retries=0`, one metadata attempt, one process and thread, and disables sliced downloads. There is one cp invocation inside the four-part sequential loop; B has no transfer command. The command test checks every setting and executes the loop with a failing local shim: one attempt, exit 7, no next part or final file.

## 4. Authentic baseline restoration and scores

Both package unpack helpers restore the exact registered returns through an explicit baseline mode (`unpack_return.py:23`). It pins the baseline token and archive digest; only that mode reads the baseline delivery's input/export metadata because those snapshots are absent from the older returns. [BASELINE_RESTORE.json](BASELINE_RESTORE.json) records commands and source hashes. Pool/EXIT/archive identities pass; JOB.log's pinned initial prefix matches, and its appended final receipt matches RETURN_RECEIPT.json.

| Baseline measurement | Reproduced | Registered | Difference after rounding |
|---|---:|---:|---:|
| Tower displacement / movement direction / rotation | 82.33 / 94.67 / 75.60 | 82.33 / 94.67 / 75.60 | 0 / 0 / 0 |
| Tower distance, candidates_argmax | 28.27; 0/150 capped | 28.27; 0/150 capped | 0 |
| Room native-answer MRA | 6.57; 134 items; 115 capped | 6.57; 134 items; 115 capped | 0 |

`score_r1route.py --self-test` passes every zero-difference and zero-width 95%/99.29% interval check. Camera calls are 450/450; non-metre conversions are 29/107. The room scorer reproduces the exact scores hash `9d3809d30712dc75c17857cb97d77dcd1cfd9fe6912d5676fdc0bc25cee04aa8`. The supplied own-arm comparators cannot be remeasured from these tower-only returns. Scoring mathematics remain unchanged.

`test_score_r1route.py:14` still cannot load the accepted `room_bootstrap.py`. [bootstrap_reference.py](bootstrap_reference.py) is explicitly a new independent stdlib calculation, not a recovered source. It matches the scorer at 95% and 99.29% on unequal room sizes and nonzero perturbations of real baseline scores (`test_baseline_r3.py:46`). That evidence does not close the accepted-source comparison.

## Gates and hashes

All out2 gate groups were rerun. [GATE_SUMMARY.json](GATE_SUMMARY.json) records the cases and blockers: base A **47 passed / 10 blocked**, base B **53 / 1**, release A **43 / 0**, release B **49 / 0**, original scorer **7 / 1**. The 11 base blockers require missing predecessor fixtures/text, as listed individually in that file. A random fixture basename collided with the opaque-name guard; the test now generates hex names and passes without changing production checks.

Supplementary checks pass: **29** R3 regression tests, **8** baseline/reference tests, **18** small-fill cases, **2** synthetic-preparation integrated cases, **2** real-preparation integrated cases, **4** return CLI cases, **2** Python 3.6 guard/dispatch cases, **10** shell syntax checks, **30** Python 3.6 compilations, and **12** operator guards. No failed/error cases remain. Test-copy archive substitutions never enter a delivery.

| File | Final SHA256 | Identity versus out2 |
|---|---|---|
| A/0.tgz | `a74371ce0554bb0b27c98d2141350bd2a1f1e24dee2879f04b102a6b88e49c37` | Identical |
| A/1.tgz | `ca977dd2bc6feb1c14c7c03023eefe7b5e2b67b1cabe838d34effbafd003c765` | Changed; resealed |
| B/0.tgz | `ab26b592277b4c44843b0ce30862d2ab9b8a00d76d7b06027b0414e588cdc05f` | Identical |
| B/1.tgz | `be1f4dec0a2607e0590f0392ef1f7b6c44e3f60c34a06ad6b6a3f3cd551ea3ad` | Changed; resealed |

[BYTE_IDENTITY.json](BYTE_IDENTITY.json) records both archive pairs; [FINAL_HASHES.json](FINAL_HASHES.json) includes manifests, plans, scripts and helpers. Each delivery changes only `3.py`, `a/4.py`, `a/7.py` and PACKAGE.json. Each package's R3_OPERATOR_DIFF.patch records the complete operator change.

## Operator order and re-review

Follow [A/OPERATIONS_R1ROUTE.md](A/OPERATIONS_R1ROUTE.md) and [B/OPERATIONS_R1ROUTE.md](B/OPERATIONS_R1ROUTE.md): place both resealed deliveries; fill A once; fill B from A's retained parts; complete A's CPU check, GPU job and fetch; then complete B's CPU check, GPU job and fetch. Retain A's parts, transfer the returns and recorded job IDs, unpack with the expected tokens, and score against the restored baselines. Each GPU submission requires the existing queue, CPU-receipt and pool guards.

The re-review must verify the four final archive hashes, delivery helper pins and diffs, exact export constants, both fetch entrypoints, explicit retry settings, baseline archive/score identities and every blocked case. It must supply the accepted bootstrap source and rerun that reference check before treating finding 4 as closed. The allocated Orchard CPU checks remain mandatory.

All commands ran locally on trinity-3-30. Searches stayed in W; writes stayed in W. No SSH, Git, network, submission, kill or deletion ran. The no-archaeology skill guided this report; comparisons remain because the brief requires byte identity and review evidence.
