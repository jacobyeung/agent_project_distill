# Frontier closed models without tools on VSI-Bench-500, ReVSI-999 and VSTI-450 (READ-1b), 2026-11-11

## Question
What do Gemini 4 Argon (thinking high) and Gemini 4 Carbon (thinking medium) score without tools on our three benchmarks under the main project's no-tool harness, so that the 9B student has a measured frontier bar?

## Answer
Without tools and at 32 frames, Argon scores 76.68 on VSI-500, 86.60 on ReVSI-999 and 83.33 on VSTI-450; Carbon scores 75.97, 89.76 and 82.29. Every item of every set has a final answer file; Carbon leaves 4 items unanswered (2 ReVSI, 2 VSTI) after 12 answer attempts each, and the scorer counts them wrong, which costs Carbon at most 0.3 points on ReVSI and 0.4 on VSTI. On ReVSI both models sit about 30 points above the published open models (GeoWeaver-10B 57.5, Video-ORA-9B 58.2), and no open model reports VSTI; on VSI-Bench, Argon's 76.68 on VSI-500 meets ConsiSpace's 76.6 on the full 5,130, which makes VSI-500 the bar a 9B student can most plausibly reach.

## Setting (identical for every cell)
- Input: 32 frames per video, the main project's frame registries (ReVSI: the official 32-frame clips, 380-scene registry; VSTI: the 32-frame `selected_frames_vstibench` registry; VSI-500: r793's sealed 32-frame payloads), each served as 1024x768 LANCZOS JPEG quality 85 with a frame label. 32 is the only count the harness and its prompt ("These are 32 frames sampled in order ...") support; 1 FPS or 64 frames would change the prompt bytes.
- Prompt: main's `prompt_base_756.txt` (ReVSI) and `prompt_base_755.txt` (VSTI), byte-identical; VSI-500 used `prompt_base_2995.txt`, the same bytes (sha 32c72b79...).
- Call: langchain `ChatGoogleGenerativeAI`, temperature 0, `max_tokens` 32,768 (the models' maximum), 900 s timeout, no tools; only the planner model and `thinking_level` differ from main's Gemini 3.1 Pro no-tool configs.
- Scoring: ReVSI with the official ReVSIMetric rule vendored by main (MCQ exact match on the first token; numeric MRA 0.50-0.95; overall = mean of seven collapsed tasks) against main's 32-frame sidecar; VSTI with main's `agent/evaluation/scoring.py` (sha f67703ea...) against `vstibench_repr_450_v3.json` (overall = mean of nine types); VSI-500 with main's pinned scorer (macro over eight categories, direction collapsed). Scorer self-test (ground truth as predictions) gives 100.0 on ReVSI and VSTI.
- Retry policy: provider errors (503/504/timeouts) were retried as fresh attempts; a returned answer is final; a response with no parseable `<ANSWER>` (every one was a 32,768-token cutoff with empty text) was rerun as a fresh attempt, in sweeps of 4, up to 12 answer attempts. Main's VSI-500 cells kept returned answers as final and reran only infrastructure failures.
- Intervals: 95% scene-clustered bootstrap, 2,000 resamples, on the overall score (`ci.py`).

## Results
| Model | VSI-500 (main) | ReVSI-999 | VSTI-450 v3 | Frames | Mean tokens in/out per answered call (ReVSI; VSTI) |
|---|---|---|---|---|---|
| Gemini 4 Argon, high | 76.68 (500) | 86.60 [84.78, 88.45] (999, 0 unanswered) | 83.33 [80.74, 85.73] (450, 0 unanswered) | 32 | 34,380/5,806; 34,382/2,880 |
| Gemini 4 Carbon, medium | 75.97 (500) | 89.76 [88.25, 91.22] (999, 2 unanswered) | 82.29 [79.71, 84.91] (450, 2 unanswered) | 32 | 34,378/6,976; 34,382/9,496 |
| Gemini 3.1 Pro (main, no tool) | 62.8 | 65.9 (64.56 by this scorer on main's r907 bank) | 57.2 on the 5,736 set | 32 | main's 4,096/16,384 caps |
| GPT-6 Astra (third party) | 73.05 on the 5,130 at 1 FPS | - | 70.33 on the 5,736 | 1 FPS | - |
| ConsiSpace (open) | 76.6 on the 5,130 | - | - | 50 | - |
| GeoWeaver-10B (open, our base) | 75.05 on the 5,130 | 57.5 | - | n/r | - |
| Cambrian-P (open) | 73.7 (128 frames), 72.0 (32) on the 5,130 | - | - | 128/32 | - |
| Video-ORA-9B (open) | - | 58.2 (all-frame labels) | - | 128 | - |

ReVSI per task (score, items), Argon / Carbon: absolute distance 75.5 / 81.3 (283); counting 86.4 / 87.3 (135); relative direction 97.1 / 98.3 (68); relative distance 92.3 / 94.0 (140); object size 84.1 / 86.3 (273); room size 81.9 / 84.2 (37); route planning 88.9 / 96.8 (63).

