**ACCEPT WITH FINDINGS.** The patch is ready for the serving lane; apply the documentation edits below. No patch-code edit is required.

Archive SHA-256: `ebbd8d42bb7de829d8debbad027d658e9e9f2d0647bfa8c0bc79a7510a179279`. `bash run.sh prepare_review.py` copied A4/src and applied the exact patch without fuzz; `bash run.sh audit_archive.py` verified packaged files.
The inspected served path cannot mix presences within a name/frame: `b/e2e_reader/stage1.py:82–104` sends one raw-name prompt and stamps one scalar on every retained instance; `StageOne.features` keeps names separate.
`stage1_factory` always binds that detector. `perception_memo.sam_encode` caches encoder pyramids/sizes only; A4 enables only G3T memoization. `Sam3Tower` rejects alias/tile settings and encodes whole frames.
The fallback is safe for all inspected A4 producers: both stage1 copies and all `detections` branches supply presence. `bash run.sh audit_inputs.py` found zero instance `presence` keys and zero missing record keys across 114,973 stored instances in 209 K1 captures; individual sample paths are recorded.
`dict.get` eagerly evaluates `record['presence']`, so record presence remains mandatory; explicit zero is preserved. `bash run.sh probe_contracts.py` verifies both behaviors and exercises the actual served detector with a CPU stub backend.
`bash run.sh -m pytest -q -p no:cacheprovider work/test_cachefix.py`: **29 passed, none skipped** against my patched A4 copy.
`bash run.sh mutations.py`: **4/4 killed**. Stamp first presence: 6 failures; ignore instance presence: 6; remove legacy fallback: 1; replace fallback with zero: 1. These are assertion/KeyError failures, not collection failures.
K1 commands: `bash run.sh work/k1diag.py today 0 1`, `bash run.sh work/k1diag.py fixed 0 1`, then `bash run.sh compare_parity.py`. Both arms use the same raw-name detector and A4 modules; only the patch differs.
K1: **0/770 selections and 0/1,037 printed gaps changed**, across 209 captures; accepted lists, vectors, proposals, boxes and refusals match exactly. Published A0 matches 1,037/1,037; paired MRA is +0.00 [0.00, 0.00] (192 rooms, 10,000 draws, seed 20261119).
`bash run.sh audit_inputs.py` scanned the journal roots below (`OUT3=/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3`; suffix `/metadata/journals/*/*/items.jsonl`). Exact filenames and hashes are in `evidence/input_audit.json`.

| Read root under OUT3 | Step | Journal files | Diagnosed pools | Nonempty frames |
|---|---:|---:|---:|---:|
| `A4/ret/metadata/reads/0` | 200 | 5 | 176 | 1,602 |
| `B5/ret/metadata/reads/0` | 200 | 1 | 0 | 0 |
| `bases/b1/work/ret/metadata/reads/0` | 544 | 5 | 346 | 3,352 |
| `bases/b1/work/ret/metadata/reads/1` | 544 | 1 | 298 | 2,836 |
| `bases/b2/work/ret/metadata/reads/0` | 544 | 1 | 0 | 0 |

Served mixed-frame zeros are **code-inferred**, not measured per-instance counts. Journals support 0/6,487 range violations and 0/4,434 single-member mismatches. Seven b1 ground records lack pools (three malformed calls, four unserved); all 34 b2 ground records are unserved. Raw K1 mixing is directly measured: 0/8,553 frames, 0/770 names; merged pools mix in 2,842 frames (1,218 after score ≥0.3).
Step 400: **MISSING**, expected `/scratch/jjyeung/step400/ret`; no affected-read count can be assigned.
`routed_features.detections` still discards instance `presence` and `source_presence`; the probe reproduces the collapse. Before merged-pool experiments, resolve each entry’s presence before validation/emission and retain record fallback. This separate defect does not block this served-reader patch.
Exact report edit: label served-table zero mixing cells “0 inferred from inspected served code; per-instance presence not journaled”; retain the separately measured K1 counts.
Exact review edit: in `review/REVIEW.md` finding 7, replace the `8.py:30 / Helper differs` module-check attribution with `orchard_h10/job.py:107–108 / Code payload differs`.
Exact test-docstring edit: replace the legacy-cache test’s caller list with “Direct legacy-cache compatibility; the named production callers use separate lift implementations.”
Landing: A4 `src/9.json` pins both original modules; the staging verifier rejects their patched hashes. Build a new sealed package and binding, and launch it at an epoch boundary. Do not patch the existing sealed A4 in place.
Evidence: `evidence/{preparation,mutations,input_audit,contracts,parity,archive,final_checks}.json` records input SHA-256 values; per-capture parity records include their inputs. `bash run.sh finalize_evidence.py` checks identities. CPU only; all writes stayed in this workspace.
