# b07_offread STATUS (Devin successor lane on trinity-3-30; updated 2026-11-16 13:40Z)
Goal: official read kit (queue brief briefs/qs/07_official_native_kit.md): benchmark {vsibench5130, revsi999t32} x export {step544, done:<D0>} x reader {direct, harness:<P8 freeze sha>, e2e:<b04 manifest sha>}. ReVSI ranks first (USER 11-16). Deliver out/OFFICIAL_KIT_READY.md, mirror, RESULT; rotate by 22:30Z.

## Done (lane folder L=/scratch/jjyeung/orch_n30/b07_offread)
- L/kit/offkit (spec, report, bind, adapt_direct, adapt_native, frames) + L/kit/tests: 34 tests pass (`cd L/kit && /scratch/jjyeung/envs/p1cpu/bin/python -m pytest -q -p no:cacheprovider tests/`). Scorer check reproduces 68.77 and 64.94 with intervals.
  sha256: report.py 5331f25e, bind.py 4cafa152, spec.py 539a67a3, adapt_direct.py 667b19b9, adapt_native.py 10b75ff4, frames.py 835057c6 (frame-layout guard: 32 duplicate default = step 544 training; 64 spread needs the export's layout or an override).
- Build R (direct-only re-bind to a D0 export; Codex run 20261116T115717Z_b07_rebind): L/builds/R/out/REBIND_READY.md (sha 97f4d974), package_vsi.tar ddf11fd2, package_revsi.tar ef31d64f; 18 tests + both D0 CPU rehearsals pass. Build R pins offkit bind/report/spec/adapt_direct by hash: never edit those four files.
- Mirror: trinity-1-18:/scratch/jjyeung/n30_mirror/b07_offread/b07_mirror_1235Z.tar sha 0bddb8617a15343d824f9524ae06787d96361375ec85e0bbc5d7b4765788eafe (kit, build R out/tests/RUN/DIFF); local copy L/work/mirror/.
- Events: RESULT checkpoint (12:26Z), RESULT rebind_ready_review_request (review of offkit + build R requested).
- Inputs copied: L/in/{x27 (VSI kit f42aa1a4 verified), kit_revsi, ret_vsi, ret_revsi, c8r, v1c, readk}.
- Build N (Codex run 20261116T123134Z_b07_native, ended 13:00Z): NOT READY. L/builds/N/out/NATIVE_KIT_READY.md; code.tar 044f8113; 24 tests pass (`cd L/builds/N && "$PY" -B -m pytest -p no:cacheprovider kit/tests --basetemp=work/<fresh> -q`; without --basetemp 7 fail by the write guard). ReVSI CPU fixtures pass for harness (synthetic socket) and e2e; VSI not done. SIZING: ReVSI harness >= 2.26 H100-h before SAM/unserved terms.
- Review review_offkit (events/review_offkit/REVIEW_VERDICT_OFFKIT.md): GO AFTER FIXES, 6 fixes. Fixes 1-5 done in L/kit_v2/offkit (label_report(report, binding=, arm=, role=) verifies the binding and matches reader kind/benchmark/arm, prints MODE/FRAMES/BINDING; bind(frames=(count,layout), frames_override_reason=) embeds bind_frames output; production needs ledger; init selection needs init_rule_sha256 d53f9c1a, selected_step in m200..m1000 matching the .done object, d0_ended{reason,event}; frames.bind_frames has no caller export_layout; adapt_native refuses scripted arm and script rows). 49 tests pass in L/kit_v2; the reviewer's 7 refute tests now fail (defects gone). NOT yet copied over L/kit (N2 imports L/kit while it runs).
## In flight
- Codex Astra build N2 (finish N in place: production stager from R, C8r real decoder + SAM 3 proposal/cache bridge, in-job proof, opaque bootstrap, governed fetch, watchdog, --g3t-source, production-CONFIG rehearsal, then VSI): brief L/builds/N/BRIEF_N2.md; run dir /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T130549Z_b07_native2 (final_message.md on finish); dispatched 13:05Z; liveness: pgrep -f b07_native2.
- No tmux, governor stream or Orchard job.
## Next steps
0. When N2 ends: copy L/kit_v2/{offkit,tests} over L/kit; dispatch Codex for build R fix 6 + adaptation (rebind.py: verify OFFKIT_PINS at run time, drop m100 at rebind.py:86, label_report(binding=b), rehearse.py bind with ledger, re-pin, rebuild packages); dispatch N3 (adapt N to the new offkit API; --g3t-source original with a clip-to-source-video mapping per ORCH 1307Z, clip32 diagnostic only); then RESULT asking re-review of fixes 1, 2, 5 (and 4, 6 for build R).
0b. ORCH 1307Z: stage the 41 extra ReVSI videos myself: find sources from REVSI_DIRECT_STEP544_20261115.md / kit ea1a1b2d video root and main's ReVSI dataset root (named paths only), upload through a governed stream; missing ones listed with item counts.
1. Poll N2 every 10 min. On finish rerun its tests, read NATIVE_KIT_READY.md critically (answer-conversion paths, denominators, labels, proof, opacity of packed bytes).
2. Write L/out/OFFICIAL_KIT_READY.md (reader x benchmark x export matrix, hashes, H100-hour estimates, open inputs) and a distill_design record + INDEX line.
3. Mirror builds/N (code.tar + out, under 5 GB) + kit to trinity-1-18:/scratch/jjyeung/n30_mirror/b07_offread/; final RESULT with review request for build N.
## Open questions / defaults
- QUESTION native_inputs (13:08Z): ReVSI G3T source (default clip32, labelled deviation), 41 extra ReVSI videos (default open input), SAM 3 Orchard location (default from K1 staging).
- Init-selection JSON: ORCH says take it from b01_d0guard / distill_design/NEXT_LEG_INIT_RULE_20261116.md (item 7: chosen after D0 ends and its candidate reads pass). It does not exist yet (D0 job 170111 runs); build R waits ready. bind_export needs a JSON with `selected_sha256` equal to the .done sha256 (and optional `label`).
- Review: lane review_offkit reviews offkit + build R; verdict at events/review_offkit/REVIEW_VERDICT_OFFKIT.md. No read uses offkit before GO.
- ORCH 1228Z: no checkpoint RESULT events; events only for questions, blockers, final results, rotate.
## Read first
This file, events/b07_offread/*_ORCH_*, L/builds/R/out/REBIND_READY.md, L/builds/N/BRIEF.md.
