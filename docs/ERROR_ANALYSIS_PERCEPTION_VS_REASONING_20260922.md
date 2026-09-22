# Why distillation gains little: perception, reasoning or format (2026-09-22 05:35Z)

**Answer.** Format explains most of the apparent gain, perception explains most of what is left, and the base is not the limit. Under the reviewed lenient parser the OneThinker student gains 3.16 points on VSIBench and loses 1.81 on VSTIBench; the Qwen student gains 20.2 and 10.8 over a terminating base, but a maximally permissive reading of that base's prose cuts those to +9.2 and -0.5. Where the student states its own measurements its arithmetic is sound — the answer follows from its own observations on 82 percent (OneThinker VSIBench) to 88 percent (Qwen VSIBench) of derivable items — yet the measurements are wrong: a stated count, distance, size or room area misses by 25 to 44 percent at the median, against an MRA metric that pays nothing past 50 percent. Distillation transferred a format and a termination habit, plus answer priors on the families whose targets state no derivation rule at all (53 percent of VSIBench items and 78 percent of VSTIBench items yield observations from which no answer can be recomputed). The base is not too weak: its own numeric estimates are as accurate as the student's (OneThinker VSIBench median relative error 39/50/26/26 percent against the student's 39/33/27/29); it wrapped them in `<1.7>` instead of `1.7`. Student errors concentrate where the base also fails (54 to 77 percent), so the ceiling is shared perception, not a weak starting model.

## 1. Headline, official aggregation (`out/DELTAS.txt`; reproduces every handoff §1 number)

| pair | base strict | base lenient | base recovered-bound | student | delta lenient | delta vs bound |
|---|--:|--:|--:|--:|--:|--:|
| OneThinker VSIBench | 31.47 | 39.19 | 39.44 | 42.35 | **+3.16** | +2.91 |
| OneThinker VSTIBench | 40.16 | 45.40 | 45.53 | 43.59 | **-1.81** | -1.95 |
| Qwen VSIBench, thinking-off base | 29.09 | 29.09 | 40.05 | 49.25 | **+20.16** | +9.20 |
| Qwen VSTIBench, thinking-off base | 35.80 | 35.80 | 47.01 | 46.56 | **+10.76** | -0.45 |
| Qwen VSIBench, fixed-protocol base | 15.47 | 15.47 | 23.18 | 49.25 | +33.77 | +26.07 |
| Qwen VSTIBench, fixed-protocol base | 28.59 | 28.59 | 32.84 | 46.56 | +17.97 | +13.72 |

Lenient = harness parser `bdd490c`; recovered-bound = one unambiguous letter or number in the last three lines, my rule, a bound and not a score.

**A. Format-only failures** (`out/TABLES.txt` §A). The lenient parser recovers 84 of OneThinker's 93 VSIBench strict failures and 41 of 55 on VSTIBench; 52 and 27 of them then score credit, concentrated in room size (23 of 26), absolute distance (20 of 34) and camera-object distance (26 of 34). It recovers none of Qwen's, whose failures are prose; my permissive rule salvages 150 of 160 and 106 of 107. Students fail to parse 0 to 4 times per cell.

## 2. B. Perception: the stated estimate against ground truth (`out/TABLES.txt` §B)

| cell / type | student median rel. err | within 50% | base median rel. err | within 50% | student gave no estimate |
|---|--:|--:|--:|--:|--:|
| OT VSI counting | 33% | 78% | 50% | 62% | 0 |
| OT VSI absolute distance | 39% | 60% | 39% | 62% | 0 |
| OT VSI object size | 27% | 74% | 26% | 76% | 0 |
| OT VSI room size | 29% | 54% | 26% | 82% | 13 of 50 |
| OT VSTI camera displacement | 62% | 36% | 72% | 36% | 0 |
| OT VSTI camera-object distance | 29% | 68% | 40% | 74% | 0 |
| QW VSI counting / room size | 25% / 14% | 92% / 96% | 40% / 43% | 66% / 58% | 0 / 0 |
| QW VSI abs distance / size | 40% / 34% | 58% / 64% | 50% / 33% | 50% / 56% | 0 / 1 |
| QW VSTI displacement / cam-obj dist | 69% / 44% | 42% / 60% | 82% / 34% | 34% / 70% | 0 / 1 |

Counting improves for both students and room size for Qwen only; distance and size do not improve at all, and OneThinker's room-size perception gets worse.

## 3. C. Does the answer follow from the student's own observations (`out/TABLES.txt` §C)

| cell | derivable | answer follows | perception wrong, reasoning right | perception right, reasoning wrong | both wrong | no observations |
|---|--:|--:|--:|--:|--:|--:|
| OneThinker VSIBench | 237/500 | 195 (82%) | 55 | 12 | 30 | 263 |
| OneThinker VSTIBench | 100/450 | 71 (71%) | 31 | 12 | 17 | 350 |
| Qwen VSIBench | 233/500 | 204 (88%) | 45 | 12 | 17 | 267 |
| Qwen VSTIBench | 99/450 | 67 (68%) | 35 | 19 | 13 | 351 |

Every relative-direction, appearance-order, route-planning, camera-movement and object-object item falls in "no observations": the target states no rule mapping its scalar to an option, so the student emits a number and then a letter. Reasoning-wrong cases concentrate in room size (7 of OneThinker VSIBench's 12) and Qwen's camera-object distance (19 of 19).

## 4. D. Where the student wins and loses under lenient credit (`out/DELTAS.txt`)

OneThinker VSIBench's +3.16 splits into +1.58 from derivation-backed tasks (counting +1.50, relative distance +0.75, absolute distance +0.50, size +0.50, room size **-1.68**) and +1.58 from tasks with no derivation rule (direction +0.83, appearance order +0.50, route +0.25) — priors, not reasoning. OneThinker VSTIBench's -1.81 is +0.72 derivation-backed (camera-object distance +1.88, displacement -1.16) against -4.27 from the object-object families, which the teacher pool never covers and whose left/right convention is object-centred while VSTIBench's is camera-centred. Qwen VSIBench's +20.16 is +15.33 derivation-backed (room size +6.70, counting +3.48) plus +4.83 priors; Qwen VSTIBench's +10.76 is mostly object-object priors (+5.87), which the recovered bound erases.

## 5. Ten cited examples (`out/GISTS.txt`)

| qid | type | GT | base output | student output | classification |
|---|---|---|---|---|---|
| 1753 | VSI abs distance | 2.4 | `<1.7>` | frame lists, "numerical result" → 4.0 | base format-only; student perception wrong |
| 99 | VSI counting | 6 | `<3>` | roster "chair A, chair B" → 2 | base format-only; perception wrong, reasoning right |
| 2685 | VSI room size | 41.4 | `<answer>35.0</answer>` | "magnitude approximately 3.0000000000000004" → 83 | perception right, reasoning wrong |
| 1405 | VSI rel distance | D | `<answer>C</answer>` | four closest-point distances → B | perception wrong, reasoning right |
| 1244 | VSI direction easy | A | `<answer>B</answer>` | centres, cross product, no rule → A | student right with no derivation (prior) |
| 5166 | VSTI obj-obj lr | B | `<answer>B</answer>` | centres, cross product, no rule → A | student loses; no derivation |
| 1819 | VSTI cam-obj dist | 1.8 | `<1.5>` | frame lists only → 2.99 | base format-only; student perception wrong |
| 5835 | VSTI displacement | 3.3 | `<answer>2.0</answer>` | two identical camera frame lists → 1.0 | perception wrong, reasoning right |
| 534 | QW VSI room size | 23.6 | prose, then "the final answer is: A" | spans → 17 | base format failure on a numeric item |
| 5026 | QW VSTI obj-obj lr | B | `A` (4 tokens) | centres, no rule → B | student right with no derivation (prior) |

## 6. E. Is the base the limit (`out/TABLES.txt` §E, lenient credit > 0 counts as right)

| cell | base right, student right | base right, student wrong | base wrong, student right | both wrong | student errors the base also fails |
|---|--:|--:|--:|--:|--:|
| OneThinker VSIBench | 173 | 75 | 90 | 162 | 68% |
| OneThinker VSTIBench | 185 | 95 | 59 | 111 | 54% |
| Qwen VSIBench | 132 | 47 | 162 | 159 | 77% |
| Qwen VSTIBench | 156 | 54 | 118 | 122 | 69% |

Distillation loses 75 to 95 items the OneThinker base answers correctly — a real cost, not noise.

## 7. Provenance

Cells, read once each and read-only: `$E/{vsibench_answerable500,vstibench_repr450_v2}/{onethinker,onethinker_armc,qwen35,qwen35_base_nothink,qwen35_c_r1}/runs/<variant>/generations.jsonl`, with `$E = /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_e3e9ffb/artifacts/paper_eval`. Labels: `$E/<bench>/prepared/scoring/labels.jsonl`. Parsers: `student_pilot/benchmark_eval/answers.py` at `bdd490c` (clone `P/claude_parser_sensitivity/work/harness`). MRA replicates `/home/jjyeung/agent_project/agent/evaluation/scoring.py` (sha256 `f67703ea…`); recomputed strict credit equals the recorded `per_question_scores.jsonl` credit on all 4,750 items, and the official aggregations reproduce 31.47 / 42.35 / 40.16 / 43.59 / 29.09 / 49.25 / 35.80 / 46.56 / 15.47 / 28.59. Derivation rules from `student/compact_targets/compact_counted_v1.py` (repo `26f698f`). Scripts and extracts: `out/` here (`analyze.py`, `aggregate.py`, `deltas.py`, `gists.py`, `survey_templates.py`, `extracts/*.jsonl`, `TABLES.txt`, `DELTAS.txt`, `GISTS.txt`, `PICKS.txt`).

## 8. Direct-answer base control (added 2026-09-22; `out/DIRECT.txt`, `out/extracts/*_qw_direct.jsonl`)

Both legs scored with the same parsers as everything above: harness lenient `bdd490c`, then the permissive bound (one unambiguous letter or number in the last three lines). Recomputed strict reproduces the lane's receipts exactly (VSIBench 17.61 against `summary_basectl_vsi.txt` 0.176083, VSTIBench 31.47 against `summary_basectl_vsti.txt` 0.314667).

| benchmark / cell | strict | lenient | permissive bound | strict parse failures | bound recovers | capped |
|---|--:|--:|--:|--:|--:|--:|
| VSI direct-answer base | 17.61 | 17.61 | 23.68 | 359 | 140 | 360 |
| VSI thinking-off base | 29.09 | 29.09 | 40.05 | 160 | 150 | 4 |
| VSI fixed-protocol base | 15.47 | 15.47 | 23.18 | 378 | 139 | 373 |
| VSI arm C student | 49.25 | 49.25 | 49.25 | 0 | 0 | 0 |
| VSTI direct-answer base | 31.47 | 31.47 | 35.91 | 187 | 93 | 187 |
| VSTI thinking-off base | 35.80 | 35.80 | 47.01 | 107 | 106 | 0 |
| VSTI fixed-protocol base | 28.59 | 28.59 | 32.84 | 205 | 96 | 205 |
| VSTI arm C student | 46.56 | 46.56 | 46.56 | 0 | 0 | 0 |

The lenient parser moves neither leg (Qwen never decorates an answer; its failures are truncations), and the permissive bound lifts the direct-answer control only 6.1 and 4.4 points, against 11.0 and 11.2 for the thinking-off control. The direct-answer prompt therefore gives the Qwen base the *less* fair reading of the two: it still fails to terminate on 360 of 500 VSIBench and 187 of 450 VSTIBench items, so most of its lost credit is an unfinished generation that no parser can recover, whereas the thinking-off control finishes every item and its remaining failures are answers a reader would accept. The thinking-off control stays the base of record for section 1; the direct-answer leg adds a per-type row (`out/DIRECT.txt`) and confirms that instructing the base to answer directly, without switching thinking off, does not fix termination.
