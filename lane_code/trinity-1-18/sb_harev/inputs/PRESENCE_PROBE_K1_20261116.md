# Presence probe on K1: is step 544's own per-frame presence a head path for appearance order and counting? (2026-11-16)

## Question
Does a small head over step 544's own per-frame presence logits answer appearance order (and counting) better than step 544's direct answer? Decision rule fixed in brief 11 (`orch_n30/briefs/qs/11_presence_probe.md`): appearance order gets a head-path minority in the next rows build only if the head beats direct by at least 10 task points on K1 held-out with the paired 95% interval above zero.

## Answer
No. Appearance order stays direct. On 143 held-out K1 items the pre-registered head (arm I) scores 32.87 against 71.33 for direct (B2048), difference -38.5, room-cluster 95% interval [-48.0, -28.9] over 32 rooms. Counting by presence runs fails too: head 25.0 against direct 64.3, and the GT-presence run program itself scores 24.8, below the constant 53.4.

## Evidence
- Report: trinity-1-18 `/scratch/jjyeung/orch_n30/b11_presence/out/PRESENCE_PROBE.md`; analysis `out/analysis/{FROZEN,ANALYSIS_train,ANALYSIS_heldout}.json` (sha f46e7cae, 49e00f24, 59232ace); journals `from13/out/` (pull manifest verified).
- Per-frame AUROC on held-out: I 0.933, Y 0.930, V 0.622. First-seen exact (head, arm I) 0.541, within one frame 0.650; 19% early, 28% late.
- Secondary (not decisive): choosing the option by pairwise ordering likelihood under the head reaches 60.8 (I) and 72.0 (V), so at best it ties direct.
- Direct read UNCLAIMED: vLLM 0.23.0, not the accepted 0.32.0. A prompt shim makes engine token ids equal the trainer's (parity 16/16). K1 rooms are training rooms, so direct may be inflated; step 544's official VSI appearance-order score is 66.18.
- Reviews: Codex gpt-6-astra, read-only. Rounds 1-3 returned NO-GO and every finding was fixed; round 4 returned GO; round 5, on the vLLM-0.23 shim, returned GO AFTER FIXES and the fixes landed. Receipts are in `agent_project_distill/agent/scratch/codex_runs/*_b11_review*`.

## Options rejected and why
- First-above-threshold rules (thr0, thrfit): these put a threshold outside the weights. As references they score 21.0 and 35.0.
- Kendall nearest-option answering: the reviewer rejected it because it answers orders that no option contains. Exact match is the rule.
- Counting by category-presence runs: even with GT presence this program sits below the constant. Category presence carries no instance identity.

## What might not work, and how we would notice
- The head ranks objects one at a time; a joint ordering read-out might do better. head_optlik on V is the hint. Re-read it only after presence training and with a pre-registered rule.
- K1 is training rooms. A non-training-room set with GT visibility would show whether direct's 71.3 holds; official VSI is 66.18.
- The direct read ran on vLLM 0.23, so a trin_read read on 0.32.0 would replace it for any claim.

## Tests that would settle it
Repeat after presence training on held-out rooms, using the accepted runtime for direct and the same frozen-on-train protocol (`code/analysis.py` fit then `--read-heldout`).

## Status
Done 2026-11-16; decision: no head path for appearance order. Counting needs instance grounding (brief 12 rows, own grounding head), not presence.
