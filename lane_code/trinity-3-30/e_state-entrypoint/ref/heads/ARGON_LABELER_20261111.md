# Gemini 4 Argon and Carbon as 24/7 image labelers on the shared Gemini key, against Codex Astra (11-11)

Lane label_argon (Devin), trinity-2-18. Lane folder /scratch/jjyeung/orch_cd/label_argon (work/ code, out/ results, events/).

## Question
Can gemini-4-argon (thinking high), called directly on the shared Gemini key, replace Codex gpt-6-astra as the image labeler that audits teacher rows, and how does gemini-4-carbon compare? Should the 24/7 labeler be Argon, Carbon, or both as an agreement filter?

## Answer
Argon matches or beats Astra on two of the three qualification tests and misses the third by a small margin. Carbon passes all three, but it runs slower and fails on 2.8% of units. The best 24/7 labeler is Argon and Carbon together as an agreement filter: their verdicts agree on 92.9% of rows, and on those rows the estimated accuracy is 96.9%, compared with an estimated 95.0% for Argon alone and 92.8–93.0% for Astra. Argon alone is the fast option when one model has to do the work. All labels stay review-only.

| Test | Astra (label_ops) | Argon (API) | Carbon (API, thinking medium) | Criterion |
|---|---|---|---|---|
| P7 sentinels rejected | 147/153 (96.1%) | 149/153 (97.4%) | 148/151 (98.0%) | ≥ Astra − 3 pt: both pass |
| P1 gold identity precision (extended gold, room CI) | 95.5% [92.3, 98.1] | 96.8% [93.6, 99.3] | 98.2% [96.4, 99.6] | within Astra's CI or better: both pass |
| P1 gold false presence | 0.6% [0, 1.8] (1/174) | 2.7% [0.5, 5.7] (5/184) | 0.6% [0, 1.8] (1/179) | within Astra's CI: Argon fails, Carbon passes |
| Adjudicated P7 disagreements vs Astra (blind Opus) | — | Argon right 64.8% [56.4, 72.1] (94/145) | Carbon right 53.8% [45.2, 62.3] (78/145) | wins or ties: Argon wins, Carbon ties |
| Argon vs Carbon disagreements | — | Argon right 71.4% [58.3, 84.0] (35/49) | | |

## Evidence
### Runner (work/argon_run.py)
- Each request carries the same packet images and the same prompt bytes as Astra's run: P7 used label_ops work/prompts/p7_teacher.md (sha ffda213b…) and P1 used the swarm_ops prompt_label.md (sha e45355e5…). After the prompt comes a fixed API adapter paragraph, which replaces the file and tool instructions with "reply with the labels.json object". One request goes out per packet. For P7 a second turn follows: the runner runs the packet's draw.py on the first answer and sends the check images back, the same self-check the agentic labelers ran.
- The runner can resume each unit, logs every call (tokens, latency, HTTP status) in out/…/jobs/JOB/calls.jsonl, gives each unit at most 2 attempts, halves concurrency when 429s exceed 2% over 5 minutes, and raises concurrency to out/…/CONC_TARGET only while 429s stay under 1%.
- The check round matters for Argon. Its first answers misread the ruler margin, so the boxes shifted by about the 36-px margin. After the check round, Argon's box IoU against Astra rises from 0.841 to 0.884 and its IoU against the teacher box on accepted rows rises from 0.905 to 0.949; verdict agreement changes by only 0.5 pt (out/p7_compare_labels_t1).
- Carbon at thinkingLevel high spent the whole 32,768-token output cap on thoughts in 9 of its first 11 calls. A thinkingBudget of 24,576 did not bind: 6 of 7 calls still ended at 32,765 thought tokens, with a median call of 392 s. Following the orchestrator's rule, the Carbon arm runs at thinkingLevel medium. The failed calls stay logged in out/carbon and out/carbon_b24k.

### A. P7 head-to-head (4,918 queries, 396 units, 153 sentinels; out/p7_compare/P7_COMPARE.json, rows.jsonl)
Argon labelled all 4,918 queries; Carbon labelled 4,780, because 11 units failed twice with MAX_TOKENS. The table gives verdict agreement with frame-cluster CIs and box IoU between the two labelers' boxes.

| Class | n | Argon–Astra agree | Carbon–Astra agree | Argon–Carbon agree | reject rate Astra / Argon / Carbon | box IoU Ar–As |
|---|---:|---|---|---|---|---:|
