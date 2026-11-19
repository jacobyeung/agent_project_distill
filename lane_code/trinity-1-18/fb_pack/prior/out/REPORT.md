# Vehicle N hard-direction prior

**BLOCKED at task step 3.** The sealed loader cannot express selective row weights or repeats. No tree or launch config changed. `PRIOR_DELTA.json` is an explicit non-runnable proposal; native before/after draws are `MISSING`.

Tree seal: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`. The native sampler refuses N’s actual binding with `R1_COMPLETE_FILTERED_POPULATION_REQUIRED`. The bound population has `complete=false`, `after_all_filters=false`, and zero counts.

Commands (run from this workspace; all numerical tables come from these scripts):
```bash
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python census_source.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python loader_boundary.py
nice -n 10 python analyze_prior.py
python manual_review.py
nice -n 10 python finalize.py
```

The source scan authenticated 204,413 v7 rows and 7,971 twins. All 12 launch removal lists apply, including n, z, the K1 union, and the 109-row naming list. It removed 23,315 rows; six additional relative-distance rows failed native text checks. Direction retains 98,315 rows: 55,808 in `direction` and 42,507 in `facing_pairs`.

`READ40.md` contains 40 manually checked question/trace/option examples; all agree with the parser. Every hard forward relation also agrees with its clause/answer transform, and every twin preserves its source forward line and applies the expected answer half-turn. Source and code hashes appear in every output JSON.

Row census and expected draws per 1,000 steps (expectations over the native shuffle, **not realized seed-17 loader counts**):

| Clause / difficulty | Rows | Front % | Back % | Expected draws | Draw back % |
|---|---:|---:|---:|---:|---:|
| away / easy | 14,967 | 0.000 | 0.000 | 7,326.791 | 0.000 |
| away / hard | 10,528 | 28.400 | 71.600 | 5,429.534 | 67.873 |
| away / medium | 7,985 | 0.000 | 44.208 | 3,413.260 | 44.208 |
| toward / easy | 19,725 | 0.000 | 0.000 | 11,324.039 | 0.000 |
| toward / hard | 24,862 | 82.596 | 17.404 | 15,407.062 | 17.567 |
| toward / medium | 20,248 | 0.000 | 4.361 | 12,135.314 | 4.447 |

Easy rows are lateral; medium rows also carry lateral relations. `CENSUS.json` includes all answer labels and stated forward relations. The card allocates 36,866 direction draws and 18,170 facing-pair draws, within 128,000 VQA and 288,000 total draws. Other-stream quota feasibility is not newly proven here.

Options keep every row eligible and preserve card-cell quotas. (a)/(b) assign the stated actual draw counts to selected rows and distribute the remaining quota uniformly. (c) and the chosen policy normalize relative weights within each cell. These are analytical expectations; a finite sampler must enforce the hard cap.

| Option | Toward-hard back % | Away-hard back % | Total draws |
|---|---:|---:|---:|
| Before | 17.567 | 67.873 | 288,000 |
| (a) Behind rows: four actual draws | 66.981 | 70.480 | 288,000 |
| (b) 2,000 source rows: two actual draws | 30.889 | 68.557 | 288,000 |
| 2,000 source rows: four actual draws | 46.375 | 69.682 | 288,000 |
| (a)+(b), capped at 4 | 66.981 | 70.480 | 288,000 |
| (c) Down-weight front to balance | 50.000 | 66.175 | 288,000 |
| Chosen: balanced, same toward-hard mass | 50.000 | 67.873 | 288,000 |

For the chosen option, back/front weights are `direction`: `10251/3676` / `10251/16826`; `facing_pairs`: `2180/651` / `2180/3709`. Other rows retain weight 1. Each cell’s toward-hard mass stays constant, so every other clause/difficulty draw total and answer share stays unchanged. The target is 50%, independent of dev truth shares.
The largest modeled direction-row expected draw count is 1.842130, below four. This is not a realized-cap proof. `CENSUS.json` lists every option’s effects on all six clause/difficulty groups and every card cell. (a)+(b) cannot add copies beyond four: the 2,000 sources are a subset of (a).

Drawing the 2,000 sources twice means two actual draws per source, not multiplying their baseline expected dose by two. This distinction supports the analyst’s roughly 30% estimate. The quoted 71.8% away-hard share precedes removals and ignores the two cell draw rates.

Exact ceiling and selection code:

- `student_pilot/r1_mix.py:27`: `totals = {k: min(n, 4*counts[k]) for k, n in requested.items()}`.
- `student_pilot/r1_loader.py:92-93`: `if max(repeats.values(), default=0) > 4:` then `raise ValueError('R1_REPEAT_LIMIT_EXCEEDED')`.
- `r1_mix.py:76-79` rejects duplicate population offsets; `83-84` requires full coverage. `81-82` shuffles once, and `96` selects `pool[consumed[kind] % len(pool)]`. No per-row weight is read.

The smallest sampler change is an authenticated finite per-cell draw schedule in `r1_mix.py:68-86,95-97`, with unchanged eligible indices, exact cell quotas, and a per-row cap of four. Normal preparation also needs to bind it at `r1_population.py:148-156`. `PRIOR_DELTA.json` identifies those edits; none were applied.

The loader audit omits `facing_pairs` and its clause parser disagrees on 23,121 source rows. Fix `r1_loader.py:55-70,101-105` and `r1_direction_twins.py:136-143` before reporting a balanced result.

`MISSING`: complete `w24/work/build24/inputs/population.json` and matching `indices.json` (the supplied files are placeholders), plus production `.../ap/8865619b/f/469ddece/receipt.json`. Exact absolute paths appear in `PRIOR_DELTA.json`. No mappings, manifests, scene lists, or production proofs were invented.

Artifacts: `CENSUS.json`, `PRIOR_DELTA.json`, `READ40.md`, source evidence, scripts, and input hashes are packaged by `python package_outputs.py` into `fbp_prior.tar`; `fbp_prior.tar.sha256` records its digest.
