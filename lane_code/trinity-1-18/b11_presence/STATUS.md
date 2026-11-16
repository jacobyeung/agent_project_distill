# b11_presence STATUS (Devin lane on trinity-1-18; updated 2026-11-16 16:35Z) — DONE
Goal (brief briefs/qs/11_presence_probe.md): price step 544's own presence as a head path for appearance order and counting on K1 held-out.

## Result
- Decision: NO head path for appearance order. Primary head (arm I, chosen by train room-CV, frozen before held-out) 32.87 vs step-544 direct B2048 71.33 on 143 held-out items: -38.5 [-48.0, -28.9], 32 rooms. Counting: head 25.0 vs direct 64.3; GT-presence runs 24.8 < constant 53.4 (presence cannot count).
- Direct is UNCLAIMED (vLLM 0.23 + prompt shim, parity 16/16); K1 rooms are training rooms.
- Report out/PRESENCE_PROBE.md; design record distill_design/PRESENCE_PROBE_K1_20261116.md + INDEX line.

## Artifacts (lane folder /scratch/jjyeung/orch_n30/b11_presence)
- code/: prep.py 6857666a, scorer.py be4bdc9b, analysis.py 9b8c0038, direct.py 1ffe0cb3 (the read ran with 0ed96714), run_gpu.sh, det_compare.py, debug_parity.py, test_cpu.py, test_analysis.py be848862, test_direct.py b2f85689.
- out/prep (CAPTURES/ITEMS), out/tests (all PASS), out/analysis: FROZEN.json f46e7cae, ANALYSIS_train.json 49e00f24, ANALYSIS_heldout.json 59232ace (+ items jsonl).
- from13/: journals V/IY (296+296), det (DETERMINISM pass, identical logits), direct journal 247 rows + PARITY receipts, run logs; PULL_MANIFEST verified.
- Reviews: work/review/ (prompts, v1-v5 code copies); receipts agent_project_distill/agent/scratch/codex_runs/*_b11_review{,2,3,4,5}.
- Mirror: work/mirror_b11_v1.tar (sha d98abb0e, 66.8 MB) = trinity-1-13:/scratch/jjyeung/n30_mirror/b11_presence/mirror_b11_v1.tar (sha equal).

## In flight
- Nothing. Cards released: 1-13 card 5 at 14:29:37Z, card 1 at ~16:26Z (run_gpu's redundant direct stage died at engine init: no flashinfer-sampler override in run_gpu.sh; harmless). No tmux b11* on 1-13; Codex reviews finished.
- Staging on 1-13 /dev/shm (exports/m544 18 GB reusable by b05; b11_presence 2.5 GB) listed in REMOVAL_CANDIDATES.md.

## Next (for any successor)
- Nothing owed. If ordered: re-read after presence training on non-training rooms with the accepted runtime, same protocol (analysis.py fit, then --read-heldout).
