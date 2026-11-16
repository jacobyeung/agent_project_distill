# Why does camera pose plateau at ~18-20 deg translation direction? (2026-11-09)

## Question
Every pose head (f17, C1-a, T0, T1) ends at ~18-20 deg translation direction, ~46-49% camera-centre error and ~12 deg rotation on evalx's 312-scene held-out ScanNet harness, while G3T gets 3.65 deg direction on the same scenes. Data, loss and partner-frame variants did not move it. Where is the information lost: (a) the input (resolution, frames, duplicate layout), (b) the vision encoder, (c) the causal LM, (d) the one-token readout or head, (e) optimisation or capacity, or (f) the labels?

## Answer
- **The geometry is built inside the LM from encoder features that carry no readable pose, and the LM builds too little of it.** Probing the frozen T0 m800 at each depth gives this picture:
  - The ViT/merger tokens give chance-level pose (direction 58-77 deg) to a fresh head. That holds with per-frame pooling, with a cross-frame token transformer, and at 2x pixels.
  - Layer 16 halves that error (26-41 deg).
  - The final CAM carrier reaches T0's own head (15-25 deg).
  - The same probe on G3T's features reaches 7.5-14.5 deg (camera tokens 7.5-10.9), and G3T's own poses match our labels to 3-6 deg.
- **The readout and head are not the bottleneck (d):** at layer 16, visual tokens and the carrier carry the same pose. A fresh head on the final carrier rebuilds T0's head in 300 steps. Given G3T features, that same head beats T0 by 2x.
- **Capacity, optimisation and labels are not the bottleneck (e, f):** the full model fits 50 repeated scenes to 5.7 deg direction (still falling). G3T agrees with A1 and A3 labels to 3-6 deg, and every source follows one convention.
- **The gap is not generalization.** T0 misses rows it trained on (seen once) by as much as new rows (11.5-14 deg). Held-out scenes add only 2-7 deg.
- **What limits pose is (b)+(c):** the encoder delivers no geometry that a head can read, and the LM's 32 layers compute only part of it from 32 views. More pixels do not change this: RES2 trained gives 0.93x (pose_sweep), and ViT probes at 2x stay at chance. Supplying geometry features does change it: GXC (G3T inside) reaches 10 deg at m200 (gx_build).

## Evidence
### Test 1: train fit (T0 m800 own head, readout-only, AWS 124953; harness metrics, frames 2..32 vs 1, |c|>0.2 m; 90% scene-bootstrap CI)
| rows | rows / scenes | rotation median | centre / distance | direction err |
|---|---|---|---|---|
| A1 rows trained on, ScanNet++ / ARKit | 100+100 | 13.6 / 14.3 | 32% / 28% | 14.0 [13.1, 15.0] / 13.0 [12.0, 14.4] |
| never-trained A1 rows, same scenes, ScanNet++ / ARKit | 100+100 | 14.4 / 12.5 | 30% / 24% | 14.1 [13.3, 15.2] / 11.5 [10.6, 12.6] |
| A1 ScanNet, trained on / never trained | 14 / 14 | 9.8 / 9.5 | 29% / 27% | 12.0 / 10.9 |
| held-out ScanNet scenes, row pipeline (scans_test) | 392 / 98 | 11.4 | 39% | 15.5 [14.3, 16.7] |
| held-out ScanNet harness, video pipeline (evalx) | 312 scenes | 11.7 | 46% | 18.4 |
| held-out ARKit scenes (A3-schema CP1 val slice) | 400 / 50 | 24.4 | 50% | 24.5 [22.1, 27.3] |
Reading (pre-registered): train error is close to held-out, not < 8 deg, which points to causes (a)-(e) rather than generalization. Each A1 "trained on" row was seen once (C1-a steps 1-800, T0's init).

### Test 2: frozen-feature probes
Frozen T0 m800, a fresh production CPDM head per source (frame + origin embeddings on every source), 300 steps x 32 A1 rows, read at m300. Direction error (deg) with rotation median in parentheses. Jobs: pdP 127119, pdG 129068, pdX 128795/128796. Tables: /scratch/jjyeung/orch_cd/posediag/work/res/{pdP,pdG,pdX}.md.
