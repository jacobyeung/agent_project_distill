# Gemini-native labelling format vs the Astra-style prompt, for Argon and Carbon (11-11)

Lane gemini_native (Devin), trinity-2-18. Lane folder /scratch/jjyeung/orch_cd/gemini_native (work/ code, out/ results, notes/GEMINI_PRACTICES.md the doc passages with URLs). Labels are review-only.

## Question
label_argon's labelling prompt was written for Codex Astra: ruler margins on every frame, coordinates read off the ruler, about 12 queries per call, and a draw-and-check round. Does a prompt and packet format built from Google's own Gemini practice for boxes and points label better, for gemini-4-argon (thinking high) and gemini-4-carbon (thinking medium and high)? Which prompt and model should label 24/7?

## Answer
Use the native format, with Argon at high and Carbon at medium, the same two models label_247 runs now. The native format labels as accurately as the old prompt, and for Carbon better: on the adjudicated P7 rows Carbon medium agrees with the blind Opus verdict 9.7 pt more often than label_argon's Carbon run (67.3% vs 58.3%, paired +9.7 [3.7, 15.9]), and it reaches 99.6% identity precision on P1 gold. For Argon the format changes no accuracy measure beyond noise. The native format costs much less: per query it sends 3.1-3.6x fewer prompt tokens, and it spends 2.4x (Argon) and 10x (Carbon) fewer thought tokens, with no MAX_TOKENS failures. Carbon at high does not pay: it is no more accurate than medium in either format and loses 3-12% of items to the 32,768-token cap. The switch for label_247 is out/LABEL247_SWITCH.md.

## The format (work/native_run.py, work/native_p7.py, work/prompts/)
Each practice below comes from the official docs; notes/GEMINI_PRACTICES.md quotes them.
- One photo per call, so P7 averages 5.7 queries per call and P1 2 (Gemini 3 prompting guide; robotics and spatial cookbook examples). The ruler margin is cropped off.
- The photo comes first and the text after it. The generateContent edition of the image-understanding page says to "place the text prompt after the image"; the files prompt guide says to "put your image first". The Interactions-API edition of the same page says the reverse, but we call generateContent. The question comes last ("Place your specific instructions or questions at the very end").
- Role, task rules and output rules go in the system instruction ("Prioritize critical instructions ... in the System Instruction"). The rule text is p7_teacher.md and prompt_label.md with the ruler and tool steps removed, so the verdict, defect, presence, box, point, count, confidence and reason fields keep their meaning.
- Boxes are box_2d [ymin, xmin, ymax, xmax] and points are [y, x], both on 0-1000 (object-detection page; robotics pointing page). A converter maps answers back to [x0, y0, x1, y1] and [x, y], so every existing scorer runs unchanged.
- The response is constrained by responseJsonSchema with enums and descriptions (structured-output page).
- Each image is sent at media_resolution HIGH, the documented recommendation for images. It equals the Gemini 4 default of 1,120 tokens, and a probe confirmed the same prompt token count without it.
- The proposal is shown as its outlined image (ruler cropped) plus its blue box as box_2d and its point as [y, x] in the query text. The box is read from the blue pixels of the proposal image and matches the private shown_box within 2.6 grid units on 1,827 of 1,828 proposals; no private map or ground truth enters a request.
- There is no draw-and-check round and no temperature setting (Gemini 4 ignores temperature).

## Evidence
Arms: native Argon high, native Carbon medium, native Carbon high, plus the old prompt bytes on the same per-frame and per-image sub-packets (work/old_run.py, which imports label_argon's argon_run.py unchanged, with the check round) at Argon high, Carbon medium and Carbon high. The references are label_argon's runs (old prompt, whole-unit packets): Argon high and Carbon medium. All arms ran 08:00-11:05Z on the same key beside label_247, with zero 429s in 4,252 calls. The old Carbon arms were cut short by the orchestrator's 11:04Z PAUSE (old Carbon medium P7 333 of 353 frames, old Carbon high P7 76).

### P1: 480 blind queries, extended gold (out/p1/P1_NATIVE_SCORES.json; work/p1_native_score.py reproduces label_argon's 96.8% and 98.2%)
| Arm | identity precision [room CI] [frame CI] | false presence [frame CI] | visible coverage | box IoU vs mask | unlabelled |
|---|---|---|---|---|---|
| Argon, old, whole room (label_argon) | 96.8 [93.6, 99.3] [94.5, 98.7] | 2.7% (5/184) [0.6, 5.3] | 94.6 | 0.882 | 0 |
| Argon, old, per image | 99.0 [97.4, 100] [97.8, 100] | 1.6% (3/183) [0, 3.8] | 95.0 | 0.866 | 0 |
| Argon, native | 98.9 [97.7, 100] [97.6, 100] | 1.1% (2/181) [0, 2.7] | 92.5 | 0.858 | 0 |
