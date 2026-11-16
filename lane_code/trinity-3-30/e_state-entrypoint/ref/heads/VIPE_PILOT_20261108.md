# ViPE pose pilot on ScanNet (lane vipe, Devin, 2026-11-08)

## Question
Is NVIDIA ViPE (Video Pose Engine, `nvidia-vipe` 1.2.0; DROID-style bundle adjustment with metric depth priors; Cambrian-P's pseudo-pose source) accurate enough to pseudo-label unposed indoor video for night-3+ pose data and later navigation/VLA video? Does it beat G3T, whose recorded level is 2.3 deg rotation (ScanNet 3.2, ScanNet++ 1.7) and 0.24 relative centre error at training-scene scale (0.07 after per-recording Sim(3) to GT), without metric scale?

## Answer
**Yes, ViPE pseudo-labels indoor video at about G3T's oracle-scale accuracy, and it does so with its own metric scale.** It matches G3T on rotation and halves G3T's centre error. On 58 ScanNet recordings with GT poses, ViPE's frame-0-relative rotation error is 2.7 deg, against 2.9 deg for G3T on the same frames. Its centre error is 0.116 of the distance from frame 0 at its own metric scale, against 0.229 for G3T at the training-scene scale. Per recording, ViPE beats G3T on rotation in 66% of recordings and on centre error in 79%.

ViPE's metric scale is biased about 9% high. With one global correction constant (x1/1.089, fitted 2-fold out of sample), 93% of recordings fall within +-10% of the GT scale, and the centre error drops to 0.081. That is G3T's level after a per-recording Sim(3) to GT (0.085 here), and ViPE reaches it without any GT.

The cost is 1.7 GPU-min per recording on an H100 (0.23 s per 10 fps frame, 10 GB peak), or about 2.3 GPU-h per hour of video. ViPE never crashed. It lost tracking on 2 of 58 recordings, and a GT-free check flags both: drop a recording when ViPE and G3T disagree by more than 5 deg on the 32 frames.

Verdict: **adopt ViPE (default preset, pose-only, x1/1.089 scale) plus the ViPE-vs-G3T 5 deg filter as the pseudo-pose source for unposed indoor video.** Before relying on it for navigation/VLA video, test it on that domain (see Tests).

## Setup
- **Recordings.** I drew 80 ScanNet v2 `_00` scans at random (seed 20261108) from rooms outside exclusions v2 (`BENCH_SCENE_EXCLUSIONS_v2.json`, 601 scans in 275 rooms, including STI's scene0000-0149 and VSTI/VSI val). I streamed each `.sens` from the official v1/scans URL on Orchard's login node and wrote no `.sens` to disk. 58 finished before the 55-recording target stopped the fetch, and I used all 58. Median 1,400 GT frames per recording (about 47 s at 30 fps); median GT extent 3.0 m.
- **Frames.** Every 3rd colour frame (10 fps, 1296x968 JPEG as recorded), plus GT camera-to-world at every frame.
- **ViPE.** `nvidia-vipe==1.2.0` (sdist sha256 25a7bbcf...), built with torch 2.11 cu130 and nvcc 13.0, sm_90. I used the default preset: GeoCalib intrinsics, UniDepth-L keyframe metric depth and the 1,024-keyframe buffer, and ViPE's internal resize to about 384x512 for SLAM. I turned off instance masks (`init.instance=null`, static rooms) and depth post-processing (`post.depth_align_model=null`, pose-only). ViPE ran on the whole recording at 10 fps.
- **G3T.** `thatbrguy/g3t` c55e91a0, the same weights as the c1r lane, with the g3t repo at 193ce195. It ran feed-forward on 32 frames sampled uniformly over the whole recording (square pad 1024, bilinear 518, w2c = g2c @ w2g from the local and global heads). Translations use the ScanNet training-scene scale 1.995 (head_acc T1).
- **Metrics.**
  - *Training metric (32 frames).* Both methods are scored on the same 32 frames. Rotation is the geodesic error relative to frame 0. Centre error is |c_pred - c_gt| in frame-0 camera coordinates, divided by |c_gt| on views with |c_gt| >= 0.25 m (head_acc T1 definition).
  - *Oracle variant.* The same centre error with a per-recording least-squares scale.
  - *Scale.* Sim(3) Umeyama on camera centres gives the ATE (also as a fraction of the GT bounding-box diagonal) and the pred/GT scale, with no alignment applied in the other metrics.
  - *RPE.* Relative pose error over 1 s.
  - *Whole-recording metrics.* All ViPE frames at 10 fps.

## Numbers (58 of 58 recordings paired; median [IQR])

| Metric (32 frames over the whole recording, frame-0 relative) | ViPE, own metric scale | G3T x 1.995 training-scene scale |
|---|---|---|
