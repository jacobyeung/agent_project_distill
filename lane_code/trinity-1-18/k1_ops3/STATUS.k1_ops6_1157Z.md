# k1_ops STATUS — operator k1_ops6 (Claude, trinity-3-30), successor k1_ops7 (Devin, trinity-1-18). Events folder events/k1_ops3/.
Updated 2026-11-16T11:57Z (k1_ops6). Read this section first; the older sections below are predecessor history.

## State in one paragraph
Own-phase job 170206 FAILED at 10:46Z (52 s into capture 1). Root cause: the Part B stage_job.py never staged CONFIG assets.depth (step_400 heads.json/heads.safetensors/encoder.safetensors), so read_runtime.load_model -> carrier_c1_run.py:782 -> carrier_c1.py:692 load_depth_stage1 -> p3_provenance.py:42 pinned() raised. FIXED in batch d1553118 (5 added lines; diff below), rehearsed on 1-18. GO conditions (a) and (b) of the k1_ops6 brief are MET (RESULT 1156Z). NOT SUBMITTED: Orchard general is held by VSTI job 170228 (native_r5, submitted 11:45Z, time limit ending by 16:30Z; ORCH order: VSTI before K1). No K1 job is running. No card held.

## Evidence and files
- Diagnosis: events/k1_ops3/DIAG_170206_k1ops6.md; RESULT 1117Z (root cause), 1122Z (general free / Orchard picked), 1156Z (fix rehearsed).
- 170206 returns (both FAILED): Orchard pool /project/community/jjyeung/okh7/b7e31d84a90c62f5/170206/{a8598721c7ff9494c,e99ce848d0e2649b6}/ (also GCS q8/b7e31d84a90c62f5/r/<token>/). Dump: trinity-3-30:/scratch/jjyeung/orch_n30/k1_ops6/work/ret170206_dump.txt. Pool has NO a.json pointer (never advanced) -> next job starts clean. a.lock is an flock file (harmless).
- Static closure audit: trinity-3-30:/scratch/jjyeung/orch_n30/k1_ops6/audit/{closure_audit.py,closure_as_built.txt,closure_with_depth.txt}: 423 pins reachable from config/receipt/artifact/model.json/export JSONs; only the 3 depth files were staged by C8r but not by K1; with depth staged, 0 gaps vs C8r, 0 sha differences.
- Fix diff (embedded stage_job.py, 0c9c9ce2 -> d1553118): events/k1_ops3/STAGE_JOB_d1553118_k1ops6.diff. Inserted after the base inventory check:
    for index, item in enumerate(assets['depth']):
        target = NS.physical(root, item['logical_path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        records['depth_' + str(index)] = NS.copied(item, target)
  (identical to C8r orchard_native/native_stage.py:470-473).
- Workspace: trinity-1-18:/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7 (copy of build/ without evidence/rh/out; stage_job.py patched; harness-only patches rh_batch_fixture.py + stage_fixture.py; inputs/depth_heads.json = real heads.json fd60ac2f; inputs/anchors.tar = HARD LINK to /scratch/jjyeung/k1/partB/k1_partB_anchors.tar, never modify).
- Batch d1553118: build7/packet/a7e31d84.sh, sha256 d1553118c4fb8773532979fd6016bca1ce2363bac8c5bcfede939d43db29bcd4, 1,377,481 B; second copy trinity-3-30:/scratch/jjyeung/orch_n30/k1_ops6/work/a7e31d84.d1553118.sh (sha checked). Payload vs 0c9c9ce2: only stage_job.py changed; a.json byte-equal; CONFIG.json sha 044829211f3444fb... unchanged; bundle d6e92a81.tar e9ffe4ae unchanged (already on GCS, gen 1794820770137604). a.json: allocation_seconds 10800, no deadline_unix, capture_reserve 3000, return_margin 900.
- Rehearsal evidence (build7/evidence/): B7_MAPPED.log (9/9 cases pass, run batch_018d4bdafa), B7_DEPTH_MAPPED.log, B7_NSDEPTH_MAPPED.log (in-namespace pinned(depth_init) passes), out/RESULT.json + out/batch_diagnostic.log (namespace mode via outer bwrap as r5: v2 prepared check pass, success pass with 2 returns, deadline fails on the known EXDEV harness artifact, system-python batch fails as expected, mounts pass), B7_PAYLOAD_DIFF.json. Driver scripts rh7.sh, rh7b.sh, rh7c.sh, rh7d.sh; check scripts depth_check.py, ns_depth_check.py, payload_diff.py.

## GO (ORCH brief k1_ops6 + note 11:25Z): one resubmission, Orchard general OR a Trinity card
- (a) RESULT with root cause, fix diff, rehearsal: MET (1156Z). (b) fix touches no scoring/selection/manifest/pinned input/admission code: MET. (c) general order: ORCH RULING 1102Z — VSTI (job 2) before K1 (job 3); from 17:30Z nothing new on general; K1's limit = need + margin and must END BEFORE 17:45Z; check `squeue -p general` just before sbatch and record it in the RESULT.
- Need (measured in 170206): staging 308 s, model load ~50 s; per-capture own time NOT measured (prefill-only; estimate 5-20 s -> 300 captures 25-100 min). The canary return after 3 captures gives seconds.

## NEXT STEPS (successor)
1. Watch VSTI 170228: `TZ=UTC squeue -j 170228` via tools/ossh.sh at most every 10 min (every 1 min near its end). Do not submit while any job of ours is on general.
2. When general has no job of ours:
   - If now <= 14:40Z: submit d1553118 unchanged with --time 03:00:00 (ends before 17:45Z).
   - If now > 14:40Z: do NOT shorten --time alone (budget comes from a.json). Use the deadline variant (step 3) with --time = (17:44Z - now) floor to minutes.
3. Deadline variant (needed after 14:40Z): in a fresh copy of build7 (e.g. build7d; cp -rp, never edit hard links), run `/scratch/jjyeung/envs/p1cpu/bin/python -B build_package.py --deadline-unix 1794850800` (= 2026-11-16T17:40:00Z; both budget sites use min(allocation, deadline - started)); record the new batch sha; rerun the mapped rehearsal `bash rh7.sh` (adapt N=) -> 9/9 must pass; RESULT with the new sha. With the reviewed 3000 s capture reserve a post-16:15Z job captures only ~(window - 75 min); lowering capture_reserve_seconds needs ORCH's word (QUESTION pending from k1_ops6 if written; default: keep 3000).
4. Submit (from trinity-1-18 or 3-30): copy the batch to the pool and sbatch the pool copy, one ossh call:
   P=/project/community/jjyeung/okh7/b7e31d84a90c62f5; F=$P/a7e31d84.<sha8>.sh; write via `base64 -d > $F.part` + `mv $F.part $F`; `sha256sum $F` must equal the batch sha; `squeue -p general -u $USER -h | wc -l` must be 0 (print `squeue -p general` for the record); then
   /usr/local/bin/sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=<T> --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_apb7e31d84a90c62f5 $F
   Then at once: RESULT with job id + squeue check; append a line to trinity-1-18:/scratch/jjyeung/orch_n30/k1_ops3/work/ORCHARD_LEDGER.jsonl (utc, token b7e31d84a90c62f5, job_id, batch sha, meaning).
5. After submission: every 1 min `TZ=UTC squeue -j <id>; sacct -j <id> -X --format=State,ExitCode,Elapsed; ls -la $P/<id>/` until the canary return lands (token dir starting 'c' with EXIT.json + result.tar.gz); read metadata/CANARY.json with `tar xzOf <dir>/result.tar.gz metadata/CANARY.json` (small); RESULT with the 3 captures' seconds/tokens + projected end; then lengthen checks to 5 then 10 min; back to 1 min on any regression. Two failed checks on one defect -> BLOCKER, diagnose before any resubmit. A job the cluster killed is never resubmitted without ORCH's word. A FAILED return has metadata/failure.json + native/probe/HALTED.json (read as for 170206).
6. Final return (token 'a...', EXIT status COMPLETE or RESUME with pointer advanced): fetch result.tar.gz via a governed GCS stream (copy work/partb/meta_pull_launch.py pattern; io_governor README; register first; never pv/rsync --bwlimit) into 1-18 /scratch; verify size+sha vs EXIT.json; extract on /scratch; every own capture must pass checked_phase(c, root, 'own') (PHASE_COMPLETE.json + own.npz sha). If RESUME (not all 300), resubmit the same batch on the next ORCH-allowed window (the job restores from the pointer).
7. Downstream on trinity-1-18 (from predecessor notes below, read REFREEZE_AMENDMENT_* in /data2/jjyeung/agent_project_data/distill_design/ first; amendments registered before outputs exist bind): convert (manifest v2 a40fbc19 / sha e684e0c7, tower root /scratch/jjyeung/k1/run_tower_sam_2, own root = extracted return) ; then `MODE=r2 K1_R2_CAPTURE=<canonical> K1_CONVERT_CACHE=<original convert root> K1_REFIT_PY=/scratch/jjyeung/envs/planner_local_v1/bin/python bash work/k1_downstream.sh` (show receipt), then the full `bash work/k1_downstream.sh` (same env, no MODE); tables on the frozen 296-capture set (amendment 1; sensitivity 300); refit under planner_local_v1 (receipt + report state: setlib d9271cc9 is a vendored copy; original setlib and sklearn bundle lost with 2-18; sklearn 1.5.2 is proof_p2's interpreter; proof P2 not run). Never point K1_CONVERT_CACHE at a copied root.
8. Report: RESULT + record under /data2/jjyeung/agent_project_data/distill_design/ (question, answer, evidence, options rejected, risks, tests, status) + one INDEX.md line; give E3's deployed column (command in E3_BACKEND_GEOMETRY_PRICING_20261116.md).
- Trinity alternative (ORCH 11:25Z): not pursued; it needs the pinned venv (8.1 GB) + numpy/FLA (1.1 GB) + depth weights (2.75 GB) through the governor, a new bwrap launcher (venv python links to /usr/bin/python3.12, absent on Trinity; staged Orchard bwrap needs glibc 2.33) and an interpreter substitution (a pinned-input change -> condition (b) fails without ORCH's ruling).

## Copies/removal candidates made by k1_ops6
- trinity-3-30:/scratch/jjyeung/orch_n30/k1_ops6/ (src118 907 MB copy of 1-18 build files, bundle/, meta/, model/, audit/, work/); trinity-1-18 /tmp/k1ops6_tl.py, /tmp/k1ops6_export_list.json, /tmp/k1ops6_tl.err, /tmp/k1ops6_batch.b64; build7/ (rehearsal evidence; 1-18). List: trinity-3-30:/scratch/jjyeung/orch_n30/k1_ops6/REMOVAL_CANDIDATES.md.

## Predecessor STATUS (k1_ops5 and earlier), kept for reference
# k1_ops STATUS (trinity-1-18); operator k1_ops5 (from 05:49Z; successor of k1_ops4, same lane and events folders).

Updated 2026-11-16T10:42Z (k1_ops5). JOB 170206 RUNNING since 10:39:56Z on orchard-community-4 (--time 03:00:00; batch 0c9c9ce2, CONFIRMED by review_k1b4 10:39Z; Orchard batch copy /project/community/jjyeung/okh7/b7e31d84a90c62f5/a7e31d84.0c9c9ce2.sh). RESULT 1041Z sent. WATCH: every 5-10 min ossh squeue + ls pool okh7/b7e31d84a90c62f5/170206/; canary return = a token dir with EXIT.json + result.tar.gz (small); fetch (gsutil cat of the GCS copy if <20 MB, else governed stream), read metadata/CANARY.json, RESULT with 3 captures' seconds + projected end (own phase: 300 captures; reader estimate ~10 s/capture). Final return after clean stop or completion; then convert on 1-18 (manifest v2), R2, k1_downstream.sh. Build 6 notes: batch 0c9c9ce2 (1,377,357 B); 170193 FAILED staging (fixed). Older notes below.
- Codex k1_partb5 DONE-ish (REPORT5.txt; F1-F4 + minor). New batch packet/a7e31d84.sh fc9ed8a8 (2,144,809 B). 1-3 r4 (k1_partb_rh/r4): ro-PROJECT batch 7/7 pass (rh13_out_r4/). RESULT 0825Z fixes_F1_F4 sent with partb/REVIEW_C_k1ops5.tgz (22079a20).
- Workspace work/partb/build is ~19 GB (rehearsal evidence + RH tars): over the 2 GB lane guideline; list in REMOVAL_CANDIDATES.md after the job.
## k1_ops5 state (supersedes "Open work" below)
- Package (workspace work/partb/build): bundle packet/d6e92a81.tar 44,328,960 B e9ffe4ae; batch packet/a7e31d84.sh 446c9c70; manifest v2 e684e0c7 (in amendment 2; copy work/manifest_v2/); config packet/CONFIG.json (pool /project/community/jjyeung/okh7/b7e31d84a90c62f5, cloud gs q8/b7e31d84a90c62f5/r). Job files unchanged by builds 3-4. Token b7e31d84a90c62f5 in work/ORCHARD_LEDGER.jsonl. Second copy of bundle+batch: inside trinity-1-3:/scratch/jjyeung/orch_n30/k1_partb_rh/r3 (RH tar ca3c4533).
- Rehearsals: local evidence/v2_976f8c0488 (+REPORT4 local); 1-3 r2 (rh13_out_r2) and r3 (rh13_out_r3: batch 6 cases pass + rehearse_v2 + real prepared check, namespace executed). k1_partb_rh/ top level = failed run 1, r2, r3 on 1-3 (all mine).
- k1_downstream.sh on v2 (work/K1_DOWNSTREAM_V2.diff; original work/k1_downstream.v1_91a2dbf9.sh).
- IN FLIGHT: governed push k1_ops5_upb7p10 (prio 10, tmux k1bup2, launcher work/partb/bundle_up_launch_p10.py, log work/partb/BUNDLE_UP_p10.log). Old record withdrawn (k1_ops5_upb7e31d84.withdrawn.1794814002, nothing landed). ON END: rename streams/k1_ops5_upb7p10.json -> .done.<epoch>; gsutil ls -L gs://cmu-gpucloud-jjyeung/q8/b7e31d84a90c62f5/d6e92a81.tar crc32c/md5 vs local (gsutil hash -h file); ledger line with generation.
- WAIT: review_k1b2 verdict (events/review_k1b2/) and ORCH GO naming a15_cot_apb7e31d84a90c62f5. Orchard general: D0 170109 running since 03:28Z (6 h limit -> ends by 09:28Z); general = 1 job/user.
- SUBMIT (on GO only): cd work/partb/build/packet && timeout 300 bash <tools>/ossh.sh '/usr/local/bin/sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=12:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_apb7e31d84a90c62f5' < a7e31d84.sh ; ledger job id; then TZ=UTC squeue; canary return appears at pool okh7/b7e31d84a90c62f5/<jobid>/ and gs q8/b7e31d84a90c62f5/r/<token>/ (fetch per build/fetch_command.txt via governed stream).

## Now: OPERATOR of phase own on Orchard (ORCH 0427Z order + 0534Z RULING on four points; read both). Submission waits for ORCH's explicit word (10-65 GPU-h; design review ~06:45Z). Build so the job can go within minutes of a GO.
Open work, in order:
1. [DONE 06:04Z] Metadata pull (needed for the prepared check): governor stream k1_ops4_meta in tmux k1meta, launcher work/partb/meta_pull_launch.py, log work/partb/META_PULL.log; gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/metadata_e10fbb95487f3baf.tar -> work/partb/meta/e10fbb95.tar (67,143,680 B, sha256 e10fbb95487f3bafc379f99ac42668f94ac4c479129d8631d63750112cab3266). Registered 05:39:22Z, waiting (position 1) at 05:41Z. ON END (log line "exit meta"): rename /data3/jjyeung/orch_n13_20261026/io_governor/streams/k1_ops4_meta.json to .done.<epoch>; sha256sum the file.
2. Codex k1_partb2 (Astra high) dispatched 05:41:04Z: brief work/partb/build/BRIEF2.md (implements rulings a-d), workspace work/partb/build/, receipt agent/scratch/codex_runs/20261116T054104Z_k1_partb2 (under /home/jjyeung/agent_project_distill). Do NOT dispatch a second build on this workspace while it runs (pgrep -u jjyeung -f 'codex exec -m gpt-6-astra.*partb'). Expected outputs: manifest_v2/ + make_manifest_v2.py, batch entrypoint + job script, rh/RH_1_3.tar + rh/run_rh.sh, REPORT.txt (rewritten), upload list.
3. After the build: (i) give ORCH v2's sha256 so it goes into /data2/jjyeung/agent_project_data/distill_design/REFREEZE_AMENDMENT_2_K1_MANIFEST_V2_20261116.md BEFORE any own output exists (ORCH ruling a says "write v2's sha256 into the amendment record": write it there yourself, one appended line, if ORCH has not). (ii) Namespace rehearsal on trinity-1-3 (ruling d): ONE IB tar pipe `tar cf - -C <rh dir> . | timeout 1800 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-3.ib 'mkdir -p /scratch/jjyeung/orch_n30/k1_partb_rh && cd $_ && tar xf -'`, then ONE batched ssh `ssh trinity-1-3.ib 'cd /scratch/jjyeung/orch_n30/k1_partb_rh && bash run_rh.sh && cat out/RH_RESULT.tar' > work/partb/rh_result.tar` (or combine both into one call). Check `ip route get` shows dev ib0; df on 1-3 first; write nothing else there; <2 ssh/min. If it cannot be done in 30 min say why; fallback = C8r namespace unchanged + in-job canary, stated as unrehearsed. (iii) Upload the code bundle (and anything else REPORT lists) as governed streams like work/partb/anchor_up_launch.py (push, io-weight 1, tier 3, priority 30; register all at once); ledger tokens in work/ORCHARD_LEDGER.jsonl. (iv) ONE RESULT event: v2 script + its diff, diff vs C8r wrapper, rehearsal output (here + 1-3), lines no rehearsal executes, exempt paths, job-count table, submit command. ORCH orders the reader on it. (v) Submit only on ORCH's GO, via ossh.sh (LANE_RULES "Orchard"), job name a15_cot_ap+hex, TZ=UTC squeue; watch canary return (3 captures' seconds + token counts) and report the sizing.
- Inputs already done: anchor tar on GCS q8/d36acca73f/b09e660d.tar (generation 1794806692483376, crc32c dpOS5g==, md5 vdkDZ6qbYRK7YvIJdI7QrQ==, sha256 1405c09c); first build's source bundle work/partb/build/payload/d64c8e20.tar (cce1a9b6; may be superseded by build 2).
- Rates (events/native_r2/20261116T0515Z_RESULT_decode_times.md): ~0.046 s/sampled token; 16,384 tokens ~780 s/capture ~65 GPU-h ~6 jobs worst case; native read items <=2,175 tokens.
- Then, after own returns: convert (on manifest v2) on trinity-1-18 with tower root /scratch/jjyeung/k1/run_tower_sam_2, then R2 and work/k1_downstream.sh (see below). NOTE: k1_downstream.sh / operator commands use MANIFEST = 91a2dbf9; for v2 they need the v2 path (ruling a: own, convert, tables run on v2) - a one-line change with re-review, flag it to ORCH before tables.

## Created outside the lane folder by k1_ops4 (all add-only)
- 296 rasters under /scratch/jjyeung/orch_cd/dose_pool/out/{t1_gt,arkit_gt}/gt/ (work/RASTER_PLACEMENT.tsv); setlib.py and MODELS.json (work/REFIT_INPUT_PLACEMENT.tsv); mirror trinity-3-30:/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2; GCS q8/d36acca73f/b09e660d.tar; lines appended to REFREEZE_AMENDMENT_1 (frozen GT sets); event subfolders gtset/ and partb/.

## tower_sam COMPLETE (300/300, rc 0, 04:19:38Z)
- Root /scratch/jjyeung/k1/run_tower_sam_2 (3.0 GB), manifest work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json (91a2dbf9). checked_phase ok 300 before and after the gt-set apply (work/TOWER_SAM_RUN2_*.json). GPU 4 released 04:20Z.
- Mirror: trinity-3-30.ib:/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2, 1,205 files sha-equal (work/MIRROR_TOWER_SAM_LOCAL.sha256 sha 7de0a8febe3e251a0e1d9b2df3f8091f953b855730dc6fe7a4ed8fb5fec9ce2f).
- Kit copy kc now carries max-bytes + gt-set builds (apply 04:22:46Z, verify_sources 109; originals work/kc_pre_maxbytes/, work/kc_pre_gtset/). Do not touch kc while any K1 phase runs.
- tmux k1stop2b (stop timer) exits by itself at about 04:46Z without writing STOP (complete event exists). tmux k1gpu2b/k1stall2b ended.
- Events today: 0101Z resume; 0112Z rasters + subset; 0138Z own_phase_on_trinity; 0149Z gtset_build; 0152Z BLOCKER refit inputs (resolved 0220Z); 0222Z refit inputs placed; 0231Z gtset F1/F2; 0424Z tower_sam complete.

## Next after tower_sam
- Rasters PLACED 01:08Z: 296 pin-verified copies at the manifest paths orch_cd/dose_pool/out/{t1_gt,arkit_gt}/gt (work/RASTER_PLACEMENT.tsv, work/place_rasters.py); 4 unpinned absent. Event 0112Z.
- GT sets FROZEN 01:25Z (ORCH GO 0118Z cond. 1): work/gt_sets/GT_SET_PRIMARY_296.json sha 2b82af52..., GT_SET_SENSITIVITY_300.json sha e305c4be... (4 unpinned copies in gt_sets/unpinned/, SHA256SUMS); hashes appended to the amendment record.
- Codex k1_gtset DONE; review_k1g GO AFTER FIXES; ORCH 0226Z: F1/F2 done (RESULT 0231Z) -> apply RELEASED once tower_sam has ended. Steps: (1) bash work/apply_gtset.sh [ORCH order file if tower_sam ended with captures left]; (2) after convert: MODE=r2 K1_R2_CAPTURE=<canonical> K1_CONVERT_CACHE=<original convert root> K1_REFIT_PY=/scratch/jjyeung/envs/planner_local_v1/bin/python bash work/k1_downstream.sh, show the receipt; (3) full work/k1_downstream.sh (same env, no MODE). Never point K1_CONVERT_CACHE at a copied root.
- Refit inputs PLACED 02:21Z (ORCH RULING 0220Z): setlib.py d9271cc9 at orch_cd/grd_selector/work/setsel/, MODELS.json cdf19409 at orch_cd/devs1_masks/out/kit/work/vendor/ (work/REFIT_INPUT_PLACEMENT.tsv). Refit interpreter: /scratch/jjyeung/envs/planner_local_v1/bin/python (sklearn 1.5.2) = K1_REFIT_PY. When refit runs, receipt + K1 report MUST state: setlib d9271cc9 is a vendored copy; original setlib and the sklearn bundle were lost with trinity-2-18; sklearn 1.5.2 is proof_p2's named interpreter; fixture proof P2 not run (bundle + dev tables lost).
- ORCH 0146Z: own stays on Orchard (no Trinity build/copy). Owed in a later RESULT: (1) H100 time for 300 own captures from native pilot 170049 / read 170056 per-item times (on 1-13; answered partially 0149Z: need native_r3 data); (2) answered 0149Z (resume works if root and paths persist, clean --max-seconds stop).
- Kill test per distill_design/REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md: primary 296, sensitivity +4 unpinned (ARKit 41125829, 42899325, 45261532; ScanNet++ ef69d58016).
- Phase own on Orchard: Part B prepared (events PART_B_JOB_DESCRIPTION.md; anchor tar /scratch/jjyeung/k1/partB, not uploaded); waits for ORCH's Orchard operator. Then convert, then CPU kill test.

## History (k1_ops3, kept for reference)
## Predecessors
- No tmux server and no process of k1_ops/k1_ops2 on this node (17:00Z). Nothing under /scratch/jjyeung/k1 changed since 07:50Z.
- k1_ops2 already withdrew the frozen record: `io_governor/streams/k1_ops_t2s_mp4.withdrawn.1794759286` (renamed 16:14:46Z). It wrote no k1 line to REGISTER.md or mover DISCUSSION.md.

## Present on 1-18 (verified)
- T1 code: /scratch/jjyeung/orch_cd/{k1_build,k1_ops,leg_s1_tree,mdg_next,evalx,p2_build,...}; all 1145 files of `orch_cd/k1_ops/work/T1_SHA256SUMS` match.
- T4: /scratch/jjyeung/k1/g3t/model.safetensors + config.json, sha256 match (T4_STATUS.txt).
- SAM 3 weights /scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt sha 9999e234 OK; sam3src present; step-544 artifact JSON 1d6eeb28 OK.
- Kit: /scratch/jjyeung/orch_cd/k1_build/work/kit_k1a. verify_sources.py: 108/108 pins OK. native_kit test_kit.py 19 OK, test_guards.py 7 OK (logs work/logs/).

## T2 (not delivered; /scratch/jjyeung/k1/src is empty)
- 138 mp4 (51 ScanNet d1, 87 ScanNet++ d2), 2,897,231,394 bytes, list `orch_cd/k1_ops/work/MP4_LIST.txt` (paths relative to /), pins `D12_MP4S.json` (sha, bytes). All 138 sources exist on /data2 with the pinned sizes.
- Command: `tar cf - -C / -T MP4_LIST.txt | pv -q -L 8m | tar xf - -C /scratch/jjyeung/k1/src`; verify `verify_mp4.py D12_MP4S.json /scratch/jjyeung/k1/src`.
- Then decode (local CPU): `wd.py D12_DECODE_MANIFEST.json.gz D12_DECODE_CONF.json /scratch/jjyeung/k1_frames WD_OUT.jsonl P` (8,832 frames).

## T3 (not started)
- 162 ARKitScenes tokens, 10,368 frames, ~0.73 GB of HTTP range reads from docs-assets.developer.apple.com; plan `D3_FETCH_PLAN.json`.
- Command: `wa_rl.py 7500000 p2_build/c5d3/k6bin/bin/wa.py D3_FETCH_PLAN.json /scratch/jjyeung/k1_frames k1 WA_OUT.jsonl 1` (one thread, pinned wa.py e31661...).
- Then `frame_parity.py K1_MANIFEST.base.json /scratch/jjyeung/k1_frames WA_OUT WD_OUT MISSING_DENSE_INDICES.json CANON_TOKENS.jsonl PARITY.json`, then `manifest_k1a.py --parity`.
- Python with cv2: /scratch/jjyeung/envs/sam3_capretry_native_v1 (p1cpu lacks cv2).

## Gaps that block the launch (BLOCKER event 2026-11-15T17:05Z)
1. GT rasters: 0 of 300 present (`orch_cd/dose_pool/out/{arkit_gt,t1_gt}/gt/*.npz`, 1,367,513,161 bytes; were on 2-18).
2. `b6_build/out/K1_RULES.json` (sha cb0aadee...) and RUNCARD_K1.md, PROOFS.md absent (b6_build was on 2-18).
3. GPU settings `config` = REQUIRED_LOCAL_STEP_544_CONFIG, `data_receipt` = REQUIRED; the `own` phase needs the step-544 model, whose heads/full weights sit at /scratch/fsw/... (not on 1-18).
4. Manifest: no kit script sets `production_ready`/`frame_staging_authorized`; fps/timestamps/total_num_frames are null (needed by `own`); pending list includes reviewed fallback traces.

## Cards (17:00Z)
GPU 6 busy (18.8 GB, 100%); GPU 5 empty.

## Files I created outside the lane folder
- Kit tests wrote new files: kit_k1a/out/{CPU_REHEARSAL,GUARD_COVERAGE,TEST_COVERAGE}.json, kit_k1a/work/tests_b510c300/ (see REMOVAL_CANDIDATES.md).

## Rulings and actions after 17:04Z
- ORCH 17:04/17:05/17:17/17:24 in events folder. K1 runs without fallback traces (targets withheld, failure labels kept). GPU phase waits for ORCH adoption of rules (17:24Z: preregister.py output adopted if sha cb0aadee...89c86e...269).
- 17:28Z wrote kit_k1a/out/K1_RULES.json + K1_RULES.sha256 (preregister.py, PYTHONPATH=native_kit/vendor_sam/vendor); sha matches REFREEZE_PREREGISTRATION_20261115.json pin.
- GT rasters: no copy anywhere; builder absent from mirror (BLOCKER 1722Z). GPU phases tower_sam/own/convert need no GT; tables/render/report do.
- Step-544 export after T2+T3: gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar.part00..03 (21.6 GB), `gsutil cat | pv -q -L 8m`, one part at a time, announced + registered; sha from evalx27 STEP544_EXPORT_ON_ORCHARD.md.
- Change nothing under orch_cd except K1_RULES (allowed). ORCH_CD_MIRROR_1_18_FILES.txt sent.
- k1_report.py/render.py import orch_cd/o3_cache/work/kit (absent) -> CPU report needs recovery or Codex repoint.

## Governed streams (serial-v1, from 17:33Z)
- Node agent on 1-18: /scratch/jjyeung/io_governor_serial (tmux iogov_agent); helpers /scratch/jjyeung/io_governor.
- T2: work/t2_launch.py in tmux k1t2 (reader 4126811 | ratelimit 4126812 | tar 4126813); log work/T2.log; record streams/k1_ops3_t2_mp4.json; on end rename to .done.<epoch>, then verify_mp4 and decode.sh.
- T3: work/t3_launch.py (wa_gov.py | ratelimit | cat), record k1_ops3_t3_arkit; after T2.
- Then GCS step-544 parts (gsutil at /home/jjyeung/google-cloud-sdk/bin), each `gsutil cat | ratelimit` registered, io-weight 1.
- Kit writes only from /scratch/jjyeung/orch_n30/k1_ops3/kc (copy, 17:39Z).

## Staging artifacts (19:47Z)
- /scratch/jjyeung/k1/src/data2/... 138 mp4 (verified). /scratch/jjyeung/k1_frames: 5.0 GB store (WD 8,832 + WA 10,368 frames + 4 pinned ScanNet PNGs).
- work/WD_OUT.jsonl, WA_OUT.jsonl, PARITY.json, PARITY_FAIL_BY_CAPTURE.json, PARITY_DIFF_4_FRAMES.md, arkit_diag/.
- k6 decoder on Orchard: opencv-python-headless 4.14.0.94, numpy 2.2.6, py 3.12.3; ours cv2 4.10.0.
- Step-544: /scratch/jjyeung/k1/m544_parts/ (4 x 5,395,758,080 B; shas in work/w544_all.sh); then extract on /scratch and bind config (84ea03af, not on 1-18) + data_receipt (not on 1-18): open gaps for phase own.

## For the next kit (ORCH 19:46Z)
- The frame decode must pin its library versions, or pins must be taken on decoded pixels with a stated tolerance: byte pins across environments broke on 40% of ARKit frames (Orchard k6: opencv-python-headless 4.14.0.94 + numpy 2.2.6; 1-18: cv2 4.10 + numpy 1.26.4).

## Substitution method (ORCH 19:09Z / 19:46Z)
- work/make_substitutions.py MISMATCH.jsonl STORE OUT [HELD.json] writes rows {s, frames:[[index, pinned sha]], substitution}; only for store files hashing to their pins. Parity input = cat WD_OUT.jsonl SUBSTITUTIONS_k6_replica.jsonl as the WD argument (frame_parity.py unchanged; later rows override). Decoded variants stay in the store.
- Note: w544_all.sh (tmux k1w544) will stop after part 0 by design (part 1 file exists); parts 1-3 run from w544_one.sh.
- o3_cache/work/kit restored 20:2xZ from 13 pinned native_kit files (list+sha: work/O3_KIT_PATH_RESTORE.md); original lost with 2-18, not comparable.
