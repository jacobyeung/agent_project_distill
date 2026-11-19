# Routed-return call rates
Requires Python 3.10+, NumPy and SciPy already installed; CPU only, no network.
Run from this directory. Returns and packages remain read-only; bytecode is disabled.
`callrate.py` writes `callrate.json` and `callrate.txt` under `--out`.
It also prints JSON to stdout and the table to stderr. Failure exits with code 2.
`--summary` instead prints only a compact RESULT table to stdout and saves it as
`callrate.summary.txt`; the full JSON and text files are still written.
Every JSON includes input and code SHA-256 hashes. Missing values say `MISSING`.

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
`src/` supplies the manifest, `9.json`, and scorers; `--scorer-src` can select it explicitly.
`--a-read`/`--b-read` select a read (default 0); manifest overrides are authenticated.
Without `--b`, B is registered step 544: b1/read 0 cameras, b1/read 1 distance,
and b2/read 0 rooms, restricted to A's planned IDs. Unregistered IDs fail loudly.
`--input-root` relocates the copied tree; `--original-root` relocates absolute symlinks.
The default input tree is `./in`; no input symlinks are changed.

Calls use recorded type-specific routes, including unserved calls. Capped means
`finish` is `max_calls`, `max_new_tokens`, or `length`, exactly as `score_r5.py`.
Usage requires a parsed response decision; missing answers then count as failures.
It uses the scorer's 5% tolerance, exact zero, unit conversion, and direction argmax.
Room area uses the package's room-response parser and squared unit conversion.
Unknown types use package/item routing evidence; absent routes/parsers say `MISSING`.
Rates use completed items; missing expected IDs are listed and exit with code 2.
Distance wording uses overlapping `classify.py` trace tags; other strata mask questions.
Paired usage uses joint eligibility; paired wording uses shared stratum membership.
Bootstrap intervals use physical rooms, seed 17, 10,000 draws, and A minus B in pp.

The summary contains per-type call rate, capped rate, usage, answer rate, score A/B
and paired score delta; distance call rates by unit; and room answer MRA by population.
Summary rates and scores are percentages; JSON rates and MRA remain on [0,1].
`room_mra` reports `all`, `dev-S1`, and `R0-dev`, each with A/B completed `n`,
expected counts, `mra_answer`, and paired delta with 95% and 99.29% room intervals.
MRA averages every completed item, including unanswered items; it is not answer rate.
Population uses explicit manifest `sets`, `population`, `r0_split`, or `split` tags.
Untagged items join by ID and matching question, truth, type, room, and options to
the other side or `--baseline-root/b2/src/items/room134.json`. Every input is hashed.
Unknown membership produces a `MISSING` group, exact unresolved IDs and expected
manifest path in JSON, and exit 2. Dataset names and ID prefixes never assign splits.
The supplied room134 manifests explicitly identify 36 dev-S1 and 98 R0-dev items;
the scene-list fallback is unnecessary. Empty populations report n=0 and MISSING MRA.

```bash
python -B -m unittest discover -s tests -v
python -B reproduce.py --input-root in --out out
```
