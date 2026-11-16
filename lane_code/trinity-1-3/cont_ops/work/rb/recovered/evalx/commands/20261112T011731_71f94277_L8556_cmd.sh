<!-- recovered by seal_plan: transcript=71f94277 line=8556 utc=2026-11-12T01:17:31.272Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ)
cat > leg_s1_tree/inbox/${T}_ORCH_ANSWER_resume_inputs_and_signal.md <<'EOF'
# ORCH answer: resume inputs, signal reserve, job start time
Yes to all three. (1) The alternating-slot state archive carries `<RUN>/inputs` and `binding.json` together with the checkpoint, and the restore verifies their pins before the mode chooser runs; I am telling orchard_cp2 now. (2) Use the 3,600-second reserve (Orchard node /tmp does not survive between jobs, so the save, the copy to /home and its verification all happen inside the leg); the 900 in my earlier note is superseded. (3) The wrapper sets `TK_JOB_START` before state restoration. Put all three in the kit's contract with orchard_cp2's wrapper and in REVIEW_PACKET.md.
EOF
cat > orchard_cp2/inbox/${T}_ORCH_slot_archive_contents.md <<'EOF'
# ORCH: three requirements from leg_s1_tree for your wrapper (its event: /scratch/jjyeung/orch_cd/leg_s1_tree/events/20261112T0116Z_QUESTION_resume_inputs_and_signal.md)
1. The alternating-slot state archive must hold `<RUN>/inputs` (derived config, pointing database, MDG index, rebuilt confusers, preparation receipt, phase journal) and `binding.json` along with the newest complete checkpoint; their pins enter the checkpoint binding, so a node without them cannot resume. Restore all of it before `r8.py` runs.
2. Signal reserve 3,600 seconds, as in your draft.
3. Set `TK_JOB_START` in the wrapper before state restoration, so staging, admission and training share the allocation's wall clock.
Agree the exact paths with leg_s1_tree through its inbox. No answer to me needed unless something conflicts.
EOF
tail -n 3 evalx/work/inbox_seen.txt; ls -t evalx/events | head -2; sed -n 1,3p evalx/STATUS.md | cut -c1-600