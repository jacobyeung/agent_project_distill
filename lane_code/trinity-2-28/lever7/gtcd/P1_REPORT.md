# GTC-D phase 1: served frame sources, stream lists, stage scripts (trinity-2-28, 2026-11-21)

## Served path (all 1,472 anchors of the 46 captures are k6tk frames)
- I matched every anchor sha256 in FRAMES_GTC.json to the k6 frame map (fb_pack/in/pk/frame_map.jsonl.gz): 1,472 of 1,472 match, each at its plan index. The builder is k6 (distill_sync/.../b06_a2dense/work/k1src/p2_build/c5d3/k6bin/bin/{wd.py,wa.py,k6run.py}); the plan is frame_plan.json.gz.
- ScanNet (d1) and ScanNet++ (d2): the served frames come from the VSI-590K release mp4 (`scannet/<scene>.mp4` at 24 fps, `scannetppv2/<id>.mp4` at 60 fps; both 640x480). They do not come from .sens or rgb.mkv. Decode rule (wd.py): cv2.VideoCapture with sequential grab, frame j = source index j, INTER_AREA to 640x480 only if the size differs (it never does), cv2.imencode PNG at compression 3.
  - Proof: I copied 2 mp4 under 20 MB and decoded them with cv2 4.10 (env sam3_capretry_native_v1). scene0380_01 gave 32/32 sha256 equal and 0c7962bd64 gave 32/32, with max pixel difference 0. Each decode also matched raw_n (922 and 4,772 frames). See work/EVIDENCE.txt and work/vid_rule.py.
  - The registered .sens path fails: frame i of scene0380_01.sens, resized to 640x480, differs from served anchor i by a mean of 2.3-3.6 grey levels (max 55), because the mp4 encoding is lossy. Index alignment holds; i+1 is far worse.
- ARKit (d3): the served frames come from Apple's raw `raw/Training/<id>/lowres_wide.zip`, which wa.py reads by HTTPS range. wa.py takes the member nearest the plan timestamp (within 2 ms), runs cv2.imdecode, rotates by the plan's rot (43828324 is 180, the other 17 none), upscales 2.5x with INTER_CUBIC to 640x480, and writes PNG at compression 3. The zip holds about 60 fps members (6,238 members for 1,034 traj rows on v00475f483e27); index k is traj row k.
  - The /data3 3dod lowres_wide source cannot reproduce the served PNGs. On the 5 captures with local 3dod copies (same file sizes as /data3), wa.py's exact orient and encode gave 0/160 sha256 equal and 0/160 within 1 grey level, with a median mean-abs difference of 0.78-1.14 per capture. The 3dod PNG pixels therefore differ from the raw-zip members. vga_wide and wide do not exist on Trinity.
  - The registered rule says each ARKit capture is then "reported, not substituted", which means all 18. I have not verified the raw-zip path on Trinity because it needs internet. k1_ops3 ran wa.py from 1-18 and matched the Orchard pins byte for byte except 2,200 frames that differed by at most 1 grey level (cv2 4.10 vs 4.14).

## Lists (tar -T, absolute paths, sizes by stat; dense = first..last anchor at the stride, plus every anchor)
| list | files | bytes | stride | fps | dense frames |
|---|---:|---:|---:|---:|---:|
| lists/scannet.txt (10 mp4) | 10 | 274,709,069 | 5 | 4.8 | 5,376 |
| lists/scannetpp.txt (18 mp4) | 18 | 444,162,900 | 24 | 2.5 | 9,534 |
| lists/arkit.txt (3dod PNG, fails sha) | 12,551 | 903,110,749 | 2 | 5.0 | 12,551 |
- Total: 1.62 GB (0.72 GB for the videos). The mp4s sit in two /data2 dirs: gt_teacher_r1313/poolext_wave2_scannet/media (9 ScanNet), poolext_wave1_scannetpp/media (13 ScanNet++), and vsi_distill_training_20260917/media (scene0666_01 and 5 ScanNet++). No capture is missing. Per-capture detail: lists/SUMMARY.json.
- The stage scripts stage_{arkit,scannet,scannetpp}.sh follow the r0p2 pattern: the root starts stopped and does not exec, --expected-bytes is the list total, and rc goes to logs/rc_<ds>.txt. bash -n passes on all three. None has been run or registered.

## Changes to the registered plan (need an orchestrator ruling)
1. ScanNet and ScanNet++ use the VSI mp4 instead of .sens and rgb.mkv. The read drops from 19.55 GB to 0.72 GB, and the mp4 is the only source that reproduces the served sha256.
2. ScanNet runs at 24 fps, not 30. The registered stride 6 gives 4.0 fps (4,555 frames). I default to stride 5 (4.8 fps, 5,376 frames) to keep the 0.2 s intent. Dense frames total 27,461 against the registered 25,531, so GPU time is about +8%.
3. ARKit has no sha-reproducing source on Trinity. Options:
   - (a) Fetch the Apple raw zip by range with the pinned wa.py. This is an internet stream (io-weight 1) of roughly 12,551 x ~90 KB, about 1.1 GB (an estimate; no request has been made). It needs a new stage script on the wa_gov pattern, not a tar list.
   - (b) Stage lists/arkit.txt (3dod) and report ARKit as not reproduced, which drops ARKit from arm d.
   - (c) Drop ARKit outright.
   - Default: (a) if the orchestrator names the stream, else (c). Do not run stage_arkit.sh unless (b) is chosen.
4. The kit should pin cv2 4.10 (env sam3_capretry_native_v1) and check every anchor. k1_ops3 saw rare 1-grey-level drifts across cv2 versions, so anchors need a stated pixel tolerance rule if a sha check fails.

Reads from /data*: 7 single files (LANE_RULES, plan sections, INDEX grep, K6TK record, DATA_MAP grep, two mp4 of 12.3 and 10.7 MB), plus single-directory listings and stats. No SSH, no Git, no GPU.
