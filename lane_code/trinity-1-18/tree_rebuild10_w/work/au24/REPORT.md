Build complete; submission requires the two permitted-root mirrors below. `orchard/` is 197423 bytes.
Exact locations, full SHA256 values, sizes, and P run/tree evidence: `INPUTS.json`; executable pins: `orchard/k.json`.
ROUTE_direct: 3,028,169 bytes, member `947cbb9fa7d6bde0.jsonl.gz` of package `f0e71513…` (161,976,320 bytes); mirror the package to `okh7/u/<full-package-sha>` or the member to `x_22c714e1/u/947cbb9f…`.
Frame inputs: `okh7/x_ee227714/k/frame_map.jsonl.gz` (14,502,816 B), `frame_plan.json.gz` (1,518,048 B), and `x_22c714e1/u/36ae882f…` (47,800 B).
Legacy FPS input: `okh7/l_94a76bda/in/cr/rt_b8b60bcef027.tar`, member `ap/5e1d07a4/f/h/r16/rows.sqlite`: 1,348,722,688 B; all 76,277 rows are required.
Trees: C `x_22c714e1/qd/k/t_e047002134f979bd.tar` → seal `0c7614c8…`; P `x_ee227714/k/t_b83a8a35d420815b.tar` → seal `b83a8a35…`. All three room sources are packed.
Runtime prerequisite: mirror kit archive `/project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar` to `okh7/u/ffc81db4…` (full hash in INPUTS.json); NumPy 2.2.6 comes from P’s pinned `k/np226_5204b3a0.tar`.
Estimated runtime: 5–15 minutes, memory 1–4 GiB (unmeasured at full scale); 45-minute allocation, 64 GiB requested, 15 GiB process address-space cap.
Dry run: actual C code, eight fixtures, eight deferrals across all three steps; JSON and integrity/failure checks passed. Real data, P code, and Orchard runtime staging remain untested; see `VALIDATION.json`.
After the lane copies `orchard/` to `x_22c714e1/au/` and ensures the mirrors exist: `sbatch /project/community/jjyeung/okh7/x_22c714e1/au/au.sh`.
Writes `x_22c714e1/o/<job>/AUDIT_TREE_C.json`, `AUDIT_TREE_P.json`, and `au_0.json`; Slurm logs use `x_22c714e1/j/au_<job>.{log,err}`. Counts persist every 200 rows or five seconds and on handled errors/signals.
