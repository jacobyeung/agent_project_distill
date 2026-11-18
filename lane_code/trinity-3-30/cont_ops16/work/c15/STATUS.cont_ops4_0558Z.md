# cont_ops4 STATUS (trinity-1-3; updated 2026-11-16T05:58Z; successor: read this, then the newest *_ORCH_* and RESULT events)
Lane folder /scratch/jjyeung/orch_n30/cont_ops (shared with predecessors). Ledger work/ORCHARD_LEDGER.jsonl. Python: /scratch/jjyeung/envs/p1cpu/bin/python (system python3 is 3.6). A command guard blocks command text containing deletion or shrink verbs (rm, truncate): write such text with the write tool. Orchard login /tmp is a full tmpfs.

## Job 1: LEG-S1 continuation (545-1000)
- PACKET READY; waits for *_ORCH_GO_submit.md (the user's yes). Card PRELAUNCH_CARD_CONTINUATION.md (command section 3; on GO section 11; scancel on a rule-E alarm authorized at GO). Token a15_cot_ap0b0c99e1. Nothing submitted. Its submission floor: project free >= 150 GB (171 GB at 03:20Z); D0 B's end slot (113 GB) would leave about 58 GB.

## Job 2: D0
Rows v5 (4af43b40, 152,123 rows) admitted; my independent read AGREE (RESULT 0141Z; events d0_tools/v5read). Orchard: okh7/e31b18bf254e12ef/r.sqlite, r.json 46c734ef (local work/d0/a2/r_v5_orchard.json). Card PRELAUNCH_CARD_D0.md (events) carries v5 numbers (old copy work/PRELAUNCH_CARD_D0.v4.md).

### Job A2 = Orchard 170109 (a15_cot_apb0d53e76), general, 64c/800G/6 h, RUNNING since 03:28:13Z on orchard-community-2 (limit 09:28Z)
- STAGE 1 PASSED 05:43:50Z (RESULT 0552Z; files events a2_170109/ and local work/d0/a2/a2res/): VQA 152,123 admitted, refused 0 (route planning 8,894 admitted); routing 47,732 (route planning 0; ROUTE_direct deferred 10,458); scene exclusions PASS; prepare 3,132 s, frames 3,352 s. GCS q8/7c31288e/170109a.tar sha 1eb7df4f.
- STAGE 2 running since 05:44:05Z, cap 10,449 s (ends by ~08:38Z), but 2 rank processes at a time (nproc honoured OMP_NUM_THREADS=16; fixed locally in work/d0/a2/s2.sh for any rerun, deployed copy s2.r12_deployed.sh). Ranks 0,1 first; 2,3 likely not measured.
- WATCH (every 10 min): `timeout 300 bash <tools>/ossh.sh 'bash -s' < work/d0/a2/w2.sh`. When o/170109.s2.json lands (or the job ends): fetch it (+ s2.steps), decode families with work/d0/a2/famdecode.py, RESULT with per-rank rows by family, loss terms, finiteness, wall time, peak memory. CANCEL RULE (ORCH GO 0335Z item 2): if any rank stage 2 measures raises or gives a non-finite loss -> `scancel 170111` (job B) before it starts + BLOCKER. A rank not finished = not measured, cancels nothing. Note s2.r*.log tracebacks may contain row text: do not copy them into events; summarize.
- Kit x_8417c021 (PREPARATION_ONLY, config 5e40bb5e, identity e757f64a, manifest 17784778, ANON_OK 14e927f3 CLEAN from r12, a.py PASS); run fdca77e7, root r/4d3cd40e. Job files i_bb09a77d/a3/ (ja2.sh d12d72dc, fam.py a8f8d7d8, s2.sh f270a63e, s2.py 1514daba, s2sum.py c35dbce4); superseded i_bb09a77d/a2/ job files are unused. Local: work/d0/a2/v5a2 (derivation), v5a3 (job files, ANON_OK_A2.json, submit_a2.sh/out).
- Stage 1: vt.py, b/r.sh p 0, census o/170109.fam.json (family codes: decode on Trinity with work/d0/a2/famdecode.py), status o/170109.s1.json, GCS gs://cmu-gpucloud-jjyeung/q8/7c31288e/170109a.tar. Stage 2 (only if stage 1 passed and was published): 4 rank processes, cap <= 3 h, summary o/170109.s2.json (s2sum), logs o/170109.s2.r*.log, o/170109.s2.steps, GCS q8/7c31288e/170109b.tar. Job exit = mode p's code.
- Watch script work/d0/a2/w1.sh (via ossh). RESULT owed: admitted/refused per family (decode), routing materialization (route planning dropped), resources; stage 2 per-rank statistics. If A2 stage 1 or 2 fails: tell ORCH (B must be cancelled before it starts).
- Notice to main: distillation_orchestrator_20260918/INBOX_TO_NONTRAINING_ORCHESTRATOR_20261116T0328Z_distill_d0_job_a2.md.

### Job B = Orchard 170111 (a15_cot_apddbe32d7), advanced 4 GPU 24 h, PENDING (submitted 03:39Z under ORCH GO 0335Z; estimate start 2026-11-16T22:51Z)
- Kit x_f5c353f7 READY (config d6827df0, identity 80f4af94, contract aaf2d7b0, manifest 231c98dc = reviewed fixture except launch READY fields; ANON_OK a9ad5b5e CLEAN; a.py PASS; sess.json 600 installed). Run 359fcc3c, root r/63e57182 (absent; the wrapper creates it). Bundle i_bb09a77d/b5/ (over 70bbb61e, 4.json 3f64925a, review.json ddd34ff2, staging.json 133bffea, jb.sh 3b8f0162 with the GCS slot fallback to q8/d2d30e36/359fcc3c_s<step>.tar, exit 6, o/<job>.SLOT_TO_GCS).
- GO 0335Z (events): scancel without asking on a step 1-3 alarm (pose/VQA/pointing loss outside m544's 530-544 range; routing exempt), on admission refusal or failed first-step gate -> BLOCKER with last lines. Cancel B before start if A2 stage 1 fails or any stage-2-measured rank raises or is non-finite (not measured cancels nothing). Stop rule distill_design/D0_STOP_RULE_20261116.md (reads decide; stop only on ORCH word).
- Submitted with: `cd /project/community/jjyeung/okh7/i_bb09a77d && TZ=UTC env -u TK_JOB_START sbatch -J a15_cot_apddbe32d7 -o /dev/null -e /project/community/jjyeung/okh7/x_f5c353f7/o/%j.err b5/jb.sh`. Ledger line and notice to main written. When it starts: watch steps 1-3 against work/BASELINE_530_544.json (routing exempt), scancel on alarm if the GO authorizes.
- Export sessions minted 2026-11-15T23:19Z (assumed expiry 2026-11-22T23:19Z): never put a session URL in an event or log.
- Packet D0_JOB_B_PACKET.md (events; source work/d0/jobB/). Local build work/d0/a2/v5b (orch records in v5b/orch).
- Mirror: trinity-0-13:/scratch/jjyeung/n30_mirror/cont_ops/mirror_d0_v5.tar (sha256 69cea70f; local build without session files).

- Card corrected 0342Z; READS_PLAN_D0.md (events): exports q8/8865619b/359fcc3c_m100/_m200 (4 parts), .done receipts in x_f5c353f7/o; sessions assumed valid to 2026-11-22T23:19Z: re-mint (work/d0/jobB/mint.py) if the second allocation cannot start by ~2026-11-21T12:00Z.

## Reviews (Codex Astra, review preset; prompts in work/review_input/)
r10 (A2 and B GO AFTER FIXES), r11 (B fixes FIXED; A2 three open), r12 (A2 GO). Copies in the events folder.

## Notes
- ORCH rulings this session: 0059Z two-stage A2; 0126Z no placeholder reservation, GCS slot fallback; 0128Z row metadata strings accepted for D0 (no Orchard output may print pool/rule/source values; fam/s2sum print digests only), v5 admission.
- Removal candidates (REMOVAL_CANDIDATES.md): work/d0/a2/dry_v4*, dryb_v4, dry_v5*, t_s2, t_fam, t_gslot, v5b/r10_superseded, v5a3/r11_superseded; Orchard i_bb09a77d/a2/{ja2.sh,fam.py,s2*.py,s2.sh} (unused), i_bb09a77d/jb/.ftest absent (never created).
