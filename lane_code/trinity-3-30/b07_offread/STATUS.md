# b07_offread STATUS (Devin lane on trinity-3-30; updated 2026-11-16 17:36Z)
Goal: official read kit (briefs/qs/07_official_native_kit.md): benchmark {revsi999t32 (first), vsibench5130} x export {step544, done:<init-rule D0>} x reader {direct, harness:<P8 freeze sha>, e2e:<b04 manifest sha>}. Summary for readers: L/out/OFFICIAL_KIT_READY.md; record distill_design/OFFICIAL_READ_KIT_B07_20261116.md (INDEX line added). L=/scratch/jjyeung/orch_n30/b07_offread, B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30, PY=/scratch/jjyeung/envs/p1cpu/bin/python.

## Current pieces (all tests rerun by me)
- offkit L/kit/offkit (binding, frame guard, aggregation, labels, adapters): bind bd74a97f, report 2656c053, frames 2ed9fcc1, adapt_native 8b90fdcb, adapt_direct 667b19b9, spec 539a67a3; 59 tests (`cd L/kit && $PY -B -m pytest -q -p no:cacheprovider tests/`). Reviews review_offkit + review_offkit2: all fixes applied; residual R1 (unkeyed binding self-hash) accepted non-blocking. Builds R and N pin offkit by hash: any offkit edit needs both re-pinned (pattern L/builds/BRIEF_REPIN2.md).
- Build R (direct re-bind; READY): L/builds/R/out/REBIND_READY.md; package_vsi.tar 03dcb73703051ffba062f136d43b14a6ab253e0552ca343b1826f5227dafbd25, package_revsi.tar 7c81383d288f84cee397fc25a39ec94b0e643cba936860e0ed0f76dbbbfe6e74 (gzip); 37 tests (`cd L/builds/R && $PY -B -m pytest -q -p no:cacheprovider tests/ --basetemp=/dev/shm/b07_n4/<fresh>`); reproduces 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4]. A D0 read needs the init-selection JSON (fields: selected_sha256, selected_step 200..1000 equal to the .done object, init_rule_sha256 d53f9c1a..., d0_ended{reason,event}) from the init-rule owner after D0 ends.
- Build N (native worker, harness = C8r, e2e = b04 snapshot vendor/b04_54dce738597e; NOT READY: owner inputs): L/builds/N/out/NATIVE_KIT_READY.md, OPEN_INPUTS.md; code.tar 06731cfaf8ca5c2c454d2e3a6f136fcd01d5102ca6acf18527b6039403c3e8ea; 113 tests, 112 pass (`cd L/builds/N && $PY -B -m pytest -p no:cacheprovider kit/tests --basetemp=/dev/shm/b07_n4/<fresh> -q`); the one failure is the reviewer's R4 case, which appends the retired export argument itself (sibling test covers the current argv). Review review_offnative: fixes 1-6 applied (prompt indices, unserved budget, e2e proof, reduced proof, naming, VSI sharding). Job names a15_cot_ap + 16 hex; in-job names are random tokens (maps pinned in each kit's out/). ReVSI dense G3T: official 64-frame clips subsampled to the 32 anchors (mapping aaa9a53b; hf_metadata/sampled_video_frame_idx.json). Identity proof reduced (170056 distance masks lost).
- Mirror (latest): trinity-1-18:/scratch/jjyeung/n30_mirror/b07_offread/b07_mirror_N5_1646Z.tar sha 9d3e6c6acf9894522dc169d0c4318aa0052827f096b547b446f8defb0149a178.
- VSI media: 288 videos on Orchard, sizes in L/work/VSI_MEDIA_SIZES.json (folded into build N).

- Re-review review_offnative2 (B/events/review_offnative2/REVIEW_VERDICT_OFFNATIVE2.md): GO AFTER FIXES F1 (R direct chain's interpreter path under the non-/dev/shm name mapping: blocks every direct read on Orchard; build R is NOT launchable until N6 lands), F2 (dataset words in in-job bwrap argv), F3 (VSI shard scene cost). Gate tests: B/events/review_offnative2/review_offnative2_tests/. QUESTION incob_names_and_stream_priority posted 17:35Z (defaults: in-job file contents exempt; streams stay at priority 100).
## In flight
- Codex Astra N6+R4 (F1-F3 + residuals: --export syntax, --account/--no-requeue, child logs, test bypass): brief L/builds/BRIEF_N6.md; run dir /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T173117Z_b07_n6; scratch /dev/shm/b07_n6. On landing: rerun both suites and the reviewer's three (basetemp /dev/shm), check job names still a15_cot_ap, mirror to 1-18, RESULT asking the re-review of F1-F3 (cc cont_ops: build R direct reads blocked until then).
- Governor streams (tier 3, priority 100; launcher L/work/stage_rv/launch.py; STATE.md /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md), both waiting (positions 5-6 at 16:43Z):
  rvA2 (scan; no media to disk): /data2/.../external_benchmarks/revsi/{32_frame,64_frame}, 302 interleaved pairs (LIST_A2.json) -> scan_check.py -> L/work/stage_rv/A2_RESULT.json (sha256+bytes of 604 clips, per-video pixel check; all_separated must be true). Log A2.log.
  rvB (push): 41 missing 32-frame clips (a/) + 302 64-frame clips (b/) -> Orchard /project/community/jjyeung/okh7/d46dd56e669a050f/7b5d2192.tar; remote sha/size in L/work/stage_rv/B.remote.out; ledger L/work/ORCHARD_LEDGER.jsonl.
- No tmux, no Codex run, no Orchard job.

## Next steps
1. Poll every 10 min (streams, B/events/b07_offread ORCH files, review_offnative2 verdict, L/inbox).
2. When N6 lands: verify as above; launch the re-review yourself (pattern B/briefs/review_offnative2.md, `bash B/tools/devin_bg.sh <lane> <brief> claude-opus-5-5-high 7200`).
3. When rvA2 ends (A2.log "done A2 0 0 0"): rename streams/b07_offread_rvA2.json to .done.<epoch>; check A2_RESULT.json (n_files 604, all_separated); fold hashes and the pixel check into build N's ReVSI media manifest (Codex pass).
4. When rvB ends: check B.remote.out; one ossh call to list the Orchard tar's members and sha256 them against A2_RESULT.json; rename the record .done.<epoch>; append the receipt to the ledger.

## Rulings in force
- ORCH: ReVSI dense G3T from the 64-frame clips, never on 32 frames (clip32 diagnostic only); the 41 clips are mine to stage; native official reads hold until the P8 freeze (build ahead only); 170056 masks lost, proof reduced; no naming exemption on Orchard.
- 3-30 /scratch is at its floor: add at most 100 MB there; scratch outputs go to /dev/shm or trinity-1-18/1-3. Lane folder is 4.3 GB of mostly test scratch: removal list in L/REMOVAL_CANDIDATES.md for the user.
- Events only for questions, blockers, final results and rotate.

## Read first
This file, B/events/b07_offread/*_ORCH_* (newest first), L/out/OFFICIAL_KIT_READY.md, L/builds/N/out/NATIVE_KIT_READY.md.
