# Build: paired M1/M2/M3 comparison of two H1-evaluator camera reads (checkpoint B minus checkpoint A)

Work only inside `/scratch/jjyeung/orch_n30/cont_ops/work/m2pair/` (write under `out/`). No network, ssh, Slurm, GPU, Git or deletion; no searches outside the paths named here.

## Inputs
- `in/result.tar.gz`, `in/curve.json`, `in/report.md`: the complete camera read of checkpoint A (step 544, Orchard job 170631; 1,050 reads = 450 camera_displacement, 300 camera_rotation, 300 camera_movement_direction over perturbation modes; per-read journals under `metadata/journals/<type>/<gpu>/items.jsonl`). `in/submerge.py`: the script that scored it.
- The evaluator package sources (read only): `/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/out/production/` (production h1eval: measure functions, statistics with room bootstrap 10,000 draws, seed 20261115, 95% interval) and the re-pinned package `/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/out/src` or `out/package/0.tgz` (same scorers, byte-identical).
- Checkpoint B (H1-1 step 100) will arrive later as a return tar of the same format (and optionally its scored `items.jsonl` / `curve.json`).

## Deliver `out/m2pair.py` + tests
`m2pair.py --a <A return tar or extracted dir> --b <B return tar or dir> --output OUT.json [--md OUT.md]`:
1. Reuse the package's own per-read measurement code (import it from the extracted package sources; do not reimplement scoring) to get, per item and arm `own`, mode `none`: M1 (call rate, exact route, answer before first call), M2 per-call errors (displacement |err| m, rotation |err| deg, movement direction correct) and task accuracy; and M3 follow / stick per perturbation mode.
2. Pair items by item id across A and B (refuse if the item sets differ; report counts); compute B minus A for each quantity per type with the package's room bootstrap (paired: resample rooms, recompute both means on the same draw), 10,000 draws, seed 20261115, 95% percentile interval; also each side's own value and interval (must equal the curve.json values for A).
3. Flag "differs" when the paired interval excludes zero.
4. Output JSON + a short markdown table per type: A value, B value, B-A [CI], differs.
Tests (`out/tests/`, run with `/scratch/jjyeung/envs/p1cpu/bin/python`): A vs A gives zero differences and A's per-side values equal `in/curve.json` (M2 displacement 0.605 m, rotation 17.9 deg, direction 0.753; M3 follow 1.000); a synthetic B with shifted displacement errors gives the expected shift; mismatched item sets refuse. `out/REPORT.md`: usage, what was verified. Keep it compact.
