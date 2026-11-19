# Counting conversion kit

The kit contains 17,564 TALLY rows: 8,404 single-category and 9,160 multiple-category rows. The same sources can be emitted with `--form locate` (17,564 rows). The alternatives must not be concatenated.
All 17,879 removed lists convert mechanically: 8,678 single-category and 9,201 multiple-category. The kit refuses 315 rows: 228 K1 held-out, 84 without independent instance annotations, and 3 without a canonical room mapping. `REFUSALS.jsonl` lists every qid and reason.
Source: pinned store v7, SHA256 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443; removal reason `count_diag_first_seen_list_form` in z.json. W/w19 is the newer sealed kit; tree seal 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa.

| Eligible source pool | Rows |
|---|---:|
| b12_cntapp_gt_v1 | 10004 |
| r1g | 6362 |
| rows_rebuild_d0_ARKIT_gaps | 341 |
| rows_rebuild_d0_T0_gaps | 282 |
| rows_rebuild_d0_T1H1_gaps | 300 |
| rows_rebuild_d0_T1H2_gaps | 275 |

| Final truth | Rows | Single | Multiple |
|---|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 1 | 22 | 22 | 0 |
| 2 | 5028 | 5028 | 0 |
| 3 | 2443 | 1506 | 937 |
| 4 | 3589 | 817 | 2772 |
| 5 | 1854 | 356 | 1498 |
| 6 | 1355 | 224 | 1131 |
| 7 | 896 | 119 | 777 |
| 8 | 689 | 99 | 590 |
| 9 | 454 | 78 | 376 |
| 10+ | 1234 | 155 | 1079 |

12,514 eligible rows have truth at least 3. Truth means the final stored answer; multi-category rows contribute once. Category totals and frame counts are recorded separately in QID_MAP.jsonl and the target.
Every admitted row passes independent instance-ID/frame recomputation, source-region preservation, ordered frames in 1..32, asked-category coverage, category sums, final sum, field-diff checks, and qid/candidate uniqueness. The kit candidate_identity formula uses the new qid and unchanged question. Each source appears once per form.
The independent audit covers 82,037 annotated instances across 32,909 category inventories. 10,004 rows retain region tags. No raster or image was read; this checks annotated labels, not visual truth.
Rooms: the pinned K1, R0, withheld-80, dev-S1, and BENCH v2 authorities exclude held-out rooms. Unresolved rooms are refused. Additional aliases come only from stored canonical/raster fields whose native scene reproduces the pinned token hash; `inputs/scene_facts.json` records the source qid and field.
Questions, answers, images, and all source fields except qid, candidate_id, target, and provenance.sb_rowT stay identical. The 30 full rows in READ30.md were read for category coverage, grammar, arithmetic, and region counts; all pass the proposed TALLY specification. Inherited question morphology such as shoes(s) stays unchanged.
Wording: Unicode NFKC + casefold + whitespace normalization; Levenshtein/max length threshold <=0.10. All 117 question/prompt wordings found across 42 sealed-kit/fixture files screen each newly authored trace body; 0 rows removed. No new question wording is generated. This does not certify absent external evaluation corpora; see MISSING.md.

Current N validation: all 17,564 source rows pass native direct-row validation and trace grammar; all 17,564 TALLY rows fail that unchanged grammar. `ground_rows.pack` refuses both direct sources and new rows with KeyError suffix; it is a program-only API, not the direct-store packer. No ground_record is fabricated.
Locate alternative: native passes 17,564; lexical grammar passes 17,564. Counting admission still rejects both alternatives: the gate requires procedure wording and bans totals. No claim that all requested trainer checks pass is made.
TRACE_RULE_AMENDMENT.md supplies the exact proposed rule and required validator/admission changes. The kit keeps the current trainer unchanged. Its status is KIT ONLY, pending the orchestrator amendment and a fresh native admission check.

Reproduction commands (run from this workspace with local Python >=3.10):
```sh
PY=/scratch/jjyeung/envs/p1cpu/bin/python
gcc -O2 -shared -fPIC ned_filter.c -o ned_filter.so
$PY -B prepare_inputs.py
$PY -B convert_rows.py
$PY -B convert_rows.py --form locate --out out_locate
$PY -B check_rows.py
$PY -B check_rows.py --out out_locate
$PY -B test_contract.py
$PY -B finalize_kit.py
sha256sum out/sb_rowT.tar
```
prepare_inputs.py produces source counts and input hashes; convert_rows.py produces every cell/refusal/histogram/validator count; check_rows.py independently produces the instance, region, source-pool, and coverage counts; test_contract.py produces the 10 mutation/distance checks. Human READ30 review is recorded separately and must be repeated if its bytes change.
The archive includes the extracted source rows and audit inputs. The generator imports the sealed W/w19 tree at the path in inputs/INPUTS.json; rerunning prepare_inputs.py additionally requires the pinned external v7 store. No trainer tree is modified or bundled.
Not done: trainer edits, training, GPU work, image/raster verification, and external evaluation-item staging. No network, SSH, Git, process termination, or file deletion was used.
Writing review: no borderline revision-history sentences retained.
