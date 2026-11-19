CPU dry run: PASS. No GPU ran; every R0 head-outcome read remains unspent.
The v2 kit is packaged for review. GPU pricing remains MISSING pending the exact bindings below.

Changes vs v1 (requested comparison):
- R0-dev accepts exactly one K1-selected fallback arm per category; PRIMARY_ARMS and its digest must exist before any R0 pass. Exclusive LOOK creation prevents a second read, including after failure.
- Counting, context/D0, strict/full, da3_f32, source selection and frame-count selection cannot run through the R0 scorer. dev-S1 diagnostics select nothing.
- BARS uses +3 absolute/relative and +5 size/appearance points, with paired lower bound >0. Size requires both replace_box parts, size_screen and the S4 treatment lower bound >-2.
- Direct joins use source_line; both repeated qids remain distinct. The numeric scorer and ReVSI/VSI-Bench mappings implement section 6.
- Appearance ties leave pairs open. Refused size/distance calls retain their present answer. S4 failures refuse metric calls; nonmetric programs use S1.
- K1 tracker jobs cover the pinned train rows; tracker CPU model loading is removed. The first GPU minute checks the predictor, and failure retains the linker.
- R1 reader sources are pinned to the pack. FITS is the exact v2 file (592c2048...); all reported rows label the S4 treatment, with no bound claimed on the reader.

CPU evidence; command: `bash scripts/cpu.sh`.
- Runtime 58.968761 s; peak RSS 563412 KiB; torch 2.11.0+cpu; eight threads, nice 10.
- Join: 1,781/1,781 rows match source_line, qid, question, type and scene. Counts per type are in DRYRUN.json.
- Numeric parity: 678/678 R0-dev and 300/300 dev-S1 stored scores match.
- All programs execute on two K1 train captures: arkitscenes/41125837 and scannetpp/067e2e4e61. GT appearance, option matching, refusal/fallback, and cached StageOne replay pass.
- Trace parses: 279/279 R0-dev and 150/150 dev-S1; the staged r0rel pattern is fixed. This reads parsing outcomes only.
- Scene 04d0dc245b: all 94 PNG hashes match the chained manifest. All 98 scene layouts have 32 anchors, 64 secondary frames and a 94-frame union.
- Missing PRIMARY_ARMS and a repeated category read both fail in isolated synthetic tests. No production LOOK exists.
- Track featuriser: candidates_argmax on a synthetic track from a stored train cache; no tracker accuracy/count was measured.
- Regression checks: 29 PASS; command: `CUDA_VISIBLE_DEVICES= PYTHONPATH=code nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/checks.py` (thread limits as scripts/cpu.sh).
- K1 job census: 1,037 registered rows, 209 captures, 770 capture/name jobs. Command: `PYTHONPATH=code /scratch/jjyeung/envs/p1cpu/bin/python -c "from k1_track import jobs; j=jobs(); print(len(j), len({x[0]['capture'] for x in j}))"`.
- dev-S1: 450 skipped (150 each counting, size, relative distance), zero frame-bound items. Command: `CUDA_VISIBLE_DEVICES= PYTHONPATH=code nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/diagnostics.py`.

Copied-tree edited lines (R1 pack/base-tree comparison; full text: EDITED_LINES.patch):
- e2e_reader/geometry.py: 18, 48; e2e_reader/stage1.py: 116, 126–128, 136, 138.
- student_pilot/routed_candidates.py: 69, 76, 87, 93, 95, 191, 196, 215, 220, 231, 235; routed_features.py: 86, 88.
- student_pilot/scene_state.py: 27, 33, 37, 44; geometry_profiles.py: 83, 123, 143.
- student_pilot/tower_read.py: 67, 74, 85–89, 95, 109, 160, 204, 209, 272–274, 294.
Command: `PYTHONPATH=code nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/prepare_v2.py`. IMPLEMENTATION_DIFF.json also gives exact v1-to-v2 implementation spans.

Prepared GPU commands, unexecuted. Each requires GPU, a staged /scratch PYTHON, GO_FILE and the authorized local GPU ledger; each uses vnice.sh. One 48 GB card per part; actual memory peaks are MISSING.
| Commands from this workspace | Estimated GPU h | Cumulative hard stop h | Memory |
| --- | --- | --- | --- |
| `bash scripts/gpu_k1_track.sh` | 1.3 | 1.75 | 48 GB |
| `bash scripts/gpu_r0_g3t.sh`; `bash scripts/gpu_r0_sam.sh` | 3.0 shared | 3.5 shared | 48 GB |
| `bash scripts/gpu_track.sh` | up to 3.0 | 3.25 | 48 GB |
| `bash scripts/gpu_T94_g3t.sh`; `bash scripts/gpu_T94_sam.sh` | 2.8 shared | 3.0 shared | 48 GB |
| `bash scripts/gpu_s1_g3t.sh`; `bash scripts/gpu_s1_sam.sh` | 2.0 shared | 2.0 shared | 48 GB |
| `bash scripts/gpu_s1_track.sh` | 1.0 | 1.0 | 48 GB |
Admission includes the other two kits and refuses used hours plus the part stop above 16 h. A lease and local lock prevent double spending. DONE hashes skip valid finished units; interrupted reservations require review.
Cut order: dev-S1, track size/relative, then added views. Cuts cannot change a frozen arm; its whole category must remain unspent. R0 track/T94 run only when the frozen arm needs them.

Remaining bindings and deviations (MISSING never means zero):
- config/KBOX_RULES_HOOK.json is unbound. The sibling /scratch/jjyeung/orch_n30/sb_kbox2/out/box_ladder/DECISION.json has MISSING bars; its recorded deployed replay is 4/5 against >=0.95. The hook owns fusion, object grouping and stage-1/track pricing.
- inputs/KBOX_DECISION.json and inputs/TOWER_DECISION.json are absent: no completed normalized K1 box/screens, 32-frame treatment, or views-pay decision was supplied. PRIMARY_ARMS is intentionally absent.
- inputs/K1_TRACK_EVIDENCE.json is absent, and out/object_route/K1_TRACK_CHOICE.json says MISSING. The GPU tracker did not run; paired pricing awaits KBOX_RULES_HOOK.price_k1_tracks. Counts decide nothing.
- inputs/DEVS1_STAGING_PLAN.json is absent. inputs/local/DEVS1_REQUEST.json pins a plan SHA256 but supplies no filename/item binding. No mapping, scene list or frame was invented.
- inputs/GPU_LEDGER.json is absent. No cross-kit hours or exclusive lease was assumed; all GPU entry points refuse admission.
- Full source/box/form dev-S1 metrics and confident object counts await frame binding and the sibling object-source interface. They remain MISSING.
- The CPU PASS proves section 7 execution and contracts, not sibling parity, GPU compatibility or route accuracy. Official items and K1 held-out outcomes were never read.
- External mirroring, RESULT publication and R0DEV_LOOKS.md writes remain with the orchestrator because this task forbids network and external writes. Each future LOOK carries its ledger line.

Artifacts: out/REPORT.md, out/DRYRUN.json, out/GPU_NEED.json, out/sb_kobj2.tar and out/sb_kobj2.tar.sha256.
Package command: `CUDA_VISIBLE_DEVICES= PYTHONPATH=code nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/package_v2.py`; verification: `sha256sum out/sb_kobj2.tar`.
ARCHIVE_MANIFEST.json pins every packaged member; PACKAGE.json records the archive SHA256 and verified member count. JSON outputs carry input hashes. The archive excludes v1 outputs, weights and image caches.
The changes-versus-v1 prose is retained because the task explicitly requires it.
