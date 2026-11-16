# FAST reference tokenizer (vendored)
- Source: https://huggingface.co/physical-intelligence/fast, revision ec4d7aa71691cac0b8bed6942be45684db2110f4 (api.json is the model-info response at download, 2026-11-11).
- `processing_action_tokenizer.py` sha256 6f021ca1f4c1b194ab6fa399d80baf3d642eadb17efb8f73301e4ac401522c20; `processor_config.json` sha256 f40cfbb1020858fe1d48c0f946b0c1315a90d6e84aa82710036f24f4c167706a.
- The package copy `vla_heads/codecs/fast_reference.py` is byte-identical; `FastCodec` calls it directly (fit, encode, decode). `tests/test_tokens_actions.py::test_fast_matches_reference_stream` checks both copies' sha256 and the token stream.
