# Component evidence report

**No production component record is justified. All nine slots remain MISSING.**
The bundle contains nine gap files, a copied registry, a source survey and CPU gate checks. W was not edited.

| Slot | Status / record SHA256 or gap | Evidence basis | Overlaps found |
|---|---|---|---|
| init_m544 | MISSING; [gap](gaps/init_m544.json); no record | Step-544 artifact, LEG-S1 config, preparation receipts and BENCH v2. | Unknown: complete parent membership missing. |
| heads_pose | MISSING; [gap](gaps/heads_pose.json); no record | Step-544 artifact, LEG-S1 config, preparation receipts and BENCH v2. | Unknown: complete parent membership missing. |
| heads_depth | MISSING; [gap](gaps/heads_depth.json); no record | Step-544 artifact, LEG-S1 config, preparation receipts and BENCH v2. | Unknown: complete parent membership missing. |
| heads_frame_embeddings | MISSING; [gap](gaps/heads_frame_embeddings.json); no record | Step-544 artifact, LEG-S1 config, preparation receipts and BENCH v2. | Unknown: complete parent membership missing. |
| depth_init_vc | MISSING; [gap](gaps/depth_init_vc.json); no record | Step-544 artifact, LEG-S1 config, preparation receipts and BENCH v2. | Unknown: complete parent membership missing. |
| geometry_tower | MISSING; [gap](gaps/geometry_tower.json); no record | N configuration, G3T/GF1 freezing code and tower selection receipts. | No complete component-level conclusion. |
| segmenter | MISSING; [gap](gaps/segmenter.json); no record | SAM3_RECEIPT.json: upstream revision and checkpoint hash. | No complete component-level conclusion. |
| data_rows_r2 | MISSING; [gap](gaps/data_rows_r2.json); no record | Deferred component_rows record, v7 store, row-family receipts and recomputed partial intersections. | 0 in resolved populations; 119,375 v7 rows unknown. |
| heads_gf1_connector | MISSING; [gap](gaps/heads_gf1_connector.json); no record | N config geometry_connector=none and r1_components deferred-slot rule. | No complete component-level conclusion. |

The policy accepts only hash-bound `r2-component-evidence-v1` records. Lineage needs explicit overlap lists and all three checked banks. Frozen exemptions need actual frozen weights; new training needs complete exclusions.
The policy permits the disclosed venue `381879` exception. No overlap was suppressed or assigned that exception.
N sets `geometry_connector=none`; the strict component policy still requires `heads_gf1_connector`. No clean claim is inferred from that setting.

The [survey](SURVEY.json) lists 325 source files with hashes, what each proves and what each lacks. The readable version is [SURVEY.md](SURVEY.md).
The local b01 source tree matches all 792 entries in the sealed code inventory. The two other named source archives were copied once each; they do not supply parent scene manifests.

Fresh scene checks use the unchanged `r1_rooms.Rooms.canonical` and `Rooms.room`, including ScanNet room grouping, ScanNet++ aliases and ARKit visits.
The bank membership source is `benchmark_scene_exclusions.json` / BENCH v2, SHA256 `3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`.
[BENCHMARK_SCENES.json](BENCHMARK_SCENES.json) preserves the bank-specific lists and input pins. [INTERSECTIONS.json](INTERSECTIONS.json) records every observed intersection and unresolved count.

| Observed population | Rows | Resolved | Unresolved | VSI-Bench / VSTI / ReVSI intersections |
|---|---:|---:|---:|---|
| Dev-S1 captures | 224 | 224 | 0 | 0 / 0 / 0 |
| absolute_distance | 8,315 | 8,315 | 0 | 0 / 0 / 0 |
| recovery | 994 | 994 | 0 | 0 / 0 / 0 |
| units | 8,577 | 8,577 | 0 | 0 / 0 / 0 |
| v7 row store | 204,413 | 85,038 | 119,375 | 0 / 0 / 0 |

These are raw surviving populations before N-side removals. The dev set is not a training manifest; the routing slices do not cover all production families. No lineage intersection is claimed.

CPU self-check ([full output](SELF_CHECK.json)):
- `components(registry, "training")`: REFUSE — `Missing component evidence: init_m544`.
- `components(registry, "native_evaluation")`: REFUSE — the same reason.
- Each of the nine requested slots: REFUSE — `Missing component evidence: <slot>`.
- Unchanged `read_bank` gateway, synthetic fixtures labeled VSI-Bench, VSTI and ReVSI: REFUSE — `Missing component evidence: init_m544`.
- Existing `tests.test_r2_policy`: 5 tests passed; [test log](policy_tests.log). The local policy and test bytes match W.
No official benchmark items were read. Native evaluation also requires five program-choice records outside this task; those remain null.

Missing named sources (full expected paths, hashes and referencing records are in [PIN_RESOLUTION.json](PIN_RESOLUTION.json) and the gap files):
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/97a6a3eb/runs/b19c1200/train/step_400/heads.json` — SHA256 `fd60ac2f525727836258ae7ea0705ff3a49163ae74320f7bf8a17b66cd69f0c7`.
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f2ad01ad/runs/49becb79/m200/artifact.json` — SHA256 `c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67`.
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/u/7c9f2d84/receipt.json` — SHA256 `93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a`.
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/5e1d07a4/f/h/r16/receipt.json` — SHA256 `9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851`.
- `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/1742c666/s/q127808/vxm_m4/receipt.json` — SHA256 `524b14f9f180ba7d2c1c860cab294145b7370f3f1282960a55bbcbc6c5657634`.
- `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a2v3/receipt.json` — SHA256 `30612832cc84ad83f9500ecbeac57704767568ff24482475feb42a92c7f166b8`.
- `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a3v2/receipt.json` — SHA256 `1e7b491b810bd45b47a6d0e02be2f123e0ba8f8851f3e48fc1164f15611c9201`.
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/pointing/rows.sqlite` — SHA256 `faa0cfc43bed88bf0f2dad6da57bc57c7dcfb8c3aba65cecc045a3de327cc85d`.
- `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a2v3/rows.sqlite` — SHA256 `b32359ce256a567912d6436fac95dcab78bcef3bb2e1154cabdca57bacdc5320`.
- `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a3v2/rows.sqlite` — SHA256 `0b95850a2dec57ec6702ca72cd198eb5afdcdcdd5f711a76a878104e30ec3571`.
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/routing/rows.sqlite` — SHA256 `c48d5b6201c935e2de8e985d2d8a163d9bb46603e693e790733e3c86fe59db53`.
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/vqa/rows.sqlite` — SHA256 `5deb54bc4ef34c46371916feb2ab7fc83a707666cc36c5f2749b144647caa81d`.
- `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/5e1d07a4/f/h/r16/rows.sqlite` — SHA256 `3d1d2d05bc8d3fed3048618da0c25b330f693e6394c6e2564c3007d64c050001`.
- Complete inherited scene manifests and parent membership receipts for `49becb79/m200` and `b19c1200/train/step_400`. Their exact manifest filenames are not recoverable from surviving metadata; none was invented.
- Geometry tower release, weights/config identity and actual frozen optimizer inventory bound to N. The joint receipt filename is unknown.
- Actual frozen SAM3 inventory bound to N and the checkpoint in `SAM3_RECEIPT.json` (`9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e`). Its inventory filename is unknown.
- Complete independent scene mapping for the 119,375 unresolved v7 rows, complete post-filter family manifests, and frame-host membership. The current `component_rows.json` explicitly leaves these unresolved.
- GF1 connector parameter inventory and complete clean training/exclusion receipt. Its original filename is unknown.

Commands that produce the reported numbers:
- Source hashes, source count and 792-file archive check: `bash work/run_python.sh work/survey.py`.
- Population counts and bank intersections: `bash work/run_python.sh work/intersections.py`.
- Nine gap decisions and copied registry: `bash work/run_python.sh work/build_gaps.py`.
- Phase, slot and official gateway results: `bash work/run_python.sh work/self_check.py`; this also records the exact unittest command that produced the five-test result.
- Any individual file checksum: `sha256sum FILE`. SQLite candidates were hashed sequentially in 8 MiB blocks; their exact digests are retained in `audit_inputs/sqlite_index.json`.
- Archive and validation: `bash work/run_python.sh work/package_report.py`; independently verify with `sha256sum out/sb_evidence_records.tar`.

The archive includes this report without the final archive-checksum footer. It excludes the tar itself and its checksum sidecar. Source paths remain provenance references; the archive contains no training databases.
The no-archaeology skill governs report wording. No historical-process sentence requires an exception.
