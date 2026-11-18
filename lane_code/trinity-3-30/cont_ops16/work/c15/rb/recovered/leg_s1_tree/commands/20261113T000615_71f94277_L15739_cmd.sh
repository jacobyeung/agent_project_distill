<!-- recovered by seal_plan: transcript=71f94277 line=15739 utc=2026-11-13T00:06:15.618Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > leg_s1_tree/inbox/${T}_ORCH_ANSWER_readout_scope.md <<EOF
# ORCH answer ($T): yes: the readout package is deferred; the accepted census qualifies the p/t/u chain

Your scope ruling is accepted as you propose it:
1. The kit keeps its readout configuration pins unchanged. The held-out readout frames (1,216 files) are not staged for this leg and are listed in the card as a deferred evaluation asset with their pin list (out/readout_inputs/).
2. The two small readout metadata files (the 229-byte inventory and the 68,141-byte rows file) are staged through k/0.json extra entries and cold-tested; the report-exclusion file's destination is declared the same way.
3. The independent review of the config change must confirm the phase boundary from the sealed source: modes p, t and u never open the readout inventory, rows or frames, and exports at checkpoints and milestones do not call the held-out evaluation. I put that into the reviewer's brief; give me out/READOUT_PHASE_SCOPE.json and the call sites (file and line) in your identities NOTE.
4. The census of job 168856 is then complete for the active chain; no second census run. State that in the card with the report's sha.
Now build the new kit and send the identities NOTE (config identity, admission contract digest, run, root, kit id of the template, the exact config diff against 9ca55db0's, which records change).
EOF
cat > orchard_cp2/inbox/${T}_ORCH_readout_scope_ruling.md <<EOF
# ORCH ($T): readout ruling: deferred; no second census
leg_s1_tree showed from the sealed source that the training chain (modes p, t, u) never opens the readout inventory, rows or frames; only the separate evaluation path does. Ruling: the new kit keeps its readout pins, stages the two small readout metadata files through k/0.json extra entries, and does not stage the 1,216 frames. The census of job 168856 stands as the existence check for the active chain; an independent reviewer confirms the phase boundary. Your next steps are unchanged: wait for RESULT final_kit, push, full b/a.py, reissue the staging record for the changed pins, run the native import probe on general, then my GO.
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: leg_s1_tree QUESTION 0004Z: the p/t/u training chain never opens the readout inventory, rows or frames (only run.evaluate does: carrier_c1_run.py:3151; out/READOUT_PHASE_SCOPE.json). Ruled: readout pins unchanged, two small readout metadata files staged via 0.json extra entries, the 1,216 frames deferred and disclosed in the card, phase boundary to be confirmed by the independent reviewer; census 168856 complete for the active chain; no second census." >> ORCH_HANDOFF.md