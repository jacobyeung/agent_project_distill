# C1 head exports through the toolprog harness: do C1's poses turn into answers? (evalx, 2026-11-08 17:20Z)

**Question.** At m100 and m200, do the C1 placement arms' own per-frame poses (and FoV) answer the 655 harness items (VSI-500 ScanNet 207 + VSTI-450 448) better than f17's heads, and better than answering directly?

**Answer.** C1-a leads at m100 and m200 and keeps improving: at m400 its rotation (median 16.8, yaw 13.6 deg) nears f17's (13.0 / 11.3), and its camera-motion program beats direct by +7.2 [-1.8, +16.4]; centre error (61% of distance) and FoV (6 deg) still miss break-even. At m200: At m200 its pose ties f17's heads on camera motion (53.7 vs 55.4, paired -1.7 [-11.4, +8.7]) and beats f17's direct answers there by +4.1 [-5.5, +13.9], a gain whose CI still includes 0. On the VSI geometry family it loses to direct (-6.1 [-14.6, +2.3] with own FoV). C1 fails every pose break-even of POSE_ACCURACY_BRIDGE at m200 (yaw 20 deg vs <= 15, centre 77% of distance vs <= 40-50%), and its FoV head is 6-8 deg off where f17's is 0.2 deg.

## Evidence
Exporter: `/scratch/jjyeung/orch_cd/evalx/work/aws_x` mode x, the trainer's own `CarrierC1.readout` on 444 VSI-500 + VSTI scenes (toolprog's 32-frame selections, PyAV rgb24, duplicate layout); AWS 107582 (m100, 3 arms) and 109072 (m200, C1-a/C1-c), 2,220/2,220 scenes, 0 errors; `pose_readout` equals `readout` exactly (max diff 0.0). Harness: vendored toolprog harness with a per-frame head source (`evalx/work/tp`); a GT replay (GT poses encoded as C1 codes) reproduces the GT program on 462/462 items. Pose-only arms train no gravity branch, so the world uses GT gravity (`c1_to_heads.py --gravity auto`). Conditions: SW-gtdepth-spec (own pose, GT clicks + GT depth + GT intrinsics) and SW-gtdepth-ownfov-spec (also own FoV). Tables: `evalx/work/out/POSE_c1a_m100_..._c1c_m200.md`, `HARNESS_SW-gtdepth{,-ownfov}-spec_*.md`.

Pose vs GT, 312 ScanNet scenes, frames 2-32 relative to viewpoint 1:

| arm | rot mean / median (deg) | yaw median | centre / distance | scale | pred / GT rot magnitude | FoV err v/h (deg) |
|---|---|---|---|---|---|---|
| f17 (anchors) | 20.4 / 13.0 | 11.3 | 49% | 0.83 | 75.8 / 74.9 | 0.2 / 0.2 |
| C1-a m100 | 55.3 / 36.7 | 31.9 | 94% | 0.84 | 41.9 / 76.0 | 8.2 / 4.6 |
| C1-b m100 | 82.1 / 76.0 | 73.8 | 103% | 0.30 | 17.2 / 76.0 | 4.4 / 5.0 |
| C1-c m100 | 77.7 / 64.3 | 42.2 | 152% | 1.26 | 47.0 / 76.0 | 5.5 / 2.1 |
| C1-a m200 | 37.1 / 26.6 | 20.2 | 77% | 0.97 | 86.1 / 76.0 | 6.4 / 6.0 |
| C1-c m200 | 46.5 / 37.3 | 22.8 | 87% | 1.02 | 81.9 / 76.0 | 7.6 / 5.4 |
| C1-a m400 | 26.4 / 16.8 | 13.6 | 61% | 0.85 | 69.7 / 76.0 | 5.8 / 6.2 |
| C1-r m100 | 39.7 / 27.4 | 19.2 | 86% | 0.83 | 73.5 / 76.0 | 6.3 / 7.8 |
| C1-r m200 | 27.7 / 18.4 | 13.4 | 70% | 0.66 | 75.8 / 76.0 | 8.0 / 7.4 |
| C1-r m400 | 22.5 / 15.2 | 11.8 | 58% | 0.98 | 79.9 / 76.0 | 7.3 / 10.5 |
| C1-a m800 | 19.8 / 13.3 | 10.5 | 49% | 0.86 | 76.7 / 76.0 | 4.6 / 6.0 |

Harness, own pose + own FoV with GT clicks and depth (program score; direct = f17's direct answers on the same items):

| family (n) | GT program | f17 direct | f17 heads | C1-a m100 | C1-a m200 | C1-c m200 | C1-a m400 | C1-r m100 | C1-r m200 | C1-r m400 | C1-a m800 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| camera motion (100) | 98.0 | 49.6 | 55.4 | 45.0 | 53.7 | 48.0 | 56.8 | 48.4 | 53.6 | 61.1 | 63.7 |
