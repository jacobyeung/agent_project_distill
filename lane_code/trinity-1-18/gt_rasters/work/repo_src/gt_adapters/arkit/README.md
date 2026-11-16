# r1313 GT training teacher

This package collects privileged **training-only** Gemini 3.1 Pro SPLIT traces from the fixed answer-free 50,000-question pool. The first prepared source scene is `scannetppv2__104acbf7d2` (297 questions). It does not run student training or benchmark evaluation.

The teacher starts with the question and choices as text. Frame search, boxes, points and masks call the authenticated donor GT methods; Gemini provides reasoning and the inherited verifiers. No SAM3 service or predicted dense geometry is required. Initial inline RGB is not required or claimed. The unchanged renderer tools can return images if the teacher requests them; actual provider inputs and outputs are archived. Student targets retain the 32 authenticated RGB frames and original questions. Students receive no GT annotations at benchmark inference.

## Data and geometry

The immutable scene receipt binds the selected RGB frames, all 32 official `aligned_pose`/intrinsic associations, instance mesh and annotations, source hashes, alignment checks and two small RGB/mask/depth render proofs. Runtime assets live under `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917`; raw scene inputs are preprocessing-only provenance. Providers take scene IDs, frame slots and labels, never question IDs, choices, gold answers or correctness-dependent mappings.

Official source intrinsics are scaled from 1920×1440 to 640×480 by one third. The selected PNG grid is already 640×480, so its additional resize/crop is identity. Geometry uses GT-valid support, not estimated/common-support masking. Grounding projects in source-world coordinates. Returned geometry transforms points and poses together: meters, first-camera origin, +Z gravity up, +Y initial horizontal view, scale one. Official OBB lengths are verified against mesh associations and converted from full extents to donor half-extents; no OBB estimator is used.

The donor uses approximate mesh vertex splats and bounded triangle rasterization, a 0.15m occlusion tolerance, and OBB fallback for annotated instances without faces. Labels use the donor's imperfect synonym matcher. GT points denote visible-instance box centers, not arbitrary landmarks or edges. Frame search can return both temporal endpoints even when asked for one frame. These are privileged reconstructed-source observations, not perfect geometry or guaranteed correct rationales.

## Admission and execution

Use `/data2/jjyeung/envs/planner/bin/python -B` with:

```sh
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME=/data2/jjyeung/cache/huggingface
export HUGGINGFACE_HUB_CACHE=/data2/jjyeung/cache/huggingface/hub
export TORCH_HOME=/data2/jjyeung/cache/torch
export PIP_CACHE_DIR=/data2/jjyeung/cache/pip
export GP_NATIVE=1
```

`audit_package.py seal --output <new-off-git-contract.json>` creates a fresh source authority. `collect.py bind` requires that contract and its SHA, a pinned registry, the normal fresh collection lease, and the fixed production root `collection_gt_r1313`. Use `--episode-limit 1` for the pilot, then a newly bound unlimited config over the same root to extend the ready subset. `collect.py start --config <config> --workers 1` starts collection; `readiness` is offline, and `set-workers` changes the inherited pool target at claim boundaries. The parent owns paid launch after bounded implementation review. No credential is printed or stored in a config.

The collector preserves native requests, response chunks, exposed thoughts, usage, finish reasons, errors, tool observations, and partial attempts. It refuses existing attempt directories and uses exclusive episode claims with live owner heartbeats. An initial attempt has a16,384-token output cap. Only an offline incorrect-and-capped decision authorizes one32,768-token top-up. `census.py --run-root <run> --output-root <off-git-census>` grades with the pinned offline labels and accepts distinct questions only when native/archive correspondence, answer correctness and successful perception before a later provider turn all pass. Rationale faithfulness is not certified. Synthetic fixtures are not production training examples.

## CPU/offline validation

`validate_package.py --output <new-task-validation-dir>` runs source/donor checks, CPU GT routing and alignment checks, inherited archive/scoring tests, admission negative cases, and real runner fixtures. Only the Google network methods are replaced by fixture responses; native schema conversion, LangGraph, GT providers, archive capture and claim/heartbeat/terminal transitions execute normally. The package's nondeleting coordination functions come from the frozen donor; only optional Git metadata queries are disabled. The live shared lease is parsed read-only; fixture leases stay in isolated task namespaces. Evidence and final closure/census manifests are generated off Git.

`prepare_gt_scene.py` implements extendable ScanNet++ scene preparation. It refuses existing outputs. Use `inspect` to check segment associations and OBB conventions, then `prepare` with an authenticated32-frame receipt and the verified `--obb-lengths full|half`. Each additional scene needs its own raw-source and all32-frame alignment proof; this package does not claim all-scene readiness. No paid teacher episode, accepted-trace yield, or student gain is established by an offline fixture.
