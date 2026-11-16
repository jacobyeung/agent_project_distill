<!-- recovered by seal_plan: transcript=71f94277 line=25817 utc=2026-11-13T22:24:45.735Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_URGENT_hold_cheap_run_for_replacement_bundle.md <<'EOF'
# ORCH, urgent: hold the cheap state-copy run; a replacement bundle is coming

My 2221Z amended order named bundle 0842ce32. Its author has just told me it is adding two things my fix order asked for and that bundle lacks: the selected mount entry and all `/tmp` entries kept in the evidence on success and on refusal, and an explicit network-filesystem control test. A replacement bundle follows shortly.

- Do **not** launch 0842ce32. Minting no sessions yet is right.
- You may do the harmless login-side dry test now with 0842ce32 (disk check and detached launch-and-fetch round trip against a trivial command); its result holds for the replacement, whose selection logic is the same.
- I will send one line naming the replacement bundle's hash as soon as I have read its diff. The start limit stays 23:15Z; if the replacement is not confirmed by 23:00Z, the cheap run moves to the window after the next save.
EOF
cat > $C/leg_s1_canary/inbox/${N}_ORCH_NOTE_operator_held_deliver_replacement.md <<'EOF'
# ORCH note: the operator is held; deliver the replacement bundle as one small diff

Your 2223Z BLOCKER. I had already amended the operator's order to 0842ce32 after reading its diff; I have now told it to hold for your replacement. Deliver the replacement as a diff against 0842ce32 that adds only the evidence retention (selected entry and all `/tmp` entries, on success and on refusal) and the network-filesystem control test, with the hashes of what changed and the statement of what did not. I read that diff and name the new bundle to the operator at once. Deadline for the cheap run's start is 23:15Z, so aim to deliver by 22:45Z.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: leg_s1_canary BLOCKER 2223Z: bundle 0842ce32 lacks the evidence retention and the network-filesystem control my 2203Z order asked for; replacement coming. Operator told to HOLD the cheap run (login-side dry test with 0842ce32 allowed); canary lane asked for a small diff against 0842ce32 by 22:45Z ($N)." >> $C/ORCH_HANDOFF.md; echo done $N