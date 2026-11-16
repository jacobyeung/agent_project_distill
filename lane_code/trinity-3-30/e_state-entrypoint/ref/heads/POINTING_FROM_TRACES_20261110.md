# 2D text pointing: what ViGoRL ("30k traces") supports, and why ours sits at 61% (research lane, 2026-11-10 07:55Z)

Host trinity-2-18, read-only lane. Sources are cited inline; "unverified" marks what I could not confirm.

## Question
The user read https://visually-grounded-rl.github.io/ as "we could train pointing with 30k traces; we should get good 2D pointing". Does that work support it, what is its recipe, and why does our student's text pointing (T0 m800: 61.2% in-mask in-video) sit far below what it suggests? What recipe should we train?

## Answer
- **The page does not show "good 2D object pointing from 30k traces".** ViGoRL (Sarch et al., CMU, arXiv 2505.23678) uses points as anchors inside reasoning chains. The 30k figure counts MCTS reasoning traces drawn from about 1,500 prompts, used only as an SFT warm start before GRPO. The paper reports no point-in-mask accuracy for its reasoning points. A human study (N=20) judged 72.8% of them to refer to the right region. The only localisation benchmark it reports is GUI point-in-box (ScreenSpot), where plain SFT already does most of the work (Qwen2.5-VL-3B 68.4 -> SFT direct 80.6 -> ViGoRL 86.5).
- **Our gap does not come from too few rows or from the output format.** Our format matches base Qwen's native one (x,y on 0-1000: 66.5% vs 13.5% swapped). The lineage saw roughly as many pointing rows as ViGoRL's warm start, and a pointing-heavy arm did not move placement (Test 3: 58.9% vs 61.2%).
- **Our gap does come from the input and the lineage.** Frames reach the model at 320x416 (10x13 = 130 merged tokens), the video form costs base ~19 points against a single image, and pose-only training eroded base's single-image pointing (66 -> 35%), which T0 only partly recovered (58%).
- **Recommended recipe:** point on one high-resolution re-read of the named frame, training on native-format single-image rows built from our GT masks. Settle resolution first with evalx's zero-training arms (base and T0 at 320x416, at 640x480 and at max pixels).

## Evidence
### External work (ViGoRL)
| Fact | Value | Source |
|---|---|---|
| Base models | Qwen2.5-VL-3B and -7B; frozen teacher Qwen2.5-VL-72B-Instruct for MCTS | paper Tables 1-3, A4; project page |
| Resolution | eval max side 1260 px (SAT-2, BLINK, RoboSpatial), 3600x3600 max (VisualWebArena, V*Bench), 1920x1920 (ScreenSpot-Pro-LR); training max_pixels not reported; multi-turn crop 100x100 resized to 384x384 | paper §5.1.1, Table A3 |
| Traces | "30 k high-quality training traces" linearised from MCTS trees; paper §4.2: ~30k traces from ~1,500 prompts (≈20 per prompt); direct and backtracking ("wait, that seems off") chains; no per-domain split given | project page; paper §4.2 |
| Trace form | each step n = <s, (x,y)>, integer pairs in text; verbatim from A9.2: "I see the name Candice Georgiadis at (330, 440)." Pixel vs normalised is not stated; Qwen2.5-VL grounds in absolute pixels of the resized image, so probably pixels (unverified) | project page; paper A9.2 |
| MCTS cost | 20 simulations/input, depth 10, 3 children, ~21 min per sample, 10 parallel processes | Table A4 |
| SFT | 3 epochs, lr 1e-6 cosine, effective batch 32, vision tower frozen, LlamaFactory | Table A1 |
| RL | GRPO 500 steps, group 5 (multi-turn 8), rollout batch 128, KL 0.01; reward = task success + format bonus (every step must carry a valid coordinate); multi-turn adds +0.2 per new coordinate ≥10 px apart (max 4); 8 A100; EasyR1 | §4.3, Tables A2-A3, A5.4 |
| Task data | SAT-2 32k; OS-ATLAS web grounding 12k (+1.5k warm start); visual search 11k on SA-1B small objects; web action 92 trajectories | §5 |
| Results (3B) | ScreenSpot-V2 68.4 -> SFT 80.6 -> GRPO 84.4 -> ViGoRL 86.5; SAT-2 46.1 -> 62.9; 7B ScreenSpot-V2 73.6 -> 91.0; V*Bench 7B multi-turn 86.4 (base 78.0) | Tables 1-3 |
| Ablation | removing grounding: SAT-2 62.93 -> 58.69; "distillation without MCTS" 63.28 (no loss) | Table 4 |
| Localisation metric | none for reasoning points; human study 72.8% accurate (95% CI 66.8-78.7, N=20); ScreenSpot scores point-in-box | §5.4, §5.1.1 |
| Input | single images (SAT "one or multiple images"); no video; absent objects and duplicate instances not addressed | §3.1, §5 |
| Released | code (MIT), 3B/7B weights per domain incl. MCTS-SFT-only checkpoints, datasets (~181k rows on HF; per-domain trace counts not shown) | github.com/Gabesarch/grounded-rl; hf gsarch/vigorl_datasets |
