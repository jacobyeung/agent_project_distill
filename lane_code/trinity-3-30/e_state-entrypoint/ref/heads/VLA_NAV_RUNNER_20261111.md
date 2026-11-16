# VLA navigation runner for R2R-CE and R2RIE-CE (lane vla_nav, 2026-11-11)

## Question
Can we score base Qwen3.5-9B and the spatial student closed loop on R2R-CE val-unseen, and build their 1% and 10% training rows, before any GPU run, so that Test N (VLA_ACTION_HEAD_DESIGN_20261111.md section 4.2) needs no debugging at launch?

## Answer
Yes for everything except the rendered frames. The package `navrun` (/scratch/jjyeung/orch_cd/vla_nav/work/navrun on trinity-2-18; an archive with its sha256 lives in the lane's out/) runs R2R-CE episodes in habitat-sim 0.2.4 under the VLN-CE convention: forward 0.25 m, turn 15 degrees, stop, a 500-step cap, a 3 m success radius and sliding on. Sensors are RGB 512x512, HFOV 90, with the camera at 1.25 m. The package also builds the training rows and the evaluation lists and scores R2RIE-CE. It has one policy interface, `act(history_frames, instruction, state)`, with five output formats:
- `text`: a primitive or an option letter.
- `nav`: vla_heads' text codec, one to three of `forward 0.25|0.50|0.75`, `turn_left|turn_right 15|30|45` and `stop`. It is the N0 and N1 default.
- `waypoint`: heading, distance and stop, run by a local controller.
- `click`: NU's `nu_dec` (VLA_SCHEMA.md 8.1, strict full match): a two-decimal `<goal frame=N x= y=>`, a big turn or stop. It is lifted by the floor plane (schema 8.2) and run by the fixed controller. vla_where's `ClickTranslator` plugs in as `click_backend` and sees only the schema 8.4 whitelist plus the commanded forward metres.
- `chunk`: a [K, 3] vla_heads action chunk, physical or normalised, with quantised residual execution.
History is 32 frames: at decision state t the clip holds states `[i*t//31 for i in range(32)]`, the rule E0 and T1 use. The length is configurable, and the prompt and the click frame number follow it.

## Evidence
- Metrics: NE, SR, SPL, OSR, TL, nDTW (fastdtw, as in VLN-CE) and SDTW. On 150 val-unseen episodes, habitat-lab 0.2.4's VLN-v0 measures equal navrun's: NE and SR exactly, SPL to 1e-8.
- Scenes: all 61 train, 53 val-seen and 11 val-unseen scenes sit in /scratch/jjyeung/mp3d/vlnce_scenes on 2-18 (4.2 GB). Test scenes are absent. No train scene is a val-unseen or test scene, and the row builder checks this before it writes.
- Shortest-path oracle (blind, CPU): SR 1.000 and SPL 0.999 on all 1,839 val-unseen episodes; SR 1.00 on rand100, val_unseen_600 and the 600 R2RIE-CE episodes.
- Visually blind priors. They see no frames, but random and forward-only use training action statistics and the prior reads the instruction:

| Cell | n | random SR | forward-only SR | instruction prior SR |
|---|---|---|---|---|
| val-unseen full | 1,839 | 0.024 | 0.041 | 0.042 |
| val_unseen_600 | 600 | 0.027 | 0.032 | 0.033 |
| rand100 (MIP; base scored 7 in MIP's harness) | 100 | 0.030 | 0.060 | 0.060 |
| R2RIE-CE direction, clean / perturbed | 300 + 300 | 0.007 / 0.027 | 0.020 / 0.020 | 0.037 / 0.023 |

  R2RIE-CE (Taioli et al. 2024; 3,218 direction episodes, 1,609 pairs): the loader, detection AUC and ATD, and the closed-loop SR and SPL drop over pairs. Random's +0.02 drop is seed noise, because its RNG is keyed by episode id.
- Lists (seed 0, written to out/lists with an ordered-id sha256): val_unseen_600_s0, the primary list, proportional over the 11 scenes by largest remainder and interleaved so that positions 0-199, which the early exports read, stay proportional. rand100 is MIP's OpenNav-100 and serves only the harness check; each id's position, scene and trajectory are verified against our val_unseen file. val_unseen_full_1839 and r2rie_direction_300 (300 pairs) complete the set.
- Oracle-click ceiling on val_unseen_600_s0, with GT lead points through the floor-plane lift and the controller but without the occlusion test, which needs the GPU depth sensor: SR 0.802, SPL 0.792, OSR 0.847.
