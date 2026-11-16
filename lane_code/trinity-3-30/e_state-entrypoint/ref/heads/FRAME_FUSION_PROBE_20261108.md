# Frame fusion probe FP1 (heads_up5, 2026-11-08)
- Question: does the frozen Qwen3.5-9B carry more relative-pose information when the two frames of a temporal patch are close or identical, instead of ~2 s apart (spread)?
- Answer (job 104414; work/h5/fp1/results/TABLE.md): yes, at the middle LM layer. Sparse rotation on 38 held-out scenes / 608 anchors: S 88.0, D 75.2, P0.5 68.1, P1.0 68.6 deg. The final layer is near chance in every layout (85-90). In-pair motion: S 31.7 deg / 0.34 m, P0.5 11.8 / 0.12, P1.0 22.0 / 0.23.
- Method: mean-pooled per-viewpoint states (layers 16 and 32), the C1 camera head trained 400 steps on 512 training clips, the same anchors in every layout.
- Caveats: frozen features and a small probe give absolute errors far from trained heads, so only the ranking counts. The equal-token check P0.5-16 was not run. Peak memory was not recorded.
- Status: settled for the layout pick; the orchestrator chooses the 800-step layout.
