The camera-only step-600 A package and five Orchard scripts are ready for review; nothing was submitted.
Stage: `/project/community/jjyeung/okh7/813f42db/c21a600`. The builder selects A only and generates a fresh token.

Run these commands from Trinity with the existing `ossh.sh`; wait at the indicated boundaries:
```bash
timeout 300 bash ossh.sh 'bash -s' < o_build_c600.sh
timeout 300 bash ossh.sh 'bash -s' < o_place_pull_fill_c600.sh
# Wait for fill.log to end with "A filled, dry pass"; fill runs under nohup.
timeout 300 bash ossh.sh 'bash -s' < o_cpu_c600.sh
# Wait for the CPU job to finish successfully and a/c/CPU.json to pass.
timeout 300 bash ossh.sh 'bash -s' < o_sub_c600.sh
# Wait for the read job to finish before fetching.
timeout 300 bash ossh.sh 'bash -s' < o_fetch_c600.sh
```
Walltime: **03:00:00** for the read. Camera times were 1415.772 + 778.560 + 1384.883 = 3579.215 seconds.
Sizing: 1.25 × (3579.215 + 76.592 first-load seconds) + 1800 stop + 1200 return + 3000 startup = 10569.759 seconds, rounded to 10800. The CPU-check allocation remains 04:00:00.

`build_r11.py` changes `a/6.py` COUNTS, SCHEDULE, descriptor types, and all four 636 completion/rehearsal counts to 450; `a/0.json` selects the three camera types.
Payload `9.json` changes only token/export binding; its five-type `order` is the shared type-index registry, not the selected read. The full item manifest stays byte-identical.
`a/4.py` changes its export identity; public descriptors, PACKAGE.json and the embedded batch bundle receive the derived hashes. USR1 handling, serving pins, tower/memo settings and return code stay unchanged.
`gen600c.py` emits the five scripts; `dry2_c600.py` changes only the expected descriptor count and two selection assertions. Its full-manifest 636-item check remains intact; `dryres2.py` is unchanged.
`make_read_plan_c600.py` writes the actual Orchard token, package/operator hashes, 450 selected IDs, counts, sequence and 600 binding to `$S/READ_PLAN_C600.json` during placement. The root copy is bound to the local rehearsal token.

`rehearse_c600.py` rebuilt 400 and 600 from the verified original archive in `rehearsal/k`; the 400 replay matches A10b after token/hash normalization.
`rehearsal/DIFF_A10b_C600.txt` and `MEMBERS.json` cover all 15 delivery, 927 payload and 3 bundle members. Comparison uses pre-fill placeholders for a/1.json and a/export.json; runtime receipts are excluded.
Exactly eight delivery members change: 0.json, 0.tgz, BATCH.sh, CONFIG.json, PACKAGE.json, a/0.json, a/4.py and a/6.py. Only payload 9.json and bundle 0.json/7.py change.
Simulated fill executes the real receipt, preparation and binding checks using authentic preparation bytes. Sparse archive headers replace model data; scan() receives simulated metadata.
`dryres2.py` and Python-3.6 `3.py check` pass; the local check remaps only Orchard paths. `dry2_c600.py` passes 27/29 checks; vnice/terminator hash checks fail because their real bodies are absent. Production checks remain strict.
`verify_c600.py` passes all original submit-assertion checks, the empty-general guard check, six rejection cases, and full/partial/stop-margin operator cases. CPU receipts in this test are explicitly synthetic.
All 29 login/helper/embedded Python sources pass `py_compile` on local `/usr/bin/python3` 3.6.8; all five shell scripts, generated fill shell and BATCH.sh pass `bash -n`. Staged model code retains A's Python environment.

`test_score_c600.py` passes with an unchanged copy of `score_r5_look.py`; no scorer patch is needed. The synthetic return contains exactly 450 original camera rows and no distance/room rows.
All camera metric dictionaries, intervals, call counts and H3 decisions equal the full step-400 result at 99.82%: displacement 81.600%, rotation 76.133%, direction 94.667%; calls 450/450.
The existing look-level test and three corrupt-binding rejection tests pass. Missing distance/room type rows are incomplete; separate A-only room diagnostics remain baseline-only. These are synthetic results, not step-600 measurements.
Evidence: `rehearsal/RESULT.json`, `TIMING.json`, `verify/RESULT.json`, and `scoring/TEST_RESULT.json`; local reruns use p1cpu Python with BLAS/OpenMP threads set to 1.
Not tested: live GCS/download hashes, real large archives, the two policy bodies, actual Orchard CPU staging, model inference, Slurm submission, live USR1 delivery or remote fetching. No SSH, network, Git, GPU, deletion or submission ran locally.
