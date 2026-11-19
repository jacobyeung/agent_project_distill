VERDICT: PARTIAL The default-off wrapper and regression tests are delivered, but strict privacy violations and missing authenticated build/fill inputs prevent a production release.

`pack.py` calls existing builders, checks built bytes locally, and generates place/fill/CPU-then-GPU-submit commands. The optional builder patch lets a fresh `all --yes --token …` use a token chosen in advance. No SSH, Slurm, GPU, Git, deletion, or paid model API operation ran. Task writes stayed under `/scratch/jjyeung/orch_n30/so_pack`.

Measured results at 2026-11-19T07:57:49Z:

| Result | Evidence |
|---|---|
| 18 unit tests passed; the requested six incident classes have planted failures. | `logs/final_tests_time.txt`, `DEFECT_MATRIX.md` |
| The final suite took 1:59.87; GNU time reported maximum RSS 319,876 kbytes. This is its reported field, not an aggregate live RAM trace. | `logs/final_tests_time.txt` |
| D's default-path deliveries matched across all 5,272,526 bytes. Its explicit-token full build passed. | `logs/final_token_tests.txt` |
| r10's default mint-loop AST and explicit mint/rejection cases passed; its full build is unvalidated. | `work/final_token_tests/RESULTS.json` |
| The inventory indexes 347 source predicates. The D200 audit passed six local gate groups and failed two prerequisites. | `CHECK_PREDICATES.json`, `D200_AUDIT_RESULT.json` |
| A4/B5 contain 498/499 payload filenames matching the strict term list. These are name matches, not counts of semantic defects. | `PRIVACY_FINDINGS.json` |
| The workspace occupied 1,833,693,716 bytes, below the requested 3 GB cap. | `MEASUREMENTS.json`; `logs/disk.txt` records free disk space. |

The configured local limits are eight CPU affinities and 28 GiB virtual address space per process, with CPU library threads capped. The D builder's 19,595 GPU-second budget is an **estimate** from the supplied timing file; its report says the budget does not fit. No GPU time or full-restore memory was measured here.

`patches/01_pack_gate.diff` adds the wrapper, isolated native probes and mutation tests. Its switch defaults off. This exact command ran from `/scratch/jjyeung/orch_n30/so_pack`; choose a fresh work path to rerun it:

```sh
nice -n 10 /usr/bin/time -v env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/final_check/test_pack.py --work /scratch/jjyeung/orch_n30/so_pack/work/final_tests > out/logs/final_tests.txt 2> out/logs/final_tests_time.txt
```

Exact summary output follows; the linked raw log contains every test result and resource field:

```text
Ran 18 tests in 119.253s

OK
```

`patches/02_explicit_builder_tokens.diff` adds default-off token branches to working copies of r10 and D, plus their tests. The D test compares complete default delivery bytes. The r10 test covers its mint branch only, because its authenticated source archives are absent.

```sh
nice -n 10 /usr/bin/time -v env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/final_check/test_builder_tokens.py --work /scratch/jjyeung/orch_n30/so_pack/work/final_token_tests --baseline-config work/final_tests/D_BUILD_CONFIG.json --patched-d work/builders/d/build_d.py --original-r10 /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/build_r10.py --patched-r10 work/builders/routed/build_r10.py > out/logs/final_token_tests.txt 2> out/logs/final_token_tests_time.txt
```

Exact assertion output follows; `logs/final_token_tests.txt` also contains the full build receipt:

```text
D_DEFAULT_BYTES_IDENTICAL_PASS sha256=71af4fa4a4c329266b5879c0ca6dc58c86fb3556eb11bd62e44144ff3bc08f6d bytes=5272526
D_EXPLICIT_TOKEN_PASS a0123456789ab
R10_DEFAULT_LOOP_AST_IDENTICAL_PASS
R10_EXPLICIT_MINT_AND_REJECTIONS_PASS (full source archives absent)
```

Both patches applied to a local input-tree copy. The resulting six files match the delivered/tested copies byte for byte (`PATCH_VERIFIED.json`). The production sources pass Python 3.6 grammar checks; no actual Python 3.6 runtime ran here. Remote scripts passed `bash -n`; none executed remotely. `PATCHES.md` states the patch base, switches and test scope. `FRAMEWORK_EVIDENCE.md` cites installed torch source and official versioned documentation.

The supplied D200 audit fails on forbidden text and absent authenticated fill inputs. A fresh explicit-token `all` test builds the requested token and stops at privacy before transport. `CHECK.json` records local failures, probe logs retain tracebacks, and native CPU logs/receipts remain separate. The batch trap preserves early failures and signal termination; the submit wrapper reports a failed CPU state or wait expiry before stopping.

What could go wrong and how it is detected:

- A package or config can change after checking. Fingerprints, file/plan/payload hashes, bundle equality and pinned operational-script hashes reject the changed bytes.
- Strict substring scans and the dependency resolver can conservatively reject native-admissible input. The resolver currently refuses dependency links; its local error names the offending member. Extend `forbidden_extra` for aliases outside the finite built-in list.
- Orchard can fail on allocation, pool permissions, namespace setup, venv versions, restore/RGB staging or GPU bootstrap. Native CPU checks still precede GPU submission. Error tails and the batch capture file make available diagnostics readable; an unwritable package path can also prevent capture.

Not done: a real step-600 build/fill/release; a full r10 build; full-size same-input fill/resolution; authenticated dependency-link handling; actual login-runtime and remote transport validation; real restored/RGB CPU rehearsal; CUDA/H100 execution; and the trainer's four-rank stop/checkpoint/export proof. The isolated-import regression uses a sibling-import fixture because the direct-read worker is absent. The B4 regression catches missing diagnostics, not its unproven node/bootstrap cause. The native USR1 proof covers the read runner with a tiny CPU decoder, not the trainer.

`REQUIRED_INPUTS.json` names the missing authenticated inputs. `NOTE_FOR_CONT_OPS.md` gives the one-page step-600 procedure, and `ORCHARD_ONLY_CHECKS.md` separates remote facts from missing local prerequisites. Input references and event filenames are retained to identify authenticated bytes and the requested regressions, not to narrate revisions.
