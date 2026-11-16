# Dynamic scenes and the VLA-efficiency pitch (plan, 2026-11-08)

Research-lead plan. Times are PT. Nothing here has launched.

## Question
The user wants to show that a VLA fine-tuned from our student learns from fewer demonstrations and steps, and ends better, than one fine-tuned from base Qwen3.5-9B. The user asks how we handle dynamic scenes and whether the student must train on them.

## Answer
- **The first demonstrations need no dynamic training.** In navigation sims (R2R-CE, RxR-CE, R2RIE-CE) and manipulation sims (LIBERO, CALVIN, SimplerEnv), the scene stays still and only the agent moves: its camera, its arm and the object it holds. Our pose and depth heads cover that motion. The published geometry gains in both families come from VGGT, a static teacher (Spatial Forcing on LIBERO, JanusVLN on R2R-CE).
- **Claims about crowds, driving or real homes with people do need it.** Main's measurements show that static geometry fails on independent motion. On DSI-Bench, time-aware stores beat our static G3T store by 7-9 points, and on STI-Bench static SPLIT trails no-tool.
- **Monday's final run should add nothing for dynamics.** Each candidate either does nothing on static data or puts an untested change into the only attempt (§3).
- **First post-final experiment:** fine-tune on LIBERO-Spatial with few demos and compare base, student and a Spatial-Forcing-style positive control (~95 H100-h). Request Matterport3D access now, so that R2R-CE, the cleanest demonstration, can run next.

## 1. Do we need dynamic training? Per target

Robot video holds three kinds of motion, and each needs a different skill.

| Motion | Examples | What handles it | In our student |
|---|---|---|---|
| Ego-motion | navigating camera, wrist camera | pose head on CAM tokens, depth | trained on static scans filmed by a moving camera |
| Agent-induced | the arm, a grasped or pushed object | per-frame depth, pointing, relations; proprioception gives the arm pose | per-frame skills trained; no tracking |
| Independent | people, pets, vehicles | motion segmentation, robust pose, time-indexed 3D | absent |

The benchmarks in the pitch contain only the first two kinds.

| Target | What moves | Dynamic training? | Why |
|---|---|---|---|
| Navigation: R2R-CE, RxR-CE, R2RIE-CE | camera only; the Habitat MP3D meshes are static | No | Its input is egocentric video of an indoor house, which matches our training data. JanusVLN's pretrained VGGT encoder lifts R2R-CE SR/SPL from 47.0/40.9 to 52.8/49.2. Moving humans appear only in HA-VLN-CE, the later dynamic extension. |
| Manipulation sims: LIBERO, CALVIN, SimplerEnv | the arm and the manipulated objects; the agent-view camera is fixed and the wrist camera rides the arm | No | Proprioception gives the arm and wrist-camera pose, so the backbone must supply per-frame depth, pointing and relations. Spatial Forcing's static-VGGT alignment scores 98.5 vs 97.1 (OpenVLA-OFT), 96.9 vs 92.7 in its 1×H100 ablation, and 42.3 at 1% and 75.8 at 5% of the data. |
| Real robots among people | adds independent motion | Later | Static priors still transfer: Evo-0 reports real-robot gains with VGGT tokens (secondary source). Dynamic training would improve these results, but they do not depend on it. |
