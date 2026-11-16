# Dynamic reconstruction timing at 32 frames

Question: How long does SPLIT take to reconstruct each moving scene before its first tool call, using 32 context frames on one H100?

Answer: SPLIT reconstructs a video in 16.567 seconds at the median across all 120 distinct videos, with a range of 15.948–17.233 seconds. The benchmark medians are STI-Bench 16.484 seconds (45 videos), ReSTI 16.416 seconds (46 videos), and OSI-Bench 16.577 seconds (42 videos). Every video has two valid, authenticated repeats; each statistic uses the faster complete repeat. Thirteen videos occur in both STI and ReSTI, and the combined statistic counts each once.

The input consists of the exact 32 displayed PNGs, frame indices and timestamps retained in the printed stores. Those 3,840 images occupy 1,506,148,655 bytes. The pipeline omits the 64 intervening frames used by the 96-context producer. Point4D's native model accepts 32 frames; a separate timing adapter preserves the complete sealed producer and bypasses only its dense96 orchestration.

The clock includes PNG decoding and model preprocessing, fresh MapAnything anchors, the Point4D DA3 backbone/depth head, D4RT cache and all 32×32×9×16 trajectory queries, common-valid scale fitting, fresh UniK3D inference and scalar fitting, gravity fitting, metric rescaling, format conversion, and closed/fsynced final tool stores. The clock excludes downloading, input admission, model loading, one untimed warmup video, raw-video extraction, provider requests, query tools and accuracy evaluation.

Each allocation keeps all three models resident on one H100 and starts with one untimed warmup. The measurement reconstructs every video twice into fresh output directories and selects the complete faster valid repeat. Each monotonic boundary synchronizes CUDA. NVML checks the allocated physical card before and after every video and once per second. A foreign process, an invalid geometry check or a missing valid repeat prevents a complete-cohort result.

Evidence: `INPUT_AUDIT.json` authenticates the scene/timeline/96-store bindings. `REFERENCE_96F.json` records all original producer receipts. The full producer comes from `stores_dense96_v3/producer`; the rescaler comes from `stores_dense96_v3/rescale_producer`. `newbench_dyn4d/out/UNIK3D_PRODUCTION_RECIPE.json` embeds the original depth producer; `unik3d_scale_fit.py` records the moving-scene scalar fit. Both use UniK3D revision 29f7862, weights 008aa543, resolution level 9 and batch four. No cached scalar is timed.

The metric rescaler implements the frozen formula and its eight constants. A CPU replay matches all 492 producer evaluations. The report discloses that this small function is transcribed from the contract because its standalone source is unavailable. UniK3D follows the moving-scene producer and scalar-fit source.

The reference median of 29.708920 seconds weights the 96-frame producer receipts by 150 questions. It excludes the MapAnything anchor, UniK3D scalar, rescaling and the final gravity-view write, and its GPU model is not recorded. The report also provides a distinct-video reference, because the primary new statistic weights 120 videos.

Rejected options: Cached anchors or scales omit required reconstruction work. Multiplying the 96-frame time by one third ignores the fixed 32-frame trajectory workload. Replacing Point4D with G3T changes the pipeline. Counting shared videos twice changes the pooled denominator. Selecting independent per-step minima constructs a runtime that never occurred. Raw-clip latency cannot be claimed from published-frame inputs.

Risks and detection: source drift fails SHA-256 admission; frame changes fail archive/member checks; unsupported 32-frame inference fails the video; missing valid depth support or invalid geometry fails the video; shared GPU use fails NVML isolation. Each completed repeat and its receipts are fsynced to persistent Orchard storage outside the measured interval. A CPU test verifies that these records survive process exit without cleanup. A deadline stop preserves completed repeats; a continuation measures only missing repeats. Models, software, driver, commands and both repeats remain in the evidence.

Status: Complete. Both allocations exited successfully on the same H100 80GB HBM3, with driver 580.159.03 and PyTorch 2.8.0+cu128. The final integrity check authenticates all 240 timed reconstructions, both warmups, all 3,840 input-frame hashes, stage clocks, geometry checks, store bindings and GPU isolation. There are no missing or duplicate timed repeats.

Result and per-video data: `/data3/jjyeung/orch_n13_20261026/rebuttal_iclr/DYN4D_RECON_TIMING_32F_H100_v1.md` and the adjacent `.csv`. Reproducibility evidence, including the immutable package, software inventory and both jobs' raw timing records, is in `/home/jjyeung/agent_project/agent/scratch/devin_lanes/dyn4d_recon_timing_1112/out/DYN4D_RECON_TIMING_32F_H100_v1_evidence.tar.gz`.
