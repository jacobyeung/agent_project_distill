# review_r1p6 removal candidates (13 GB; above the 1.5 GB lane cap)
The cap breach comes from test fixtures: each test_fix10 full-store build writes about 1.7 GB of rows.sqlite, and each pre_submit test writes about 0.5 GB. /scratch still has 441 GB free.
- /scratch/jjyeung/orch_n30/review_r1p6/work/snap_fac07052 (1.8G), work/snap_0647a0df (1.6G): copies from the first test run, which I aborted
- /scratch/jjyeung/orch_n30/review_r1p6/work/t2_snap_fac07052 (4.5G), work/t2_snap_0647a0df (4.5G): copies from the second test run, which passed
- work/A, A0, B, B0, fc (about 60 MB): extracted packets and fail-closed fixtures
All of these can be removed once the proof has run. Logs and scripts are in work/*.py, work/*.log and work/my_offenders.json, under 1 MB.
