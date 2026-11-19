# Routed-return call rates
Requires Python 3.10+, NumPy and SciPy already installed; CPU only, no network.
Run from this directory. Returns and packages remain read-only; bytecode is disabled.
`callrate.py` writes `callrate.json` and `callrate.txt` under `--out`.
It also prints JSON to stdout and the table to stderr. Failure exits with code 2.
Every JSON includes input and code SHA-256 hashes. Missing values say `MISSING`.

For new returns, set these paths to the actual local return/package directories:
```bash
export RETURN400=/scratch/jjyeung/step400/ret PACKAGE400=/scratch/jjyeung/step400
export RETURN600=/scratch/jjyeung/step600/ret PACKAGE600=/scratch/jjyeung/step600
export BASES="$PWD/in/cont_ops/work/r1route/out3/bases"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -B callrate.py --a "$RETURN400" --a-step 400 --a-package "$PACKAGE400" --baseline-root "$BASES" --out out/step400
python -B callrate.py --a "$RETURN600" --a-step 600 --a-package "$PACKAGE600" --baseline-root "$BASES" --out out/step600
python -B callrate.py --a "$RETURN400" --a-step 400 --a-package "$PACKAGE400" --b "$RETURN600" --b-step 600 --b-package "$PACKAGE600" --baseline-root "$BASES" --out out/400_vs_600
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

```bash
python -B -m unittest discover -s tests -v
python -B reproduce.py --input-root in --out out
```
