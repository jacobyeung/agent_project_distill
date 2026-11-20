K1-X awaits explicit approval for the heavy raster/geometry pass.
The served-reader factorial CLI is implemented but has not been validated on real captures.
Round-1 outputs and code remain in out/round1/.

| Train reference, 1,037 rows | Target | Saved ladder score | Fresh replay |
|---|---:|---:|---|
| A0_deployed | 56.77 | 56.7695 | NOT RUN |
| A2_gt_masks | 73.97 | 73.9730 | NOT RUN |

Saved scores do not establish raw-geometry parity. The full run requires every per-row prediction and printed box to equal the ladder.
Held-out cross-program differences, all 16 factorial cells, 12 extra rows, C1/C3/C5/C6, the arm-B gate, tower verdicts and readouts are NOT RUN.
The inventory found all primary files for 259 captures (3,676,008,943 bytes). No heavy raster pass ran.
Seven synthetic/source tests pass. Two checks await full parity and factorial outputs; out/TESTS.json records the test result.
The two refused-capture fallbacks use run_tower_sam_2/<key>/tower.npz and own_170235/native/probe/<key>/own.npz, exactly as the ladder reconstruction. Their convert candidates.json files exist.
The CLI freezes run_iso masks on served geometry, retains the reader lift and distance program, and matches GT metric inputs by own_scale/oracle_scale.
The oracle-scale function is copied from E3. The GT endpoint retains served intrinsics and samples GT rasters onto the served 51×51 grid.
Pi3X and DA3 depth exports exist for all 300 captures. The voted-box rule is the ladder frozen vote_10_3_best.
Run after approval: nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py run --heavy-io-approved.
The run uses one CPU process and one numerical thread, local /scratch inputs, and outputs only under r2.
Deviation: execution remains pending because the Trinity Agents rule requires an answer before heavy I/O; elapsed time does not grant approval.
Borderline no-archaeology sentences retained: round-1 archive location, because the user explicitly requires its preservation.
Files: k1x.py, tests/test_k1x.py, vendor/LADDER_COPIES.json, out/INVENTORY.json, out/K1X.json, out/REPORT_R2.md, out/SHA256SUMS.
