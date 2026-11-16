# Matched timing on moving scenes

The question is whether SPLIT's accuracy and latency tradeoff holds on the moving-scene benchmarks under matched question selection and explicit preparation accounting.

The answer is a ready offline measurement package for 50 STI-Bench, 50 ReSTI and 50 OSI-Bench questions, frozen with seed 20261112 and proportional category quotas before outcome inspection. The cohort contains 45, 46 and 42 scenes respectively. The canonical design is `/data3/jjyeung/orch_n13_20261026/rebuttal_iclr/DYN_TIMING_DESIGN_v1.md`. All lane artifacts are under `/home/jjyeung/agent_project/agent/scratch/devin_lanes/dyn_timing_1112/out/`.

The required systems are baseline HIGH, SPLIT with the static speed settings, SpatialClaw at released settings, and pySpatial with explicit LOW code generation and MEDIUM answer/fallback. Optional SPLIT with printed method settings is also ready and runs last. Its native requests retain HIGH thinking, thought summaries, nonstream transport and native stopping. Priority service is an explicit timing-protocol setting for both SPLIT points and the baseline; both comparison harnesses retain provider-default service.

Each point reports the official score and measured preparation separately. The harnesses reconstruct inside each question's clock. SPLIT uses pinned prepared stores and attributes the recorded Point4D96 producer duration to each question. Missing anchor, scalar and rescaling costs keep full-reconstruction totals null. Neither those attributed totals nor frame-based input clocks establish raw-video end-to-end latency.

SpatialClaw's native video path supports per-frame DA3 geometry, camera motion and trajectory rendering. pySpatial uses native VGGT geometry, generated-code execution and image fallback. Its public-input adapter admits all five supplied choices on STI/ReSTI and preserves four-choice and numeric formats. The adapters add no SPLIT geometry or tracks.

The 1-18 placement is fully admitted offline. SpatialClaw's four model pins total 10.211 GB and hash-match. pySpatial's 38,441 source/dependency entries total 11.971 GB and hash-match, including its declared RAM relocations. Only 1.506 GB of selected frames and 0.164 GB of package files were staged over InfiniBand. `PLACEMENT118_AUDIT_v1.json`, `FRAMES118_VERIFIED_v1.json` and `ADMISSION118_v118a.json` record the evidence.

Each SpatialClaw unit requires 109 GB free scratch: 4 GB output, 5 GB margin and the 100 GB floor. Measured static outputs occupy 0.36–0.58 GB per 50 questions. Each pySpatial unit requires 117 GB: 12 GB output, 5 GB margin and the floor. Its native 32-frame reconstruction retains 206,076,290 bytes per question, or 10.304 GB per 50 before traces and retries. The cap allows modest retries and remains enforced.

The releases authenticate every package file, admit all selected questions, and pass native mocked dispatch-to-canonical-scored-row proofs on each benchmark. Tests exercise E choices, pySpatial fallback and explicit request levels, SPLIT native empty-response recovery, exact source/model bindings, capacity boundaries, lease exclusion, private service routing and owned shutdown. Provider and GPU boundaries are mocked; live service loading and provider acceptance remain launch gates.

`NEEDS_LAUNCHER_DYN_TIMING.md` contains the combined commands and preconditions. `QUEUE_LINES_DYN_TIMING_118.tsv` contains six four-field lines for the 1-18 variant queue, using GPU 6 and fresh roots. The lane did not append them or launch an experiment. The launch owner must recheck capacity after retained static outputs; a passing admission reserves no future space.

Rejected choices are sampling successful or fast questions, replacing missing selected inputs, reporting fixtures or partial units as measurements, substituting G3T reference times for Point4D96, regenerating the reconstruction bundle, transferring duplicate environments, changing a sealed package in place, treating 50 questions as 50 distinct scenes, and assigning Gemini HIGH by leaving pySpatial's answer level unspecified.

DSI remains conditional because its complete membership/input/source closure has not been admitted. Baseline LOW and MEDIUM are outside the requested timing comparison. No new sampling or benchmark claim uses the quarantined VSIBench development role.

The decisive live checks are complete fixed denominators, native model loading, recorded requested/served settings, all request attempts and reconstruction components, private service ownership, and final official scoring. A cluster-killed run is preserved and requires review. This lane used no provider calls or GPU runs.
