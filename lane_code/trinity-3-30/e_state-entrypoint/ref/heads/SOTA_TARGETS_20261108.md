# SOTA targets for the student: ReVSI, VSTI, VSI-Bench, dynamic and multi-view benchmarks (2026-11-08, Sun 05:45 PT)

Planner record (Claude Opus, read-only; this is the only file it wrote). Scope: the Qwen3.5-9B student with its own heads. SPLIT (Gemini planner + tools) numbers appear only as headroom. Downstream scope is indoor robotics: no driving, no fisheye.

**Question (user, 11-08).** "Get state of the art basically on revsi, vsti, ideally other dynamic scenes as well, and multiview (eg mindcube)", alongside VSI-Bench. Where does the student stand against each published top, what limits it, and what should change before the final run starts tonight (night 1 from Sun ~17:00-18:30 PT; night 2 from Mon 19:00 PT)?

**Answer.**
- **VSTI is the nearest claim.** f17 scores 69.41 on our 450-question subset against Cambrian-P's 68.9 on the full test. That lead sits inside the subset's sampling error, so only a full 6,042-question read settles it.
- **ReVSI has the lowest bar** (Gemini 3 Pro 60.9, best open model 54.1, Cambrian-S 49.1), but no student has been scored on it. Score base, f17, FT-X and Cambrian-S on the ReVSI dev subset today, so that Monday's read has references.
- **VSI-Bench is the hardest.** FT-X's 64.14 trails Cambrian-P's 73.7 by 9.6 and the Cambrian-S floor (67.42) by 3.3. Closing that gap takes VSI-590K-scale data and the missing heads, not a change to tonight's recipe.
- **The final run is a heads-and-routing run, and its VQA dose is small** (about FT-A's m300-m500 dose, §2). It will probably not pass f17 on VSI-Bench or ReVSI; the SOTA push on those two comes after it.
- **Dynamic and multi-view benchmarks need post-final work.** DSI, STI and MMSI have weak published tops (41-49), but our heads never saw independent motion, and the evaluator has no multi-image path. MindCube is a specialist race: models trained on MindCube-10K score 85.6-90.1, while VSI-trained models score 38-40.
- **Tonight, add no training rows.** Run the contamination checks in §3.2, stage the ReVSI references (§3.3), and leave the recipe alone (§3.4).

## 1. Targets

| Benchmark (metric, size) | Published top | Our best today | Gap | What SOTA requires |
|---|---|---|---|---|
| **ReVSI** (7-task macro; 6,158 q at 32 f) | Gemini 3 Pro 60.9 (1 fps); best open InternVL3.5-38B 54.1; spatial fine-tunes VLM-3R-7B 50.1, Cambrian-S-7B 49.1 (128 f) | student: none measured. SPLIT 74.8 vs no-tool 65.2 on the 6,158 (brief; not re-verified) | student unknown; SPLIT +13.9 | No training split exists, so every model transfers. Our student counts as a VSI-domain specialist, like Cambrian-S. Above 54.1 it is the best open model; above 60.9, the top |
| **VSTI-Bench** (5-task mean; full test 6,042 q) | Cambrian-P 68.9 (VLM-3R data + pose); GeoThinker-8B 67.4; VLM-3R 58.8; human 77.0 | f17 69.41 on VSTI-450 v3 (student evaluator; 66.95 under the head-call harness); P1 m200 68.71; FT-X 68.41 | +0.5, but subset against full set, inside ~±4 sampling error | A specialist with in-domain data, which we are; confirm on the full 6,042 |
| **VSI-Bench** (official 5,130) | Cambrian-P 73.7 at 128 f, 72.0 at 32 f; SpaceMind++ 73.2; GeoThinker 72.6 | FT-X 64.14, f17 63.79 (32 f). VSI-500: f17 60.99, FT-X 60.86 | −9.6 (−7.9 frame-matched); −3.3 below the Cambrian-S floor (67.42, 128 f) | A specialist trained at VSI-590K scale |
| **MindCube** (Tiny eval set) | trained on MindCube-10K: SenseNova-SI-8B 85.6 (board 90.1). Untrained: Gemini-3-Pro 70.8, SpatialClaw agent 72.8 (both aggr) | none (data not held) | VSI specialists score 38-40 (Cambrian-S 39.6 aggr, Cambrian-P 38.4) | Train on MindCube-10K and beat 85.6-90.1. The untrained bar (70.8) is far above every VSI-trained 7-9B model |
| **DSI-Bench** (1,769 q × 4 augmentations) | Gemini-2.5-Pro 46.9 sample-wise; SpatialTrackerV2 35.7 group-wise | student: none. SPLIT 68.2 (paper, static store); 74.0 with Point4D on the 1,000-q subset | student unknown | Zero-shot (no training split) |
| **STI-Bench / ReSTI** (2,064 / 1,782 q) | Gemini-2.5-Pro 41.4 (STI) | student: none. Gemini 3.1 Pro no-tool 49.5, static SPLIT 46.0 (STI, 1,721 q) | student unknown | Zero-shot. Only the Omni6DPose rows and the 21 ScanNet-val videos are clean and in scope for the student (§3.2) |
| **OST-Bench** (~10K q, online rounds) | Gemini-2.0-Flash-Thinking 54.2 zero-shot; InternVL2.5-38B 60.2 after its 50K training split | none (not held) | n/a | Either; the training split allows a specialist |
| **MMSI-Bench** (multi-image) | Gemini-3-pro 49.2 (aggr); human 97.2; Cambrian-P 28.0 | student: none. SPLIT 67.8 (paper) | student unknown | Zero-shot (no training split) |

Notes.
- "Our best" uses the official protocol where one exists: 32 frames, thinking on, the 4,096-token cap. VSI-500 sits inside the 5,130, and the ReVSI dev subset inside the 6,158.
- The VSI-Bench tops are probably full-set numbers: Cambrian-P's table lists Cambrian-S-7B at 67.5, and our full 5,130 run of Cambrian-S gave 67.42 at 128 frames.
