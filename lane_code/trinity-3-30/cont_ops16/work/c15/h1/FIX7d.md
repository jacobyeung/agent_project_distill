Cause: eb3429c5.tar repeats the empty JSONL member and its SHA256SUMS line; the checksum parser rejected identical rows and the extractor incorrectly limited repeats to inventory occurrence counts.
Change: tools/selection_stage.py:95 accepts identical checksum rows; :102 verifies repeated member size/hash without writing twice; :70 aligns path normalization/directories and :79 enforces member_prefix.

| s.py alignment | Result / justification |
|---|---|
| build/fx/b/s.py:134–171 | POSIX names, safe directories, prefix, unique count = inventory size, and complete trailing-byte digest align; duplicate payloads receive the additional requested byte verification. |
| build/fx/b/s.py:100–174 | Sparse refusal, checked checksum metadata, inventory requirement, fresh outputs and full pre/post hashing remain deliberate restrictions; every branch is mapped in [ARCHIVE_ALIGNMENT7d.md](evidence/fix7_selection/ARCHIVE_ALIGNMENT7d.md). |
Tests: test_fix7_selection.py, test_fix7_deriver.py, test_fix7_admission.py and test_fix7_package.py PASS; identical duplicate member + SUMS line pass; conflicting size/hash/line refuse; prefix, dirs, sparse, count, trailing bytes and existing-output guards pass; deterministic build and bash -n PASS.
build/q.sh: 120696 bytes; SHA256 aa534ae743700bb321dadb55de38a2e173bb23fb4abd3af9623a6a5c27f41f2a.
Output: BUN/q_f28a4d73/o/ (tools/package_selection.py:55); q_7b62108a, q_c492e8d1 and q_91f06d2e stay untouched. Local CPU only; no SSH/network/Orchard/GPU/Git/deletion; production equality remains unverified.
