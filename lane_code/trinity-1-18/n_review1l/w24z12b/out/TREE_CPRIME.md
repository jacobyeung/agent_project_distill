C′ has seal `4648e6b3e66c1c08db091dc3104455d6011000fb9d961aa1f78eee03e38ec43d`. The tree's own `source_seal.inventory` and `p3_provenance.digest` computed it.

Its base is `0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de`. The authorized patch has SHA256 `a0d9cef403712f2636ac4a1eb8d72eedd7251df7ed95cb1c0ef8d377bb5d8762` and was applied with `patch -p1`.

Exactly three files differ:

- `student_pilot/carrier_c1_run.py`
- `launch_r1/entry.py`
- `tests/test_r1_processor_compat.py`

`work/build24m4l/TREE_CPRIME.json` records both inventories' changed-file hashes. `patch.log` records the application. C′ contains no other source changes.

The three compatibility tests pass. The existing single-image, host-admission and carrier-run suites ran 37 tests in total, including those three: 33 passed, two skipped and two failed on incompatible fixtures. The raw failures remain in `tree_tests3.log`. Two external fixture corrections then passed: legacy admission uses null pixel fields; the single-image preparation fixture supplies its missing trace version and source metadata. `TREE_FIXTURE_TESTS.json` records those exact fixture edits. No test source in C′ was edited.

`DEPENDENT_PINS.json` lists the archive, both source records, source maps, decoded config identities, capsule hashes, runtime upload and changed kit files. `PIN_AUDIT.json` authenticates all four embedded archives and verifies that no old C identity remains in their decoded metadata. The runtime source record is uploaded as `u/e380ee2ca038d4148feb46c864dcc9068e170007c903aaf5a8740a9327f9a85e`.

The tests use CPU fixtures. They do not establish production row equivalence, real tokenizer-asset compatibility, GPU forward behavior or training admission.
