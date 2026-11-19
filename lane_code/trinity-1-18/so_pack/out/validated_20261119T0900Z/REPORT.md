VERDICT: PARTIAL A strict default-off wrapper passed 21 local tests, but privacy and missing authenticated-input blockers prevent a release-ready package.

This directory contains the source actually validated by this run. Its four source hashes match the saved frozen source. Concurrent edits changed both the root command and the out/tool aliases after validation; their newer behavior is outside these results. This snapshot retains the strict scan of all package text, comments, environment literals and nested archive contents.

Measured results: 21 tests passed in 113.446 seconds; GNU time reported wall 1:54.08 and maximum RSS 320548 kbytes. All six historical defect classes have planted regressions: null frame metadata, isolated import, overwritten env archive, stale embedded descriptor, missing error trap and USR1 without end-slot evidence. The B4 test establishes error visibility, not the unknown node/bootstrap root cause. Signal fixtures do not certify production trainer export.

The exact full-suite command was:

```sh
nice -n 10 /usr/bin/time -v env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/delivery_source/test_pack.py --work /scratch/jjyeung/orch_n30/so_pack/work/delivery_tests > out/logs/delivery_tests.txt 2> out/logs/delivery_tests_time.txt
```

Exact unittest summary:

```text
Ran 21 tests in 113.446s

OK
```

Builder-property command:

```sh
nice -n 10 /usr/bin/time -v env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/release_source/test_builder_tokens.py --work /scratch/jjyeung/orch_n30/so_pack/work/release_token_tests --baseline-config work/release_tests/D_BUILD_CONFIG.json --patched-d work/builders/d/build_d.py --original-r10 /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/build_r10.py --patched-r10 work/builders/routed/build_r10.py > out/logs/release_token_tests.txt 2> out/logs/release_token_tests_time.txt
```

Exact property assertions, with the build receipt JSON omitted here but preserved in the raw log:

```text
D_DEFAULT_BYTES_IDENTICAL_PASS sha256=71af4fa4a4c329266b5879c0ca6dc58c86fb3556eb11bd62e44144ff3bc08f6d bytes=5272526
D_EXPLICIT_TOKEN_PASS a0123456789ab
R10_DEFAULT_LOOP_AST_IDENTICAL_PASS
R10_EXPLICIT_MINT_AND_REJECTIONS_PASS (full source archives absent)
```

Patch 01 adds the wrapper, native-check probes and mutation tests. Patch 02 adds optional token-enabled builder copies plus property tests. Both are add-only diffs against the input tree. The optional copies preserve native default code paths; explicit behavior requires the opt-in switch. This snapshot regenerates those diffs directly from the tested source; regeneration does not claim an additional test run.

The command prints ossh plans; the transport test uses only a local copy stub. No SSH, Slurm, GPU, Git, deletion or paid API operation ran in this task. Python 3.6 grammar passed; this tested source ran under Python 3.12, so actual Python 3.6 runtime compatibility remains unproven.

Not done: complete step-600 release, missing full r10 source archives, authenticated export/env/policy mirrors, actual rows absent from fixtures, full job-venv restore/RGB checks, GPU execution, and four-rank trainer stop/export. Supplied payloads fail strict privacy. These failures block release instead of producing a passing receipt. Orchard-only failures retain CPU/batch diagnostics and block GPU submission.

The shared workspace exceeded the 3 GB limit after concurrent review data appeared: the last measured allocated size was 3,486,248,960 bytes. This snapshot adds only small source/docs/log files; no more data-producing tests ran. Cleanup is queued in ../PENDING_USER_COMMANDS.md under the user's no-deletion rule. This run could not maintain the cap while another writer grew the shared tree, and deleted nothing.

Framework behavior evidence is recorded in ../FRAMEWORK_EVIDENCE.md with installed-source file:line and official PyTorch documentation references. No estimate is presented here as a measurement.
