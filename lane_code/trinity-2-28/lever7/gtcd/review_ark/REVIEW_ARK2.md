# REVIEW_ARK2: GTC-D ARKit unit re-review (fresh, trinity-2-28, 2026-11-22; read-only; no d value computed)
## Verdict: GO for the ARKit GPU pass on trinity-0-13, provided the launch line uses absolute paths (F1).
Option (a) closed the earlier NO-GO: k6's cv2 4.14.0 build reproduces every served anchor byte for byte, so no tolerance (option b) is needed.
1. Decode and stride: PASS.
   - The env matches Orchard (cv2k6/oq1.out:25-26 numpy 2.2.6, cv2 4.14.0; k6cv2 prints 3.12.13 4.14.0 2.2.6). Both wheel sha256 values equal pypi_*.json.
   - run_decode_k6.sh:6-7 runs the unchanged decoder (decode_arkit.py, 19:52, the version REVIEW_ARK.md:11-15 checked against wa.py) on raw/ into frames_k6/.
   - decode_k6.log:1-20 shows 18/18 OK and 576/576 anchors; logs/dense_ark.log:20 gives DENSE_RC=0, 18 ok, 576/576.
   - I checked independently: all 576 dense_ark anchors equal FRAMES_GTC.json's served sha256, all 12,551 frames equal their manifest sha256,
     and every non-anchor frame sits at an even traj row (stride 2), with 0 missing indices. frames/ and DECODE_ARKIT.json are untouched.
2. Kit diff: PASS. SHA256SUMS_GTCD_ARK and SHA256SUMS_GTCD both check (rerun now). No kit_ark file changed after REVIEW_ARK.md
   (mtimes up to 20:05), so its findings stand: frames.py, seeds.py and old tests are identical; arm d resolves frames from the manifest folder (track.py:346).
3. Relift: PASS (code unchanged). unit_state binds each unit's dense sha256 (relift_t.py:177,356-379). Pooled is read only when both units
   are complete (:491-504), and a..b are asserted equal to RELIFT_GTCB.json (:448-458). I reran no tests (they write under work/).
4. Launch: PASS. The safeguards are those REVIEW_ARK.md accepted (launch_gpu.sh:50-64,67-107). Collisions are refused: launch_gpu.sh:56-62,
   track.py:242-250, and there is no out_ark/ yet. The embedding cache lives in memory, not under the shared work/gpu_cache.
   track.py --forecast on DENSE_D_ARK.json (read-only, run now) gives 18 captures, 49 seeds, 1388 s and a 21.7 GiB GPU peak, against the 5280 s hard stop.
   Host image cache for the largest capture (1615 frames x 12.2 MB fp32) is ~20 GB, under the 60 GiB RSS guard (track.py:366).
5. Governor: PASS.
   - Apple stream: as REVIEW_ARK.md:24-26 found (logs/stage.log root_state=T, rc 0 0 0, .done.1795311297).
   - cv2 wheel stream: the root starts stopped and never execs (cv2k6/stage_cv2.sh:25; logs_stage.log root_state=T rl_comm=ratelimit), ratelimit is in the pipe (:27), registration returned rc 0 (:36-38).
     The record was renamed only on PIPE_RC 0 0 (:44-47; streams/lever7_gtcd_cv2.done.1795314878 exists, no live .json). There was one curl and no retry.
   - The numpy wheel (16.5 MB) was under 20 MB and moved unregistered, which is allowed.
6. Run or readability: no crash path found. Rotations are only none or 180, so the frame size is constant per capture. All 18 captures have b seeds.
   - Cosmetic: the DENSE_D_ARK.json captures say "cv2": "4.10.0", the env dense.py ran in, although it only copied frames_k6 bytes.
     The provenance of record is DECODE_ARKIT_K6.json (4.14.0); say so in the RESULT.
## Required fixes and actions
- F1: The brief's form "cd gtcd && ... --dense gtcd/dense_ark/... --out gtcd/out_ark/track" is relative, so launch_gpu.sh:52-53 refuses it (and :44 leaves a
  stray gtcd/gtcd/out_ark/track). Use the absolute line in events/lever/STATUS.md:6, as REPORT_GTCD_ARK.md step 4 does.
- Before the relift on 2-28: out_ark/track must be copied back, and the ScanNet unit's out/track and out/RELIFT_GTCD.json must be present (I did not look).
- Record in the plan record that option (a) reproduced 576/576 with cv2 4.14.0, so no tolerance was registered.
- Disclosure: my bounded read of the plan record's GTC-D section also printed the already-recorded ScanNet-unit result lines (record:275-282). I used none of them.
