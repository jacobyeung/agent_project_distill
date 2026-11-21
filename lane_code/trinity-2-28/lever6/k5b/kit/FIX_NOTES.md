# K5 fix after CPU check 174236 (token adba6b82bdb9d, /project/community/jjyeung/adba6b82bdb9d)
Cause: staging leaves fsw absent, and 0.py launched the namespace without creating it, so bwrap refused the bind source and the arm exited 1 in 6 ms with no error record.
Changes (0.py, 9.py, 2.py, build_k5.py; test and dry-run paths now point at k5b):
- 0.py ready(): creates sj, fsw and m/ap (parents, exist_ok) after stage() and before any launch, as rank 1's runner does (job.py:215-236).
- 0.py also applies rank 1's other steps there: it drops env names with the deny-listed fragment (this removes the sampler variable), runs the opaque check on argv, env and cwd (the package's process guard), sets umask 077, and refuses a CPU check with under 120 s left after staging (E28).
- 0.py job root is /tmp/a<job>-<pid> instead of a mkdtemp name, whose random letters could trip the opaque check about 1% of the time.
- Kept as designed: K5's thread counts and K5's own 1.json in the root.
- 9.py capture() keeps 4 KB from each end of the child's stderr and classifies it (B1/N1/N2/P1/B2/W1/S1/Z0/X0). Each nonzero arm exit records class, exit code, wall time and stderr bytes; if the arm left no error record, 0.py also appends E94 to 4.err or 5g.err. No stderr text leaves the job.
- Card identity per arm: 2.py records the torch UUID and PCI bus id, and 0.py records nvidia-smi index, UUID and bus id before each GPU launch.
- Fetch scripts (o_cfetch, o_fetch0, o_fetch1) tolerate a purged job id: squeue's error is dropped, and a final sacct state is still required.
- o_sub1.sh pins to job 0's node only after job 0 has left the queue and reached COMPLETED; otherwise it exits with E51.
Tests: 21/21 unit tests pass (TESTS_K5.log). The stub dry run exits 0 on every step, the opaque scan passes 37 checks, and bash -n and compile pass.
New LaunchPath test (LAUNCH_TEST_K5.log): the old lever5 0.py fails with status missing, exit 1 in 22 ms and no error record. The new 0.py passes: its worker starts in the pinned interpreter inside the real namespace and stops only at the empty capture list.
Place: o_place.sh is 8,761,360 B, sha256 64a56345c36cbe9772e7993084779d24eb494966becea060791415912fbbdc3f, and places 6,748,442 B. The forecast is unchanged: 32.0 min per GPU job, 48.0 min at x1.5, and the CPU check takes 24.8 min.
