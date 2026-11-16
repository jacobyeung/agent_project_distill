# Lane native_r5 (runs on trinity-1-3): successor of lane native_r4, operator of the first official native read (VSTI-450, camera calls only)

Lane folder: the predecessor's, /scratch/jjyeung/orch_n30/native_r4 on trinity-1-3. Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r4/ (write your events and STATUS.md mirror there). First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are an operator: code changes go to Codex as the rules describe.

## Why
The step-544 student writes programs that tools serve inside generation; on dev-S1 its camera programs score 82 to 95 against 13 to 53 for direct-answer models. No official benchmark has been read that way. This job reads VSTI-450 with only camera calls served, which is legal before the project's re-freeze; closed-model bars and f17 / P1 m200 comparators exist on the same items.

## Start
Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r4/STATUS.md ("Next steps") and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r4/20261116T1011Z_RESULT_rotate.md, then my files there, newest first: *_ORCH_GO_conditional_vsti.md (the conditional GO and its four conditions, and the reporting rule), *_ORCH_NOTE_queue_rules.md (shortest honest wall time, --nice=200, deadline 16:15Z), *_ORCH_ORDER_kit_fixes.md, *_ORCH_NOTE_orchard_primary.md. Kit V1c is built and its fixes are with a second reader (lane review_vsti2), whose CONFIRMED_dc40cf60.md will appear in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_vsti/. The predecessor's uploads (frames b.tar, reference d.tar) run in tmux nr4_upb and nr4_upd2 on this node: never duplicate them.

## Do
1. Finish the packet as STATUS.md describes: GCS copies from Orchard, the packet under the opaque project folder, every input verified by hash on Orchard. RESULT event named packet.
2. Submit under the conditional GO when all four conditions hold; RESULT with the job id and name at once. If a condition fails or the reader does not confirm: BLOCKER and wait.
3. Watch with one small poll every 5 minutes until the dev-S1 proof and the canary have returned, then every 10 minutes. Report in separate RESULT events: the proof's outcome; the camera types when their 100 items are done (per type: items, call, served and refused counts, score with its interval over scenes, beside f17 and P1 m200 on the same items); the full read at the end with the per-type table, the refused-call cost (items that emitted a non-camera call, what the student answered after the refusal, their score), the proof outcome and the frames line. Fetch returns through the governor. If the job stops at its deadline with items left, say what is missing and prepare the resume job; it needs my word.
4. Keep the record /data2/jjyeung/agent_project_data/distill_design/VSTI_NATIVE_CAMERA_READ_STEP544_20261116.md current.

## Limits
One job under the conditional GO; no other Orchard job, no VSI-Bench or ReVSI item, no object-grounding call served on a VSTI item, no paid key, no Git, no deletion. Your session ends after 6 hours: a RESULT event named rotate before then or at 60% of your context.
