# Codex build: `--max-bytes` for the K1 phase CLI (kit copy only; no change to receipt identities)

Model gpt-6-astra, effort high. Write only in /scratch/jjyeung/orch_n30/k1_ops3/work/codex_maxbytes/ (patched files, diff, new pins, tests). Read-only: /scratch/jjyeung/orch_n30/k1_ops3/kc/** (executed kit copy), /scratch/jjyeung/orch_cd/**, /scratch/jjyeung/k1/run_tower_sam_2/** (halted root; do not touch it). No Git, ssh, kill, GPU (CUDA_VISIBLE_DEVICES=''), network, deletion, recursive search outside named folders. Read /home/jjyeung/.claude/CLAUDE.md "Key Trinity Cluster Rules" first. Python: /scratch/jjyeung/envs/p1cpu/bin/python (tests) and /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python (torch).

## Problem
Run /scratch/jjyeung/k1/run_tower_sam_2 halted with ValueError('Output cap') after 152/300 captures: kit_k1a/work/k1_phases.py run(..., max_bytes=1_500_000_000) (line 115; check at 163) and k1_cli.py (line 53) never passes max_bytes. Output is ~9.9 MB/capture, ~3.0 GB for 300.

## Change
1. kit_k1a/work/k1_cli.py only: add `--max-bytes` (positive int, default 1_500_000_000 so current behaviour is unchanged) and pass it to F.run as max_bytes for stage cache. Do NOT change k1_phases.py, k1_pipeline.py, run_k1.sh, native_kit/* or anything in B.source_identity() / producer_sha256, so BINDING.json and the 152 PHASE_COMPLETE receipts in the halted root stay valid. Prove that: show that B.source_identity() and B.sha(k1_phases.py) are unchanged by the patch (compute both with the patched kit in a scratch copy under codex_maxbytes/, CPU only).
2. Confirm run_k1.sh forwards extra args to `k1_pipeline.py cache` ("$@") so `--max-bytes 4000000000` reaches k1_cli.
3. New DEPENDENCIES.json (from kc/k1_build/work/kit_k1a/out/DEPENDENCIES.json, sha c0c81f33...) with only k1_cli.py's hash changed.
4. Tests: default unchanged; flag reaches F.run (monkeypatch F.run with a recorder; use the kit's CPU fixture path or a stub manifest); non-positive values refused. Run native_kit/test_kit.py and test_guards.py on the patched scratch copy with p1cpu.
Report: unified diff (difflib), new pins, identity proof, test outputs. A second reader follows before use.
