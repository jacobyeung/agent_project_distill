# Routed-return call rates

Requires Python 3.10+, NumPy and SciPy already installed; CPU only, no network.
Run from this directory. Returns and packages remain read-only; bytecode is disabled.
`callrate.py` writes `callrate.json` and `callrate.txt` under `--out`, prints JSON to
stdout and the table to stderr. Every result JSON records input/code SHA-256 hashes.
Missing values say `MISSING`; invalid or missing inputs exit 2.
`--summary` prints a table to stdout and saves `callrate.summary.txt`.

For new returns, set these paths to the actual local return/package directories:

```bash
export RETURN400=/scratch/jjyeung/step400/ret PACKAGE400=/scratch/jjyeung/step400
export RETURN600=/scratch/jjyeung/step600/ret PACKAGE600=/scratch/jjyeung/step600
export BASES="$PWD/in/cont_ops/work/r1route/out3/bases"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -B callrate.py --a "$RETURN400" --a-step 400 --a-package "$PACKAGE400" --baseline-root "$BASES" --out out/step400 --summary
python -B callrate.py --a "$RETURN600" --a-step 600 --a-package "$PACKAGE600" --baseline-root "$BASES" --out out/step600 --summary
python -B callrate.py --a "$RETURN400" --a-step 400 --a-package "$PACKAGE400" --b "$RETURN600" --b-step 600 --b-package "$PACKAGE600" --baseline-root "$BASES" --out out/400_vs_600 --summary
```

Each package needs `READ_PLAN.json`, `tower_sequence.py`, `package/0.json`, and `src/`.
`src/` supplies the manifest, `9.json`, and scorers; `--scorer-src` selects the common
scorer explicitly. Both sides use that scorer, including its score overrides.
`--a-read`/`--b-read` select a read (default 0); manifest overrides are authenticated.
Without `--b`, B is registered step 544: b1/read 0 cameras and b1/read 1 distance.
For A4-style five-type reads, rooms use b1/read 0, as in `score_r5.py`; a labelled
secondary room36 row uses b2/read 0. Room-only reads use b2/read 0. Default B is
restricted to A's planned IDs; unregistered IDs fail loudly. Room population rows
name their source return/read, distinguishing A4/read 0 from B5/read 0.
`--input-root` selects the copied tree. Links resolve to their existing targets.
Only missing targets under `--original-root` relocate under `--input-root`.
No symlink is modified. The default input tree is `./in`.

## Coverage and pairing

Every summary/table metric row shows `n/expected A / B`. `n` is the shared completed
population; `expected` is the shared planned population. JSON `coverage` preserves
each side's original completed/expected counts, and `set_sizes` preserves both sets.
Incomplete coverage prints a `PARTIAL` banner. With `--summary`, incomplete inputs
without `--allow-partial` produce no stdout, a one-line reason on stderr, and exit 2.
`--allow-partial` permits a labelled partial result and exit 0.

Different planned or completed A/B ID sets refuse unless `--allow-subset` is given.
That flag prints original planned/completed sizes for both sides and computes all
marginals and deltas on shared completed IDs. Types with no shared IDs say `MISSING`.
Use both `--allow-partial --allow-subset` when an incomplete return has fewer
completed IDs than its partner. The flags do not waive authentication checks.

## Metrics

- Calls count recorded type-specific routes, including unserved calls. Capped means
  `finish` is `max_calls`, `max_new_tokens`, or `length`, as in `score_r5.py`.
- Response categories use the last parsed matching response and the scorer's 5%
  relative tolerance (exact zero). `follow_converted` matches the requested-unit
  value; `copied_unconverted` matches the printed metre value while another unit is
  requested; `other` matches neither. Usage is their first two categories summed:
  **the answer follows the response**. Categories are exclusive; converted agreement
  takes precedence at zero because copying cannot be distinguished there.
- Category rates and usage divide by response-eligible items. Missing answers are
  `other`; absent/unparsed responses make usage and categories `MISSING`.
  `conversion_failure` reports copied-unconverted answers among eligible items
  requiring conversion. JSON includes counts and denominators for every rate.
  Camera displacement uses the same categories; room area uses squared conversion.
  Rotation and option questions use `follow_converted` for response agreement.
- Answer rate requires a finite value parsed by the type's scorer or a listed option.
  `not_seen` and `other_non_numeric` are separate rates over completed items; JSON
  `non_numeric` combines them. Empty answers are neither. `max_calls` suppresses answers.
- Score preserves `h1eval.scorers.accuracy`, including `scores.answer` overrides.
  Numeric tasks report MRA; option tasks report accuracy. Room MRA averages all
  compared items, including unanswered/capped items; it is not answer rate.
- Paired usage uses joint response eligibility. Physical-room bootstrap intervals
  use seed 17, 10,000 draws, A minus B in percentage points, and 95%/99.29% intervals.
  Summary rates/scores are percentages; JSON rates/scores remain on [0,1].

Room populations use explicit manifest `sets`, `population`, `r0_split`, or `split`.
Untagged items join by ID and exact question/truth/type/room/options to the other
side or `--baseline-root/b2/src/items/room134.json`. Unknown membership says `MISSING`,
reports unresolved IDs and the expected manifest path, and exits 2. No split is guessed.

## External wording strata

`--strata FILE` accepts an item-ID mapping with a stratum label and canonical unit:

```json
{"vsi590k_163095": {"stratum": "HELDOUT", "unit": "ft"}}
```

Units are `m`, `cm`, `mm`, `ft`, `in`, or `N/A`; room units denote square units.
Units must match the question. Provide all IDs for each represented type; omitted
IDs within that type form a `MISSING` stratum and exit 2. Other types need no labels.
The table and summary add per-stratum and per-stratum-by-unit call rates, score/MRA,
coverage and paired deltas. Membership is fixed across A/B. Unused IDs are listed in
JSON; a file with no matching IDs refuses. `_meta` may hold provenance metadata.

`examples/devs1_wording_strata.json` freezes the existing A4 dev-S1 distance trace
wording tags. Its `TRACE_A4:` labels join overlapping tags into one label per item.
They describe generated traces, **not question-wording or held-out/training effects**.
The built-in `by_wording` groups are also trace diagnostics. Replace the example
with dist_diag's explicit item labels when available; no HELDOUT/TRAIN_DEV/R0_REWORDED
membership is inferred. The example records its command and source hashes.

```bash
python -B make_strata_example.py --input out/step200/callrate.json --out examples/devs1_wording_strata.json
python -B callrate.py --input-root in --a in/cont_ops/work/r1route/out3/A4/ret --a-step 200 --out out/strata_example --summary --strata examples/devs1_wording_strata.json
python -B -m unittest discover -s tests -v
python -B reproduce.py --input-root in --out out
python -B review_probes.py --review-root /path/to/sb_crrev/scratch/rob --out out/review_probes
python -B build_delivery.py
```

`reproduce.py` also builds and checks the strata example. Tests use temporary
fixture directories under `scratch/tests`, with no fixtures written into `tests/`.
The archive contains code, tests, documentation and the example mapping, without returns.
