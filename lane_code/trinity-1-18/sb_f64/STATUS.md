# sb_f64 status

Stage 0 (inputs) DONE 2026-11-18 23:40 EST.
- Package in/tree_rebuild_b18_60e6ea72.tar copied from W, sha256 caa09d0c... verified; extracted to pkg/.
- Real Qwen3.5-9B meta files (config, tokenizer, processor; no weights) copied to in/qwen35_9b_meta/ with one throttled rsync. No 9B weights exist under n30_mirror or W, so the dry run uses the real architecture at random init.
- Read package A inspected read-only.

Stage 1 (entry points, config, patches) DONE 2026-11-19.
- Decision: nested 64 viewpoints (32 anchors + 32 bisection frames). Carriers, markers, heads, targets and question text stay on the 32 anchors. Record: out/kit/DESIGN_F64.md.
- Patched tree: pkg/work/tree_f64 (copy of tree_r1; must sit beside tree_r1 because tests resolve ../base etc.).
- Configs: out/kit/configs/r1_config_f64.json and r1_config_n32_pinned.json, with CONFIG_DELTA.json.
- Found a pre-existing launch blocker: N's config has max/min_pixels null, so processor_for_receipt refuses it (processor_resolution_pin_missing). Both configs pin DEFAULT_PIXELS; r1_handover now treats null as DEFAULT_PIXELS.
- Focused suite (build-18 list + frame tests, 109 tests): baseline tree 1 error, patched tree 1 error; the error is the same absent input (/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl).

Stage 2 (CPU dry run) RUNNING 2026-11-19 00:05.
- Encode of every rank's first row of every stream, real tokenizer and processor: done for both configs and both clips (out/evidence/encode_*.json). 64 viewpoints: 9,127-9,303 tokens at 4:3, 10,039-10,215 at 16:9; ceiling 16,384; no truncation.
- Full-depth forward (real 32 LM layers, random init, BF16 base): smoke row finite, 24.1 GB peak RSS. All-rank runs and reduced-depth fwd+bwd runs are queued in work/logs/stage2*.done.
- IO note: the first dry-run processes used /scratch/jjyeung/envs/vllm, whose stdlib is missing, so Python fell back to its compiled prefix /data2/jjyeung/envs/vllm and imported from NFS. Nothing was killed. Later runs use p1cpu (local) plus the torchvision 0.26.0+cpu wheel unpacked under work/pyext_tv.

Stage 3 (read configs) DONE 2026-11-19 00:00.
- out/kit/read/: f64_read.py, reader_f64.patch (parity.py, parity_adapter.py, prepare.py), READ_CONFIG_F64.json, READ_PLAN_F64_DIFF.md, STUDENT_FRAMES_PLAN.json (152 captures, 4,864 frames to decode, 1,131 already decoded in the tower manifest).
- The tower's 64-frame dense manifest (devs1_tower_v2) differs from the training rule in all 55 of its 64-frame captures, so the student gets its own manifest built by the training rule.

Stage 4 (tests) DONE 2026-11-19 00:05.
- tests/test_f64_layout.py: 12 tests, 12 pass locally (encode-level agreement included, env F64_META/F64_CONFIG/F64_READER_ROOT).
- Focused suite on tree_f64 (build-18 list + frame tests + test_f64_layout, 121 tests): 1 error, the same absent POOL.jsonl as the baseline.
- Overflow gate: the R1 trainer aborts on any row that fails check_row, and the routing build admits suffixes up to 9,600 tokens, so at 64 viewpoints the 16,384 ceiling no longer holds by construction. out/kit/scripts/token_audit.py encodes every distinct planned row through Rows.get and check_row on CPU, sharded, and flags rows over the ceiling or the 11,500-token H100 tripwire. tests/test_token_audit.py: 4 of 4 pass on the synthetic nested store; its `run` path against a real preparation receipt is untested here (none exists locally).

Next: finish stage 2, then F64_REPORT.md and the kit tar.
