# SOTA survey: geometry-aware VLMs on VSI-Bench, ReVSI and VSTI, and what explains their gains (2026-11-09 08:00Z)

Research record (SOTA-survey lens of the 11-09 SOTA design workflow; Claude Opus, web search plus bounded reads). It updates `SOTA_TARGETS_20261108.md` with newer papers, the VSTI label erratum and per-technique evidence.

## Question
Which published models lead VSI-Bench, ReVSI and VSTI, with what frames, geometry inputs, data and training, and do they predict pose or depth? Which techniques explain their gains, and how far is the student from each top?

## Answer
- **VSI-Bench.** Open tops: GeoWeaver-10B 75.05 (Qwen3.5-9B, LoRA r64, frozen VGGT patch tokens, trained at 8 frames; EASI protocol, eval frames unstated), Cambrian-P-7B 73.7 at 128 f / 72.0 at 32 f, SpaceMind++ 73.2, Video-ORA-9B 73.1 (Qwen3.5-9B, no CoT, SFT + RL), GeoThinker-8B 72.6 at 32 f. Ours: f17 63.79, FT-X 64.14 (official 5,130, 32 f). Gap: -8.2 to Cambrian-P at 32 f, -11.3 to GeoWeaver-10B, -3.6 to the Cambrian-S floor (67.42). The same base, Qwen3.5-9B, scores 57.9 direct (Video-ORA's table), so our fine-tunes add ~6 points where same-base SOTA adds 15-17.
- **ReVSI.** Open top at 32 f: GeoWeaver-10B 57.5 (57.3 at all frames). Best open overall: Video-ORA-9B 58.2 at 128 f (55.8 at 64 f). Gemini 3 Pro 60.9 (1 fps, 1,093-item tiny subset); CROSS, a training-free SAM3 + DA3 operator library on Qwen3-VL-32B-Thinking, 60.2 at 64 f. Base Qwen3.5-9B 51.6 at 64 f. The student has never been scored. Fine-tunes gain only +4 to +6.6 over base, and VSI-590K-style training loses 15-22 points from VSI-Bench to ReVSI (Cambrian-P 73.7 -> 52.0).
- **VSTI.** Upstream relabelled the five camera-position types on 2026-07-13 (camera centre was computed as -R^T t on camera-to-world poses) and removed 306 items, leaving 5,736. Our upstream file `vsti_upstream_labelfix_20260715/vstibench_test.json` holds exactly those 5,736 rows, so VSTI-450 v3 is post-erratum and the "6,042 full set" in SOTA_TARGETS is the old count. Every published top uses old labels: Cambrian-P 68.9, Cog3DMap-8B 67.5, GeoThinker-8B 67.4, VLM-3R 58.8. The only corrected-label number found is GPT-6-Astra 70.33 (third-party blog, 32 f). f17 scores 69.41 on VSTI-450 v3. The largest cell gap is camera movement direction, whose labels did not change: f17 56.0 against Cambrian-P 87.7 (67.7 without its pose loss).
- **No top VQA model needs accurate inference-time pose.** Cambrian-P drops its pose tokens at inference (VSI 72.0 either way); GeoWeaver models no pose or depth; Video-ORA uses no geometry. Our 18-20 deg plateau matters for routed programs (pose bridge break-evens 7.6-15 deg), which no published VQA model relies on.

## Techniques and their measured value
| Technique | Evidence (VSI-Bench unless noted) |
|---|---|
| In-domain QA at >= 590K rows | Base of every model above 70: Cambrian-S (VSI-590K) 67.5; GeoThinker 1.8M rows 72.6; SpaceMind-900K 73.2; Video-ORA (VSI-590K + SenseNova-SI-800K subset, 285K SFT + 100K RL prompts) 73.1. Buys VSI-Bench far more than ReVSI |
| Frozen VGGT features fused into visual tokens | SpaceMind++ +0.9 (VGGT) and +2.6 (cognitive map); SpatialStack (Qwen3.5-4B, VGGT layers 11/17/23 -> LLM layers 0/1/2) 64.76 -> 67.52; GeoWeaver-5B placement: pre-reasoning grounding 72.80 vs decoder-side 70.45 vs input-level 68.10; GeoThinker +18.8 in a small-data regime |
| Training-only pose loss (camera token + VGGT-style head) | Cambrian-P +4.7 at 32 f (67.3 -> 72.0), +2.5 at 128 f; VSTI +6.5, camera movement +20.0; pose beats depth (72.0 vs 69.4); T only 70.7, R only 69.7 |
| Auxiliary pose / depth / scale / alignment heads | GeoVR (Qwen3-VL-4B, VGGT teacher, VSI-590K + VLM-3R): pose +3.1, depth +3.0, pose+depth+scale +4.2, alignment only +0.8, all four +5.4 |
| RL with annotations as oracle rollouts | Video-ORA: 9K spatial RL prompts -> 68.1; seven task families, 100K prompts -> 73.1; step cost 2.2x SFT (GRPO with CoT 4.9x). GRPO-only SpaceR collapses on ReVSI (30.5) |
| Frames 32 -> 64/128 | Cambrian-P 72.0 / 73.1 / 73.7 (196 / 64 / 64 tokens per frame); GeoThinker 72.6 -> 73.4; Video-ORA ReVSI 55.8 -> 58.2 (64 -> 128); GeoWeaver ReVSI 57.5 -> 56.9 (32 -> 64). At most +2.4 |
| Training frames | GeoWeaver trains at 8 f; GeoThinker's 8-frame model scores 69.8 at 32 f vs 72.6 for its 32-frame model; SenseNova-SI trains at <= 16 f |
| Typed geometric operators + validity gate | CROSS: ReVSI 55.9 -> 60.2, VSI-Bench 59.8 -> 61.4; context without operators scores 52.8, below direct |

## Pose inside a VLM
- Cambrian-P (LM camera token -> 4-block VGGT-style head; GT + MapAnything sources + ViPE pseudo-poses; 64 H200): ScanNet ATE 0.078 m, RPE rot 0.88 deg on contiguous 90-frame clips, against offline VGGT 0.035 m / 0.38 deg. Its pose-only ablation reads ATE 0.141.
- G2VLM needs a dedicated 518-px, 28-layer DINOv2 geometry expert to approach VGGT: Co3D RRA@30 97.9 / AUC@30 74.8 vs VGGT 99.0 / 88.6.
- CamDistill (a token extractor on intermediate ViT features, cosine-distilled to VGGT-Omega camera tokens) matches injecting the teacher tokens (67.5 vs 67.5 F1), but only on coarse camera-motion classes; tokens placed before the frame's visual tokens beat after (67.5 vs 64.7). Pose as prompt text does nothing (23.1 vs 24.2).
- A probe of Qwen2.5-VL's ViT finds camera-motion cues weak and fading in deeper blocks (arXiv 2603.13119).
