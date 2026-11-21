# INVENTORY_D: dense-frame sources for GTC arm d (read-only inventory, trinity-2-28)
Anchors: 32 per capture, uniform, first=0, last=N-1 (whole video). Native N = anchor_last+1. Tracked units total 334 (ARKit 98, ScanNet 77, ScanNet++ 159).
## 1. Local /scratch (trinity-2-28)
- Local 64-frame sets: DENSE_MANIFEST.json (cont_ops24_c/.../admission/), frames in /scratch/jjyeung/devs1_frames (sha-named PNG, 256 dirs). Only the 28 ScanNet/ScanNet++ captures: 64 = 32 anchors + 32 midpoints; anchors are a subset (verified 32/32). Stride = anchor_spacing/2 (about 7-68 native frames ScanNet = 0.23-2.3 s at 30 fps; 64-359 native ScanNet++ = 1.1-6 s at 60 fps). NOT dense.
  Files missing locally for 2 ScanNet++ captures (246fe09e98, 38fcf02d0b: manifest paths absent). ARKit: manifest holds only the 32 anchors (no midpoints); devs1_r2/g3s64 holds just 1 ARKit dir (not GTC).
- ARKit lowres: /scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/<id>/<id>_frames/lowres_wide, 125 PNG (256x192) per capture, 10 captures, only 5 are GTC (41069054, 41159782, 41291643, 42899535, 43828368). Traj gives 10 fps (0.1 s/frame, 41069054: 2165 frames/216 s). Mapped by timestamp->traj row: 125 = anchors (32/32 subset) + gap fills; gaps = 1/3 or 1/6 of anchor spacing (e.g. 41069054 gaps 11/12/23 frames = 1.1-2.3 s; 41291643 gaps 3/4/7). Near-consecutive only for short captures; not dense.
- k1_frames (256 dirs of sha PNGs), devs1_r2/anchors (g3s32/g3s64 anchor sets): anchors only, no dense sequence. No other lowres/raw store on /scratch.
## 2. Full-rate native on /data* (single-dir listings and stat only)
- ARKit: /data3/shared/datasets/arkitscenes/3dod/Training/<id>/<id>_frames/lowres_wide/<id>_<ts>.png (256x192 native, ~74 KB avg, 1 file/frame, frame count = N exactly, 18/18 present). Total N = 24,518 frames = ~1.8 GB if all; individual small files (not archived).
- ScanNet: /data3/shared/datasets/scannet/scans/<scene>/<scene>.sens, 0.50-1.60 GB each (10 files, 10.86 GB). Sequential file with depth interleaved, no index: any stride costs the full file. numColorFrames = N+1 (sens 3368 vs anchor_last+1 3367 for scene0166_00; ScanNet 30 fps).
- ScanNet++: /data2/jjyeung/raw_datasets/scannetpp/data/<id>/iphone/rgb.mkv, 186-866 MB each (18 files, 8.69 GB; video, decode is sequential so any stride costs the full file). Frame counts 4,772-22,250 (60 fps assumed, not verified: no ffprobe).
## 3. Cost per option, all 46 captures (frames; read GB; GPU min on one 6000 Ada, both directions, excluding the single 15 s load; one direction = half)
Model: per capture 0.43 s + 2*frames*(0.08 + 0.01*units_c).
| option | ARKit | ScanNet | ScanNet++ | total GPU min |
| every native frame | 24518f 1.81GB 113 | 25709f 10.86GB 132.5 | 215706f 8.69GB 1210 | 1455 |
| 2x anchor (64f) | 1152f 0.09GB 5.3 | 640f 10.86GB 3.4 | 1152f 8.69GB 6.6 | 15 |
| 4x anchor (128f) | 2304f 0.17GB 10.5 | 1280f 10.86GB 6.8 | 2304f 8.69GB 13.1 | 30 |
| ~5 fps (stride 2/6/12) | 12259f 0.91GB 56.6 | 4284f 10.86GB 22.1 | 17975f 8.69GB 100.9 | 180 |
| ~2.5 fps (stride 4/12/24) | 6130f 0.46GB 28.3 | 2142f 10.86GB 11.1 | 8988f 8.69GB 50.5 | 90 |
Governed read at 8 MB/s: ScanNet+ScanNet++ full files 19.55 GB = ~41 min; with ARKit PNGs (5 fps) 20.5 GB total, under 30 GB. Registers with the IO governor (>20 MB). Extract on /scratch. Frame decode (.sens, mkv) is CPU on the node.
## 4. Recommendation
- Local sets suffice for nothing: 64-sets are 2x anchors only; 125 ARKit sets cover 5/18 and are 3-6x anchors.
- ARKit: stride 2 (5 fps) or all frames; cheapest genuinely dense = stride 2 (0.2 s), 0.9 GB, 57 min; stride 4 is 28 min.
- ScanNet: stride 6 (5 fps, 0.2 s), 10.86 GB read (full .sens), 22 min.
- ScanNet++: stride 12 (5 fps, 0.2 s), 8.69 GB read, 101 min; stride 24 is 50 min. All native = 20 h, reject.
- Fit: 30 GB yes (20.5 GB). 2 GPU-h: 5 fps all datasets = 180 min (both directions) no; 90 min if embed counts once (fits); 2.5 fps everywhere = 90 min both directions (fits). Cut ScanNet++ first.
