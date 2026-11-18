<!-- recovered by seal_plan: transcript=71f94277 line=24124 utc=2026-11-13T19:13:50.184Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/leg_s1_canary/inbox/${N}_ORCH_RULING_state_copy_without_save_handshake.md <<'EOF'
# ORCH ruling: design the state copy without a producer handshake; the limitation is accepted

Your 1912Z question. Ruling: **yes.** The design may rest on a fresh, immutable complete-state snapshot, a conservative deadline before the next due save, monitoring for a concurrent save, and end-to-end content verification, with literal proof that no save has begun marked as not established. Reasons:

- A complete state is immutable once its `complete.json` exists. A new save writes a new folder with its own UUID and does not touch the one being read. Rotation renames a state into `_superseded/` only after two later completions (your reading of the sealed source), which is at least four hours after it was written.
- So the only interaction between a copy and a save is competition for the node's disk and CPUs. Bound it and report it; do not try to exclude it.

Conditions the design must state and enforce:

1. Start only after a save has completed: the newest folder with `complete.json`, checked against the four-rank metrics record of that step, and at least two minutes old.
2. Finish before the next save is due (7,200 s interval): give the copy's expected duration from measured rates (archive write to node-local disk, SHA256, upload at the measured 433 MB/s over four parts) and refuse to start if less than three times that duration remains before the due time.
3. Read by open handles where possible, so that a rename of the folder during the copy cannot break it; verify every member against `complete.json` and the wrapper's member rules at the end; if a new checkpoint folder appeared during the copy, record it and still finish.
4. Resource bounds for the step, and what its page cache counts against (I have asked the operator for the facts in your points 1 to 4; you get them through me). If the step's memory limit includes page cache, say how reads and the node-local archive write behave under it and choose the limit accordingly.
5. The archive on node-local disk is left in place; nothing is removed by any agent.

A second, cheaper variant is worth one paragraph in the design: copy only `inputs/` and `binding.json` (2.7 GB) plus the checkpoint's small records now, as a first rehearsal of the whole path with almost no load, before the full state.

Post the design as a RESULT when it is ready; build only after my word. The checker's remaining work waits behind this.
EOF
cp $C/leg_s1_canary/events/20261113T1912Z_QUESTION_state_copy_facts_and_save_guard.md $C/orchard_cp2/inbox/20261113T1912Z_QUESTION_leg_s1_canary_state_copy_facts.md
cat > $C/orchard_cp2/inbox/${N}_ORCH_NOTE_answer_canary_fact_questions.md <<'EOF'
# ORCH note: answer leg_s1_canary's four fact questions (copied into your inbox as 20261113T1912Z_QUESTION_leg_s1_canary_state_copy_facts.md)

They refine the facts I asked for at 1836Z (session minting, checkpoint retention, save times). Answer points 1 to 4 from records you hold where you can; for what needs the node, add it to the read-only health step or your next routine call, within the limits already set. No credentials or session content in the answer. Post one RESULT to me and I route it. The retention question is settled from the source (the two newest complete states stay at the run root; older ones are renamed into `_superseded/`, not deleted), so you need not answer that one.

Your order of work stays: production checks; the donor row scan (the r2 operator file is in your inbox; my 1839Z conditional go stands); these facts; the checker's fixture.

Free space rose to 359.0 GB at 19:06Z and held at 358.8 GB at 19:11Z. Preallocation is closed (your 1905Z RESULT); thank you for not trying a size-changing fallback.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: tick 19:13Z ALL OK. leg_s1_canary QUESTION 1912Z: facts needed from the operator (minting tool/TTL/overwrite policy; newest completed periodic save evidence; whether an in-job step has its own cgroup memory limit incl. page cache; rank stdout FD target and unbuffered flag); retention settled from source (rotate keeps the two newest complete states, older ones renamed into _superseded/, not deleted); asks whether the state copy may proceed without a save-in-progress handshake (the source has none). RULING ($N): YES: fresh immutable complete state, start >= 2 min after complete.json, refuse unless 3x the copy duration remains before the next due save, read by open handles, verify against complete.json at the end, record a concurrent save, node-local archive left in place; add a cheap first variant (inputs/ + binding + small records, 2.7 GB) as a rehearsal. Fact questions routed to orchard_cp2. Project free 358.8 GB at 19:11Z (holding)." >> $C/ORCH_HANDOFF.md; echo done $N