# Call-rate reader report

The reader passes 56 unit tests, 190 reproduction checks, and 31 checks against the independent reviewer’s saved probes. All original reproduction checks remain enabled. Camera, distance and room36 primary scores and bootstrap intervals match `score_r5.py` outputs.

Archive: `sb_callrate.tar`  
SHA-256: `ba53f02503ec38b437a398f60b97f49e02c2d0ab2ac2e9dd29bcf4c75694c043`

The archive contains code, tests, documentation and the example strata mapping. It excludes returns and test fixtures.

## Commands and validation

These commands ran on trinity-1-18 with CPU only, no network and one BLAS/OpenMP thread. The reader commands recorded in the reproduction and review JSON files produce every metric below.

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -B -m unittest discover -s tests -v > out/unit_tests.txt 2>&1
python -B reproduce.py --input-root in --out out > out/reproduction_tests.txt 2>&1
python -B review_probes.py --review-root /scratch/jjyeung/orch_n30/sb_crrev/scratch/rob --out out/review_probes > out/review_probes.txt 2>&1
python -B build_delivery.py
```

The reproduction command invokes:

```bash
/data2/jjyeung/envs/planner/bin/python -B /scratch/jjyeung/orch_n30/sb_callrate/callrate.py --input-root in --a in/cont_ops/work/r1route/out3/A4/ret --a-step 200 --out out/step200 --summary
/data2/jjyeung/envs/planner/bin/python -B /scratch/jjyeung/orch_n30/sb_callrate/callrate.py --input-root in --a in/cont_ops/work/r1route/out3/B5/ret --a-step 200 --out out/room134 --summary
/data2/jjyeung/envs/planner/bin/python -B /scratch/jjyeung/orch_n30/sb_callrate/make_strata_example.py --input out/step200/callrate.json --out /scratch/jjyeung/orch_n30/sb_callrate/examples/devs1_wording_strata.json
/data2/jjyeung/envs/planner/bin/python -B /scratch/jjyeung/orch_n30/sb_callrate/callrate.py --input-root in --a in/cont_ops/work/r1route/out3/A4/ret --a-step 200 --out out/strata_example --summary --strata /scratch/jjyeung/orch_n30/sb_callrate/examples/devs1_wording_strata.json
```

[Unit-test log](unit_tests.txt) · [reproduction checks and hashes](reproduction.json) · [review probe checks and hashes](review_probes/review_probes.json)

## Reproduction table

A is step 200; B is registered step 544. Camera/distance and A4 room rows come from the first reader command; B5 room rows come from the second. Scores use package overrides when supplied. Deltas use percentage points.

| Population / source reads A vs B | n/expected A / B | Calls A/B | Capped A/B | Score A | Score B | Score delta, 95% CI (pp) |
|---|---:|---:|---:|---:|---:|---|
| Camera displacement: A4/read 0 vs b1/read 0 | 150/150 / 150/150 | 150/150 | 0/0 | 0.818666667 | 0.823333333 | -0.466667 [-1.006711, -0.000000] |
| Camera rotation: A4/read 0 vs b1/read 0 | 150/150 / 150/150 | 150/150 | 0/0 | 0.762666667 | 0.756000000 | 0.666667 [-0.365898, 1.687520] |
| Camera direction: A4/read 0 vs b1/read 0 | 150/150 / 150/150 | 150/150 | 0/0 | 0.946666667 | 0.946666667 | 0.000000 [0.000000, 0.000000] |
| Distance: A4/read 0 vs b1/read 1 | 150/150 / 150/150 | 88/149 | 0/0 | 0.502666667 | 0.282666667 | 22.000000 [13.149333, 29.609958] |
| Room36 primary: A4/read 0 vs b1/read 0 | 36/36 / 36/36 | 0/36 | 0/29 | 0.669444444 | 0.116666667 | 55.277778 [38.823529, 70.385417] |
| Room36 secondary: A4/read 0 vs b2/read 0 | 36/36 / 36/36 | 0/36 | 0/27 | 0.669444444 | 0.111111111 | 55.833333 [39.499342, 70.500000] |
| Room134: B5/read 0 vs b2/read 0 | 134/134 / 134/134 | 0/134 | 0/115 | 0.644029851 | 0.065671642 | 57.835821 [50.746269, 64.676259] |

Room36 uses b1/read 0 because A4 is the registered five-type read. The b2/read 0 comparison is secondary. The room36 and room134 populations overlap and must not be added.

## Metric definitions and missing values

- Call rate counts recorded calls of the item type, including unserved calls. Capped rate counts `max_calls`, `max_new_tokens` and `length` over all compared items.
- Usage means the answer follows the response: `follow_converted + copied_unconverted`. Category rates divide by items with parsed responses; a missing answer is `other`. Converted agreement takes precedence at zero, where copying and conversion cannot be distinguished.
- `conversion_failure` counts unconverted copies among response-eligible questions requiring a unit conversion. Room area uses squared units; camera displacement uses length units.
- Answer rate counts finite values parsed by the type scorer or listed options. `not_seen` and `other_non_numeric` have separate rates over compared items. `max_calls` suppresses answers.
- Scores preserve package accuracy and supplied `scores.answer` overrides. Numeric-task scores are MRA. MRA includes unanswered/capped items and is not answer rate.
- Marginals and deltas use shared completed IDs. Paired usage additionally requires response eligibility on both sides. Intervals retain the seed-17, 10,000-draw physical-room bootstrap.
- Missing responses make usage `MISSING`; room usage is MISSING in these reads. Population membership uses explicit manifest tags or identity-checked joins. Unknown membership is never guessed.

## Room populations and RESULT summary

The second reader command yields these room MRAs. The explicit manifest contains 36 dev-S1 and 98 R0-dev items. The A4 dev-S1 population is separately labelled in the primary table and summary.

| Population / source reads A vs B | n/expected A / B | MRA A (%) | MRA B (%) | Delta, 95% CI (pp) |
|---|---:|---:|---:|---|
| dev-S1: B5/read 0 vs b2/read 0 | 36/36 / 36/36 | 68.89 | 11.11 | 57.78 [39.41, 74.12] |
| R0-dev: B5/read 0 vs b2/read 0 | 98/98 / 98/98 | 62.76 | 4.90 | 57.86 [50.82, 64.69] |
| all: B5/read 0 vs b2/read 0 | 134/134 / 134/134 | 64.40 | 6.57 | 57.84 [50.75, 64.68] |

[A4 table](step200/callrate.txt) · [A4 summary](step200/callrate.summary.txt) · [A4 JSON](step200/callrate.json) · [Room134 table](room134/callrate.txt) · [Room134 JSON](room134/callrate.json)

## Review fixes

The review-probe command above reruns the supplied t2/t3/t4 cases with outputs confined to this workspace. The review fixtures remain read-only.

- **Partial summaries:** t2 refuses with exit 2, empty stdout and one stderr line. With `--allow-partial --allow-subset`, it prints PARTIAL, distance 100/150 and room 20/36, and computes both sides on those shared IDs.
- **Mismatched populations:** t4 refuses without `--allow-subset`. With it, the room row prints original planned sizes A=36, B=134 and compares only the 36 shared IDs; both marginals use that set.
- **Symlink relocation:** t3 reproduces the reference metrics with the default original root. Existing targets are retained even when a stale relocated target exists. Only missing targets under the original root relocate.
- **Authentication and resumes:** wrong steps, bindings, packages, duplicate rows, uncommitted tails and started segments without journals still refuse. The legitimate two-segment resume matches the complete read.
- **Test isolation:** fixtures use temporary directories under `scratch/tests`; path assertions derive from temporary paths or stable suffixes.

The first reproduction reader command produces the response-following and answer results below:

| Distance metric | A4/read 0 (step 200) | b1/read 1 (step 544) |
|---|---:|---:|
| Usage | 85/85 (100.00%) | 142/142 (100.00%) |
| Follow converted | 73/85 (85.88%) | 72/142 (50.70%) |
| Copied unconverted | 12/85 (14.12%) | 70/142 (49.30%) |
| Other | 0/85 (0.00%) | 0/142 (0.00%) |
| Conversion failure | 12/50 (24.00%) | 70/100 (70.00%) |
| Parseable answer | 150/150 (100.00%) | 147/150 (98.00%) |
| Not seen | 0/150 (0.00%) | 3/150 (2.00%) |
| Other non-numeric | 0/150 (0.00%) | 0/150 (0.00%) |

Room36 primary reproduces B=0.116667, capped 29/36, and delta 55.28 [38.82, 70.39]. Its labelled secondary b2/read 0 comparison gives delta 55.83 [39.50, 70.50].

**External strata:** `--strata FILE` adds per-stratum and per-stratum-by-unit call rates and score/MRA to the table and summary. The example generator command freezes the existing dev-S1 A4 trace tags for 150 distance IDs into 19 labels. The reproduction checks confirm that these rows partition the same items and leave per-item measurements unchanged.

The example labels describe generated traces, not question-wording effects or HELDOUT/TRAIN_DEV/R0_REWORDED membership. No dist_diag split is inferred. Supply its explicit ID mapping when available. Units must match questions, and missing labels within a represented type say MISSING and exit 2.

[Example mapping](../examples/devs1_wording_strata.json) · [stratified table](strata_example/callrate.txt) · [stratified summary](strata_example/callrate.summary.txt)

The README documents the schema, denominators, opt-in flags and step-400/600 commands. Real step-400/600 metrics require those returns; synthetic tests cover their CLI behavior.

[Delivery validation](delivery_validation.json) records input hashes, archive contents, checks and this report’s hash.
