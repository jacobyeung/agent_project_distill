Both requested arms remain MISSING; no training accuracy or first-seen/count result was produced.
The registered workload is 1037 rows, 209 captures, 192 rooms and 770 capture/name jobs across all three datasets.
The table-covered rowset contains 883 rows. Each unavailable arm/reference contrast is recorded on both fixed rowsets in K1_TRAIN_TABLES.md and K1_TRAIN_RESULTS.json.
Census command: `bash scripts/train_cpu.sh code/train_prepare.py`.

CPU feasibility: the two specified train captures were attempted with all registered operand names and 32 anchors planned per capture.
Both attempts failed while importing SAM 3: `ModuleNotFoundError: No module named iopath`.
The source independently requires a nonempty CUDA GPU list and calls `.cuda()`; the staged predictor has no CPU configuration.
These are failed construction attempts, not completed two-capture tracking benchmarks.
No checkpoint was loaded and no frame was decoded or tracked. Full-set CPU hours and the six-hour subset size are MISSING.
The conditional subset rule was fixed before attempts: SHA256-sorted captures within dataset, round-robin all three datasets, complete captures/all names, at most six process CPU-hours.
No subset ran because no successful pilot timing exists.
Probe command: `bash scripts/train_cpu.sh code/train_cpu_probe.py`.
Attempt overhead: 0.120400 wall seconds; 0.114295 process CPU seconds; peak RSS 233620 KiB. These are not inference costs.

The object-gathering hook points to read-only sb_kbox4 and remains MISSING.
Missing expected receipt: `/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/DECISION.json`.
Missing expected replay receipt: `/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/REPLAY_CHECK.json`.
Missing exports in `/scratch/jjyeung/orch_n30/sb_kbox4/box_math.py`: count_objects, object_source, price_k1_tracks, stage1_replay.
The missing object-source/count interface blocks gathering independently of the frozen fusion choice. Legacy gather is not a substitute for the specified merged object set.
No A0 geometry was substituted, no GT-geometry arm ran, and no fusion winner was invented.
Readiness, diagnostics and contrast-report command: `bash scripts/train_cpu.sh code/train_finalize.py`.

Paired intervals, refusals and first-seen/object counts remain MISSING. A missing execution is not a zero-scored refusal.
Future paired scores use identical registered rows, refusals scored zero, 10,000 room-bootstrap draws and seed 20261119.
GPU_NEED.json records the specification estimate for all remaining tracking: one 48 GiB card, 1.3 GPU-hours estimated, 1.75-hour hard stop; no GPU timing was measured.
No GPU is authorized or used by this task.

Isolation: CPU-only PyTorch, nice 10, eight threads, 38,000,000 KiB virtual-memory cap; all writes stay in this workspace.
Only the named specification was copied from NFS. Kit code/configuration/scripts and train rowsets were copied locally; evaluation data and inherited result tables were excluded.
The mixed local manifest container was hashed; only explicit training blocks were decoded. No held-out caches, labels, frames or outcomes and no R0-dev data were opened.
No SSH, network, Git, process termination, tmux operations, model downloads or GT-geometry evaluation ran.
JSON evidence records input SHA256 values. The copied train manifest preserves existing registration; no membership, frame map or proof was invented.
Archive command: `bash scripts/train_cpu.sh code/train_finalize.py`; verification: `sha256sum -c out/sb_kobj3.tar.sha256`.
The archive includes code, train inputs, configuration and evidence; ARCHIVE_MANIFEST.json records each member hash. PACKAGE.json records archive verification.
No borderline revision-history prose is retained.
