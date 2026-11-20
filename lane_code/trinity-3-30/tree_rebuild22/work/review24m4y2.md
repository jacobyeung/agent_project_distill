# Narrow review (read-only, once) of rcj helper build 24m4y2 of lane tree_rebuild: only the two findings of the full kit review rev24m4x2c, as ORCH ANSWER 1938Z settled them

You review; you do not fix. Run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, with file:line and evidence. Your final message is the verdict. ORCH ANSWER 1938Z item 3 limits this review to the two points below. The rest of kit 24m4x2 (tree 9d2bbb8a, kits q df93cfba, n 797255ae, n_go aa2d1267, qd 8ae781f4) was reviewed in full by rev24m4x2c (codex_runs/*_tree_rebuild_rev24m4x2c/final_message.md), which raised only these two findings.

- Build: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y2/`. Read the prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24m4y2.md`, which quotes ANSWER 1938Z. Also read out/BUILD24M4Y2_REPORT.md, out/UPLOADS_24M4Y2.json/.list, out/RCJ_FILES_24M4Y2.sha256, out/rcj/ and work/build24m4y2/ (REPLAY173817.json, CONTROL_REAL_STORE.json, REFERENCE_SOURCE.json, DECISION_TESTS.json, VALIDATION.json, PACKAGE_CHECK.json). The base is 24m4x2 at `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24x2/`. Only rcj x.py, nd.py, ch.py and f.json changed.
- Real-path evidence:
  - Before: candidate CPU job 173817 (24m4x2 helpers), `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173817/173817/`: post_returncode 1, rdiff_returncode 1, nd task_i FAIL from the literal diff, and the third control with origin sealed_reference.
  - After: candidate CPU job 173864 (24m4y2 helpers), same `rcj.sh r` command, `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173864/173864/`.
  - The kit qd seal is identical in both jobs; only the rcj helpers differ.
- Point 1 (ANSWER 1938Z item 1): verify all of the following.
  - The exit status is 0 iff every mode-r step passes and task A (a), (b) and (c) pass; (d) is reported as DEFERRED_TO_DISCOVERY.
  - (a)'s field list is derived from the tree code with file:line, and it covers every field that reaches the encoded example (prompt ids, target ids, frames, masks, spans), plus the raw SQL target, over all rows.
  - Any difference in those fields or in the target fails (a), with examples.
  - The literal whole-row diff stays published, labelled as information superseded by ANSWER 1226Z, with counts by class.
  - rd0 stays informational.
  - 173864 shows these results on the real rows.
- Point 2 (ANSWER 1938Z item 2): verify all of the following.
  - The third control uses a real Orchard row if any staged store holds one.
  - Otherwise the sealed reference is a real row's bytes, with its source store and sha256 named. Its source is not on the exemption list, and it has no a0_ prefix and no r1_source.
  - The run publishes the gate-required, exempted and receipt-entry counts, and their sum holds.
  - Check this against 173864's chain.json.
- Also verify: the changed rcj files' sha256 equal RCJ_FILES_24M4Y2.sha256 and UPLOADS_24M4Y2; no tree or kit file changed versus 24m4x2; and nothing in the change weakens a check (no refusal that 173817 raised for a reason other than these two findings now passes). Also list what you did not check.

Rules: Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). nice -n 10, at most 8 threads, under 20 GB RAM. First line `GO`, `GO AFTER FIXES` or `NO-GO`; at most 14 lines.
