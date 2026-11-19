# sb_f64 status

Stage 0 (inputs) DONE 2026-11-18 23:40 EST.
- Package `in/tree_rebuild_b18_60e6ea72.tar` copied from W, sha256 caa09d0c... verified; extracted to `pkg/`.
- Real Qwen3.5-9B meta files (config, tokenizer, processor configs; no weights) copied from the base snapshot c2022362 (= N base_identity) to `in/qwen35_9b_meta/` (23 MB, one throttled rsync). Weights are not under n30_mirror or W (largest there: a 2.9 GB step-544 subset), so the dry run uses the real architecture at random init.
- Read package A (sb_callrate .../out3/A) inspected read-only.

Next: stage 1 (frame-count entry points, 64-frame config, patches).
