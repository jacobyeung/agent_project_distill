# k1_ops3 STATUS (trinity-1-18)

Updated 2026-11-16T00:33Z. tower_sam RUN 2 HALTED at kit output cap (1.5 GB) after 152/300 (all 152 intact; BLOCKER 0032Z). Codex k1_maxbytes dispatched (k1_cli --max-bytes; identities unchanged). Resume in same root needs ORCH order (rename HALTED.json, 2 card readings, --max-bytes 4000000000).

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
