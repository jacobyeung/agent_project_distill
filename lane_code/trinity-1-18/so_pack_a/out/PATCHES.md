# Patch layout and verification

Apply `patch -p1` for both patches at a writable root corresponding to the supplied input mirror. Patch 01 adds the packaging command, structural probe generator, regression tests, input refusal tool and handoff documents. Patch 02 adds only pack_token.py and test_pack_token.py beside the native r10 and D builders. Neither patch edits native source or embedded scripts.

The top-level delivered files are canonical. TOOL_SHA256.json records their hashes. PATCH_VERIFIED.json records a fresh patch application, exact reconstructed-file equality, adapter-copy equality, source-input hashes and test log hashes. REPORT.md contains exact commands and outputs. Test output directories must be fresh; tests do not delete prior evidence.

Run test_native.py first, then pass its RESULT.json as PACK_NATIVE_RESULT to test_review.py. Run test_pack.py under the specified CPU Python and both additive adapter tests under /usr/bin/python3 3.6.8. Set CUDA_VISIBLE_DEVICES empty, OMP_NUM_THREADS=8, MKL_NUM_THREADS=8, OPENBLAS_NUM_THREADS=8, TOKENIZERS_PARALLELISM=false and PYTHONDONTWRITEBYTECODE=1; prefix commands with nice -n 10. The logged commands in REPORT.md include those settings.

Production actions require --enable. Token override requires --enable-token; wrapper normalization requires normalize_wrapper=true; structural fill requires fill_mode=structural. All default OFF or retain the original mirror path. Native D default-OFF delivery equality is measured. r10 default source equality is measured; its full build refuses missing original inputs. The raw D scorer mismatch remains a release blocker.
