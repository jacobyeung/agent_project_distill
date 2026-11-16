# VSTI-450 native read of the step-544 student with camera calls served (design record, 2026-11-16)

Lane native_r4 (trinity-1-3). Lane folder `/scratch/jjyeung/orch_n30/native_r4`; events `EV/native_r4/` (`EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`).

## Question
Does the step-544 student, reading VSTI-450 v3 end to end with only its camera calls (move, turn, pose) served by the frozen pose tower inside generation, lift the camera types and the VSTI primary above the direct-answer models and the closed-model bars, and what do its refused non-camera calls cost?

## Answer
Pending: the kit is built and CPU-rehearsed; no GPU read has run. The read is legal before the re-freeze because only camera calls are served (frozen public G3T run on the read's own frames, with step-544's own depth for scale and its gravity head); the object selector, fitted on all 44 VSTI rooms, is never loaded.

## Evidence
- Items: VSTI-450 v3 (`agent/vstibench_repr_450_v3.json` of the main repo, sha d7c16986...): 9 types x 50, 311 ScanNet val scenes. Camera types: camera_displacement and camera_movement_direction (50 each, 86 scenes); no rotation type exists in VSTI.
- Frames: the comparator reads' prepared 32-frame sets (rgb32-selection-v1, linspace indices, 24 fps, av 15.1) under `/data2/.../student_diagnostic_pilot_20260918/eval_instructed_provisional_e3e9ffb/artifacts/paper_eval/vstibench_repr450_v2/prepared/generation/frames` (312 scenes; all 311 v3 scenes covered). They were decoded from the VSI-Bench copies of the videos (scene0011_00 sha b25ed6f0 vs VSTI release 6c8831ee); a five-scene release-video check found equal frame counts and indices (so the same frames) with re-encode noise only: 0/160 bit-identical, mean absolute difference 1.5-2.6, PSNR 33.6-41.3 dB (`EV/native_r4/RELEASE_CHECK.json`).
- Comparators on the same 450 items (other models): f17 primary 66.95 (camera displacement 36.6, direction 50.0), P1 m200 68.71 (39.6, 66.0); Orchard `official_reads/scores/`. Closed models: nine-type mean 83.33 / 82.29, VSTI primary 73.73 / 72.65 (`MEM/closed-model-bars-20261111.md`).
- Scorer: Orchard official `score_and_aggregate.py` (MC fuzzy + exact match; numeric MRA .5:.95:.05) and the main repo's five-subtask collapse; the kit's port reproduces 66.95 and 68.71 from the comparators' recorded answers (`builds/01_vsti/out/SCORER_CHECK.json`).
- Decode rates from the dev-S1 native read (`EV/native_r2/20261116T0515Z_RESULT_decode_times.md`): camera displacement 6.0 s, direction 7.3 s per item on one H100; frozen G3T 3.8 s per 32-frame scene, ~10 GB peak.

## Options considered and rejected
- Full VSTI test set (5,736 items): 15-115 GPU-h; the closed-model bars are on VSTI-450.
- Serving object calls on VSTI: illegal before the re-freeze (selector fitted on all 44 VSTI rooms).
- A direct (unserved) arm: on dev-S1 it was no direct-answer baseline (unserved calls force-close) and would double the decode time.
- Release-video frames: would break item pairing with the f17 and P1 m200 reads; kept as a pixel check instead.
- Trinity cards: no 48 GB card with disk at 08:00Z; Orchard general is the primary venue, Trinity the fallback.

## What might not work, and how we would notice
- The student calls ground or depth tools on camera-object types; refused calls without trained recovery may score zero. The report gives, per type, the items with a non-camera call, their answers after the refusal and their score.
- The scale/gravity path: V1b calls C8r's factored preparation and is bit-identical on CPU with synthetic heads; the in-job proof compares prepared geometry with job 170056 on the GPU.
- 321 inherited C8r lines on the dev-S1 proof path run only on Orchard (unchanged bytes that ran in job 170056).
- A time-limited job ends before the 350 non-camera items; camera items run first and a second job resumes.

