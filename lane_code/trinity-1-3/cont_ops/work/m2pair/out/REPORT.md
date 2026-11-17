`m2pair.py` compares checkpoint B minus checkpoint A using the production package’s
`h1eval.runner.measure`, `statistics.scalar_metrics`, and per-side room bootstrap.
All 10 CPU tests passed. Checkpoint B has not arrived; the saved comparison uses A twice.

Run from `/scratch/jjyeung/orch_n30/cont_ops/work/m2pair/`:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B out/m2pair.py \
  --a in/result.tar.gz --b in/B-result.tar.gz \
  --output out/B_minus_A.json --md out/B_minus_A.md

/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest discover -s out/tests -v
```

Inputs may be return tars, extracted return directories, journal roots, or scored
`items.jsonl` files/directories that retain complete raw outputs. Archives are streamed
without extraction. Existing measurements are recomputed. Inputs must reside in this
workspace; outputs must reside under `out/`. The read-only package dependency is
`/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/out/production/`.

The comparison uses arm `own`: baseline M1 call rate, exact route, and answer before
first call; baseline M2 call error/correctness and task accuracy; and M3 follow/stick
for each standard camera perturbation. JSON retains per-call measurements for both
checkpoints, per-side values and intervals, counts, paired differences, and source hashes.
Markdown provides one compact table per type.

The paired bootstrap uses the package’s sorted rooms, NumPy RNG, 200-draw batches,
10,000 draws, seed 20261115, and 95% percentiles. Every draw uses the same sampled
rooms for both checkpoints and recomputes their item-weighted means. M2 averages
scored calls within each item; M3 uses each checkpoint’s eligible reads. Missing
scores retain separate denominators. If either mean is undefined on any draw,
the interval and `differs` flag are null, with the undefined-draw count recorded.
Otherwise, `differs` is true exactly when the interval excludes zero.

Verification covered:

- All 1,050 reads paired across 450 items: 150 items per camera type.
- All 23 reported A values, interval endpoints, item counts, and room counts
  exactly matched `in/curve.json`; all A-versus-A differences and intervals were zero.
- A’s M2 values were 0.6049 m displacement error, 17.9000° rotation error, and
  0.7533 direction accuracy. M3 follow was 1.0000 for all perturbation modes.
- Synthetic raw displacement responses increased every baseline absolute error
  by 0.25 m: B−A was 0.25 m with interval [0.25, 0.25], and `differs` was true.
- Unequal item sets refused with per-type counts and missing IDs. Missing modes,
  duplicates, incomplete records, and room mismatches also refused.
- Tar and directory inputs agreed; CLI JSON/Markdown output worked. Complete-pair
  bootstrap results matched the package; separate denominators and undefined draws
  behaved as specified.

Saved self-comparison: [JSON](a_vs_a.json) and [Markdown](a_vs_a.md).
Tests retain their small generated fixtures under `tests/artifacts/`.
