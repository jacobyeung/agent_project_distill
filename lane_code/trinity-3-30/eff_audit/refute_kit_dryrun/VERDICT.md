# Refute check: change #2 kit-dryrun (2026-11-16)
refuted: true (the claimed saving is overstated; the change itself is sound)
- D0 170050: caught (rowschema null total_num_frames; prod-config prepare). Supported.
- K1 170193: caught (prose anchors.members; config identity). Supported.
- tower_sam (INCIDENTS row 7): run 2 on a Trinity GPU, not a first launch; cap is a code default "max_bytes=1_500_000_000 in k1_phases.run (line 115) ... k1_cli.py does not pass it" -> lint_config sees no config field; a CPU run makes no real-size output. Not caught as briefed.
- tower_sam run 1 (row 6): GPU-only inference-tensor crash. Not caught (record admits).
- K1 170206 (10:45Z, omitted from the claim): "stage_job.py never stages the three step_400 depth files"; "every one ran the CPU boundary ... CPU.own never calls read_runtime.load_model" (events/k1_ops3/20261116T1117Z_RESULT_170206_root_cause.md). Dry run with CUDA empty would mark load_model gpu_only -> not caught.
- Session tally: 2 of 5 first-run failures, not 3 of 3. evalx 5 of 9 pilots plausibly supported (169477 mkdir, 169537 + 169589 stale pins, refusal-size recheck, 169687 argument).
- Duplication: K1 already has rehearse_v2.py, rh_transport.py, rh_mounts.py, rh_coverage.py, audit_config.py (REF/trinity-3-30/k1_ops6/src118/build); evalx has the whole-worker CPU rehearsal with trace coverage (order 20261115T024906). Brief names only trace_runtime.py.
- IO/legality/provenance/running jobs: no weakening found (bwrap --unshare-net + tmpfs /data2 verified working on trinity-3-30). Brief paths all exist.
