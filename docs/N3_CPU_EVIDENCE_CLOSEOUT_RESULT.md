# N3 CPU evidence closeout — result record

This record preserves the CPU evidence packet at `O` below. The documentation checkpoint authenticates its retained machine receipts; it runs no new inference and changes no source, recipe or score authority.

**Date:** 2026-10-07.

**Decision stage:** postrun.

**Final gate:** NO-GO for promotion; GO for the completed saved-generation CPU replay only.

**Execution:** complete for the four authenticated seed-17 banks; the required four-arm, three-cohort comparison remains incomplete or unverified.

**Scientific status:** inconclusive; all outcomes remain provisional.

**Controlling reason:** The short-primitive arm passes the frozen consistency guard on only 34/250 trained-family outputs (13.60%), below 90.00%. Both overall paired intervals include zero. Paired seed-18 and full-Debiased results are not authenticated in this packet.

**Attempt budget:** Planned four saved-bank CPU replays and no inference, training, paid calls or new reviews. Actual four replays, 17 group bootstraps with 10,000 resamples each, and 39 parser tests; no inference, training, paid calls or new reviews. One external authentication-reader attempt stopped on an archive-entry schema difference; its corrected retry preserved the initial receipts. No source artifact changed.

**Authority statement:** Codex chose this evidence-closeout lever under the 2026-10-07 ruling. This record makes no benchmark nomination, target-achievement claim or retrospective prediction registration.

## 1. Hypothesis and mechanism

N3 tests whether one short perception-primitive line improves the student when the answer-only control and short-primitive arm receive identical coverage replay. AR is the answer-only control; SR changes the canonical target to the existing primitive followed by the same answer. Both arms retain the same 7,548 training rows, including 3,795 canonical rows and 3,753 identical answer-only replay rows. The comparison estimates the primitive-target effect conditional on replay; it does not isolate the effect of adding replay.

The frozen contract requires AR17, SR17, AR18 and SR18, with matched generation settings and the prescribed full-Debiased comparison. The training targets use privileged GT-assisted supervision, so this diagnostic cannot establish a clean teacher-distillation result. Equal rows and optimizer steps also do not equalize supervised token counts. The audited VSI-590K identity count is 4,846, not the brief's requested 5,348 label.

This lane resolves the parser discrepancy without another generation. It reuses the native seed-17 banks and leaves all training/evaluation ownership intact. The planning document supplies decision context, not scoring authority. The primitive guard and the two-seed/full-cohort requirements remain unchanged.

## 2. Exact implementation and provenance

The read-only production checkout is `/home/jjyeung/agent_project_distill`, at `b83b3df17d510ac8a4389c4202450aa333526b98`. It remained clean. Let `C` denote `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/covfmt9b_20261004` and `O` denote `/data2/jjyeung/agent_project_data/codex_distill_orchestrator_20261007/n3_evidence_closeout_devin_01`.

- The source bundle uses commit `fcd2a131b371374752ee7f6cced6be78c88a90f0`; the scoped runtime review binds `7431a162c07725bcdaf3603f6c4635f8e65d8a60`. All 261 direct path/hash references checked across the bundle, plans and review/runtime bindings match. These are direct retained bindings, not a fresh replay of every source geometry calculation.
- The native trainer is `64d01b4c68a341e6cd88ba990d231b91c68a5a6e`. The model is Qwen3.5-9B at `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. The retained publication receipts verify AR17, SR17 and AR18 at 236 actual optimizer steps, versus the brief's 237; 7,548 rows at effective batch 32 require 236 steps. This lane authenticated those receipts and the evaluated adapter identities; it did not rehash remote adapter weight files.
- The saved seed-17 cells use mnb6s, 32 original RGB frames, decode batch 6, greedy decoding, one output and a 4,096-token cap. Training seed 17 and decoding seed 17 are distinct fields. The native generation configuration hash is `b43a012b7dfebe6dcb798840dd57a632612b5dd4c43fc8a5c2a73d7fa7a4b9f1`.
- The four generation files are `C/out/returns/t73_mnb6s_covfmt_{AR,SR}_s17_{vsi,vsti}_20261005/run/generations.jsonl`. Their 1,900 immutable per-question receipts exactly equal the saved projections, preserve ordered membership and match their recorded hashes. The corresponding answer-bank archives match their retained entries. Returned files and archives are authenticated copies, not reviewed score authority.
- VSI preserves all 500 questions. VSTI preserves the canonical corrected 450-question authority and its provenance, including the required cohort and answer mappings. Scoring manifests, labels, source-authority bindings and both arms' membership/configuration identities authenticate. Data-bearing hashes remain in external evidence, not this record.
- The reviewed parser is commit `126a81b62b2b885cfd81ee2b6de824393a17cbfa`, SHA256 `a5fdda78c451e802bdc981b6b317c05de5281fde57b2c0517c5481044530bfc5`. Its upstream Git object, retained parser checkout and candidate `student_pilot/orchard_eval/answers_lenient_v2.py` at integrated evaluator commit `3440c3a7af6f3efc368158bcba75173af6a5386f` have identical bytes. The parser retains an inherited v1 metadata string; its reviewed commit and bytes distinguish v2. No integrated evaluator deployment occurred.
- The native metric implementation remains SHA256 `f67703ea8fbca0db13f922e34dc778ead6a546e0b574435e8924c00da6b609c5`; its composite aggregation remains `503a16f193cc4974e4904103eda35138420dfc8c71dac48574d304d52c8194a9`. The contracts remain `vsibench-official-8task-v1` and `vstibench-official-5subtask-v1`, including their numeric credits and category collapses.
- The unchanged saved-answer rescorer is `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/scripts/orchard_lenient_rescore.py`, SHA256 `2590ea5043c06e0a0e6ef6786c2229cf26a23a74c93ff0d339b234fa569d7219`. The unchanged paired-bootstrap helper is the sibling `hillclimb_20261004/paired_bootstrap.py`, SHA256 `b6412a5c0e925d3e8fb67fdc828f2d6118071ad3e5d3f40bd9bc6709000d80b5`.

### Paired v2 results

All scores below are provisional percentages. Deltas subtract AR from SR. Each interval uses 10,000 paired question resamples within raw question type, with bootstrap seed 20261005; it does not measure training-seed variation.

| Cohort or group | n | AR17 | SR17 | Delta, points | Paired 95% interval |
|---|---:|---:|---:|---:|---|
| VSI-500 overall | 500 | 54.48 | 57.36 | +2.88 | [-0.48, +6.26] |
| VSTI-450 overall | 450 | 46.35 | 50.08 | +3.73 | [-0.51, +8.01] |
| VSI trained families, T3 | 250 | 53.82 | 57.69 | +3.87 | [-2.13, +9.91] |
| VSI coverage families, U3c | 150 | 52.20 | 57.47 | +5.27 | [-0.47, +11.20] |

VSI has 79 questions with increased credit and 74 with decreased credit; 36 change from zero to full credit and 33 from full credit to zero. VSTI has 81 increased and 54 decreased credits, with 46 zero-to-full and 32 full-to-zero changes. Numeric partial credit and the category macro mean determine the net score; flip counts alone do not. These are observed outcomes, not preregistered predictions.

| Native merged category | n | AR17 | SR17 | Delta, points |
|---|---:|---:|---:|---:|
| VSI appearance order | 50 | 66.00 | 74.00 | +8.00 |
| VSI absolute distance | 50 | 42.60 | 40.40 | -2.20 |
| VSI counting | 50 | 38.80 | 50.40 | +11.60 |
| VSI relative direction | 150 | 60.67 | 54.67 | -6.00 |
| VSI relative distance | 50 | 62.00 | 68.00 | +6.00 |
| VSI object size | 50 | 59.60 | 57.60 | -2.00 |
| VSI room size | 50 | 58.20 | 55.80 | -2.40 |
| VSI route | 50 | 48.00 | 58.00 | +10.00 |
| VSTI camera displacement | 50 | 23.40 | 28.20 | +4.80 |
| VSTI camera movement direction | 50 | 34.00 | 36.00 | +2.00 |
| VSTI camera–object absolute distance | 50 | 39.00 | 42.20 | +3.20 |
| VSTI camera–object relative distance | 150 | 64.00 | 68.00 | +4.00 |
| VSTI object–object relative position | 150 | 71.33 | 76.00 | +4.67 |

The external results retain all raw-category denominators, category intervals and per-question paired credits. No category or failed answer is dropped.

### Parser-only effects and strict secondary check

V2's end-of-turn rule recovers five AR17 VSI answers. Two gain credit, increasing that arm by 0.40 points and reducing the VSI SR advantage from the recorded v1 value of +3.28 to +2.88. The other three recovered answers retain zero credit. No SR17 answer and no VSTI answer changes. These changes belong to the parser, not the student. No new inference was performed.

Strict replay reproduces every native per-question credit and the native aggregates: VSI AR17 54.08 versus SR17 57.36, and VSTI AR17 46.35 versus SR17 50.08. V2 leaves zero answer-parse failures in all four cells. Answer parsing and primitive consistency are separate checks.

### Primitive guard

The frozen audit reproduces 34/250 consistent outputs, or 13.60%. All 34 are counting tallies. The 216 failures comprise 16 counting, 50 relative-distance and 150 relative-direction outputs; each starts by closing thinking and contains no nonempty primitive body. None contains the canonical tally, distance or signed-turn markers elsewhere in its raw output. There are no malformed nonempty primitives, multi-line primitive bodies or canonical arithmetic contradictions in this audited population.

This evidence identifies missing primitive emission, not a more permissive answer-parser repair. It does not identify why the model omits the primitive, and it does not establish whether any displayed perception is true. The unchanged 90.00% gate fails independently of the score readout.

### Twelve-cell evidence matrix

| Training arm | VSI-500 | VSTI-450 | Full-Debiased, 2,362 |
|---|---|---|---|
| AR17 | Saved bank authenticated; v2 replay complete | Saved bank authenticated; v2 replay complete | Retained native preflight only; no bank at the exact local cell path |
| SR17 | Saved bank authenticated; v2 replay complete | Saved bank authenticated; v2 replay complete | Retained native preflight only; no bank at the exact local cell path |
| AR18 | Publication and retained preflight exist; no bank at the exact local cell path | Publication and retained preflight exist; no bank at the exact local cell path | Retained native preflight only; no bank at the exact local cell path |
| SR18 | No authenticated saved bank in this packet | No authenticated saved bank in this packet | No authenticated saved bank in this packet |

A missing local bank is not proof that a remote attempt is absent or unfinished. `CELL_MATRIX.json` preserves exact paths, receipt hashes, admission statuses and the retained owner records. The original N3 controller lease remains with `covfmt9b_20261004`; newer Trinity training leases remain with `trinity9b_20261006`, and the evaluation status belongs to `trinityeval_20261006`. This lane neither takes over nor stops any worker. The timestamped adoption evidence is retained at `../adoption_codex_fallback_01/REPORT.md`; its observations do not authenticate the eight missing cells. Newer runtime/world-size training attempts must not be substituted for the code-aws banks without their own matched admission.

## 3. Reviewer findings

This lane commissioned no review and changed no reviewed scorer. It authenticated existing review evidence rather than manufacturing a new PASS. The following inherited findings delimit its authority; severity is unassigned where the original receipt supplies only a verdict.

| id | round | reviewer | severity | category | verified status | exact safe evidence | fix / disposition |
|---|---:|---|---|---|---|---|---|
| Parser compatibility | 3, inherited | Independent Devin parser reviewer | Not assigned; PASS | integrity | verified | `agent/scratch/devin_lanes/lenient_option_echo_review_20260924/out_v2/REVIEW.md`, lines 3–7 and 109–111, in the distillation checkout | Exact commit and parser bytes match; compatibility is not answer truth or benchmark nomination |
| Renderer and replay selection | 1, inherited | Independent Codex reviewer | Not assigned; PASS with warnings | scientific-validity | verified within retained scope | `C/out/review_codex_01/final_message.md`, lines 13–26 | Preserve privileged-supervision disclosures, row/step counts and destination gates; no fresh source-geometry or RGB rehash by this lane |
| Initial-scope helper binding | 2, inherited | Independent Devin runtime reviewer | Not assigned; REVISE | integrity | resolved in authenticated confirmation | `agent/scratch/devin_lanes/covfmt9b_20261004/review_required_SR18_02/VERDICT.md`, line 5; `C/out/review_required_SR18_codex_01/final_message.md`, line 21 | Existing runtime repair binds imported helpers; this lane applies no runtime change |
| Unreconciled N1 queue identities | 2, inherited | Independent Devin runtime reviewer | Not assigned; REVISE | engineering | resolved in authenticated confirmation | Same runtime verdict, line 7; Codex confirmation, line 23 | Existing admission rejects unknown queue identities; no GPU admission follows from this closeout |
| Full-cohort and two-seed evidence | Confirmation, inherited | Independent Codex reviewer | Warning | scientific-validity | verified unresolved requirement | `C/out/review_required_SR18_codex_01/final_message.md`, lines 13–15 | Full-Debiased submission/scoring lies outside that runtime packet; retained preparation is not completion |

## 4. Final decision and controlling reason

Do not promote SR or transfer it as a validated primitive-distillation gain. The failed primitive guard alone controls that NO-GO. The complete four-arm/full-cohort evidence is also unavailable, both overall intervals include zero, and training-seed spread is unmeasured. The U3c point difference of +5.27 does not satisfy the original literal within-five-points condition; its interval does not establish equivalence.

The CPU replay is complete and reusable. It shows how the reviewed parser changes the comparison without changing a model or making another generation. Both reviewed score indices verified mechanically, but the VSI development role and VSTI headline role queries remained quarantined. No reviewed score nomination was made or inferred.

## 5. What would change the decision

The owner must first identify and repair the primitive-emission omission through a separately reviewed mechanism change, while preserving the grammar, full denominator and 90.00% gate. The current evidence does not establish whether training targets, masking, model behavior or another boundary caused the omission. Inspect the preserved evidence before choosing that repair; do not rerun the unchanged fixed recipe.

The owner must also reconcile every missing cell against its exact publication, native bank, runtime and lease, and obtain the required paired seed-18/full-Debiased evidence under the existing four-arm contract. Question-bootstrap intervals cannot replace training-seed uncertainty. Any perception-fidelity claim additionally needs an independent sealed primitive-truth assessment. This packet authorizes none of those launches or source edits.

## 6. Salvage and non-revival boundary

Reuse the authenticated generation banks, publication receipts, exact parser binding, per-question credits, category readouts and bootstrap receipts. Preserve the source banks unchanged. Do not generate another answer for a parser discrepancy, mix v1 and v2 arms, count repeated questions across seeds as independent examples, loosen the primitive gate or treat missing evidence as a completed experiment.

No observed seed-17 recovery is registered as a future predicted flip. The lane assigns no new round number and makes no fixed-recipe rerun, benchmark nomination or target-achievement claim. Training-derived diagnostic lineage does not become clean teacher-distillation lineage through a change of label.

## 7. Audit receipts

All paths below are under `O` unless stated otherwise. Data-bearing or correctness-derived evidence is path-only in this canonical record. External machine receipts retain the hashes requested for authentication; they must not be copied wholesale into Git.

| artifact / sanitized path | availability | hash or omission reason | role |
|---|---|---|---|
| `AUTHENTICATION.json` and `AUTH_{AR,SR}_s17_{vsi,vsti}.json` | Present | hash=omitted_unsafe | Native membership, per-question, publication and copy checks |
| `SOURCE_BINDINGS.json` | Present | hash=omitted_unsafe | Retained bundle, plan and runtime path/hash checks, including data-bearing pins |
| `PARSER_V2_BINDING.json` | Present | hash=omitted_unsafe | Reviewed parser/source lineage and native metric bindings; includes data-related references |
| Reviewed parser source | Present | sha256:file_bytes:a5fdda78c451e802bdc981b6b317c05de5281fde57b2c0517c5481044530bfc5 | Exact v2 implementation |
| Frozen primitive audit source | Present | sha256:file_bytes:6de51a56623d0930cc7ad28fce8765adc5f641eae73718c63bba951e8cdef65e | Unchanged consistency grammar |
| `COHORT_AND_PUBLICATION_CONTRACT.json` | Present | hash=omitted_unsafe | Canonical cohort/source and retained publication checks |
| `V2_PAIRED_RESULT.json`, `V2_PAIRED_{vsi,vsti}_PER_QID.jsonl` | Present | hash=omitted_unsafe | Full-denominator paired scores, gains/losses and intervals |
| `RAW_CATEGORY_DELTAS.json`, `PARSER_ONLY_RECOVERIES.json` | Present | hash=omitted_unsafe | Raw-category comparisons and exact parser-only changes |
| `PRIMITIVE_CLASSIFICATION.json`, `PRIMITIVE_FEATURE_FLAGS.json` | Present | hash=omitted_unsafe | Raw-supported per-question guard dispositions |
| `CELL_MATRIX.json` | Present | hash=omitted_unsafe | Twelve cells, exact artifacts, owner metadata and unresolved admission |
| `VALIDATION.json`, `PARSER_TESTS.log`, `BOOTSTRAP_*_COMMAND.json` | Present | hash=omitted_unsafe | Deterministic reconciliation, 39 passing tests and 17 successful interval commands |
| `SESSION_METADATA.json`, `OWNERSHIP.json` | Present | Path-only operational metadata | Session and distinct CPU lease records |
| `../adoption_codex_fallback_01/REPORT.md` | Present, checked 2026-10-07 08:36Z | Path-only operational metadata | Timestamped host/ownership adoption evidence |

## 8. Validation and canonical routing

The retained `VALIDATION.json`, checked at 2026-10-07 08:32Z, records PASS for all four bank checks, 1,900 native receipts, 39 parser tests, both strict replays, 17 bootstrap commands, full-denominator aggregation and unchanged source generations. The primitive guard remains FAIL; validation success does not promote the model. These are retained CPU-lane checks, not new tests performed by the documentation checkpoint.

The native session is `handsome-brick`. The completed CPU lease is `cpu_evidence__covfmt9b_n3_closeout__saved_matched_cells__s17_18__0fda4c042f`; its terminal receipt covers this packet only. Training and evaluation leases remain with their existing owners. The canonical distillation record is `docs/N3_CPU_EVIDENCE_CLOSEOUT_RESULT.md`, accompanied by the current distillation handoff. Raw analysis remains under `O`; this documentation task edits no shared ledger, request queue, score authority or paper.

The documentation checkpoint checks the rounded scores against `V2_PAIRED_RESULT.json`, the guard against `PRIMITIVE_CLASSIFICATION.json`, the exact local parser/metric/audit source hashes, the retained evidence manifest and the scoped document links. Its external validation receipt is `../docs_checkpoint_devin_01/DOCS_VALIDATION.json`. Remaining scientific work comprises exact runtime diagnosis, disposition of eight unverified cells, paired seed-18/full-Debiased evidence and training-seed uncertainty. No completed CPU-lane worker needs resumption.
