# vla_schema_v2 worked-example generators (vendored)
- `schema_examples.py`: copy of /scratch/jjyeung/orch_cd/vla_design_review/schema_examples.py (sha256 5d32c582655ce6ba11b0a77df334e7cec94c104ff746c86979496a3a146fac4d, after the orchestrator's 14:14Z final-check fixes; its own run prints "ALL 53 CHECKS PASSED"). VLA_SCHEMA.md v2 sha256 b80b10a2bb217a525061e859b6642abaa6f9b5c54f1ab8c1013fee18f91c7277 at the same time.
- Tests import its generators (`example_chunk`, `fast_fixture_chunks`) and constants (`EX1_WHERE`, `EX3_WHERE`) instead of copying arrays.
- `../fast_fixture_v2/fast_fixture_v2.json` = `FastCodec(8, 7, 1024, 10.0).fit(fast_fixture_chunks()).save(...)`, sha256 cab2442cc376ab1ee68f13097bce41462b2db0d1655152a086a04df3e00352b5, tokenizers 0.22.2 (also at vla_heads/out/fast_fixture_v2.json).
- `../reserved/qwen35_9b_c2022362_rare_ids_1025.json`: copy of vla_heads/out/ (ids 247019..248043; pin = its `sha256` field 87a74b67...).
