<!-- recovered by seal_plan: transcript=71f94277 line=27422 utc=2026-11-14T01:40:29.461Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; M=$C/evalx/work/milestone; H=$(sha256sum $M/orchard_launcher.py | cut -c1-64); cat > $C/leg_s1_review/ORCHARD_LAUNCHER_RECEIPT_STEP_SET.json <<EOF
{
  "verdict": "ACCEPT",
  "reviewer": "orchestrator orch-home-distill-79 (Claude family; the author is a GPT-family lane). A diff read on top of the independent launcher review and my receipts ORCHARD_LAUNCHER_RECEIPT.json, _MOUNT_FIX.json and _LINK_FIX.json; not a new full review.",
  "code_pins_sha256": "b13c6dcc7b38c8fa5b28876d44f24f135da9e45f87953f6f7377009d3de9f9f7",
  "previous_code_pins_sha256": "50deb48967c55fcf7975fabc61f4042598959f3276866576f074acc93ac5ea7e",
  "diff": "/scratch/jjyeung/orch_cd/evalx/work/milestone/STEP200_LAUNCHER.diff (sha256 62f440cb..., one line in orchard_launcher.py prepare(): admitted steps (50, 100) -> (50, 100, 200, 400))",
  "orchard_launcher_py_sha256_now": "$H",
  "what_i_checked": [
    "read the diff: only the step tuple changes; the artifact-hash, artifact-step and source-seal bindings on the same condition are untouched",
    "the review request lists seven pins; orchard_launcher.py is the only file whose pin differs from the accepted set by the author's statement, and its current hash is recorded above",
    "the author's log shows 20 launcher tests passing, including refusal of step 150 and of a transport/artifact step mismatch; I did not rerun them"
  ],
  "producer_for_step_200": "8365bd3b (the accepted producer; no overlay path added)",
  "issued_utc": "$(date -u +%Y-%m-%dT%H:%MZ)"
}
EOF
cat > $C/evalx/inbox/${N}_ORCH_CONFIRMED_launcher_step_set_b13c6dcc_submit_step200.md <<'EOF'
# ORCH: launcher step set confirmed (digest b13c6dcc); submit the step-200 read now

Receipt: `/scratch/jjyeung/orch_cd/leg_s1_review/ORCHARD_LAUNCHER_RECEIPT_STEP_SET.json`. Package and submit step 200 once (token bffa0d6ef), producer 8365bd3b, reader fb2796c5. Report the job id and staging as before; put the watch list from my 0115Z ruling in the first lines of the packet.

# ORCH answer to BLOCKER 0140Z (native storage on trinity-0-28)

Do not build a new loading path. Make the ordinary path fit, in this order of preference:

1. **Keep no archives on the node.** Stream the export's parts through the hash and straight into the extractor, so only the extracted members land on `/scratch` (about 21.6 GB, not 43 GB). If the hash at the end of the stream differs, leave the files, move the folder aside under a name ending `_BAD`, and report; never remove it.
2. **Base checkpoint without an archive.** If an extracted copy of the base snapshot already sits on a Trinity node's `/scratch` (the forward probe on trinity-1-8 loaded one), copy that folder node to node over InfiniBand with the tar pipe (`tar cf - ... | ssh <node>.ib "tar xf -"`), which is not rate-limited and reads nothing from the file server. Verify the copied files against the snapshot's manifest. Only if no extracted copy exists, say where the 19.3 GB archive would come from and its cost.
3. **Reserve.** With 1 and 2 the footprint is about 41 GB plus the runtime. I lower the floor on trinity-0-28 `/scratch` from 150 GB to **125 GB free** (the cluster rule asks for 100 to 200), which gives you about 76 GB. Check free space before each stage and stop if another user has taken the margin.
4. **Or another node.** If the dashboard shows an allowed node (never 0-8, 0-23, 3-23; leave 0-18 free) with an empty large card and at least 300 GB free on `/scratch`, prefer it and tell me which; same limits, under vnice.

The runtime closure is the probe's interpreter plus its GPU-site overlay paths, as you say; copy those node to node as well if they already exist on trinity-1-8. State the final footprint before the download starts.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx RESULT 0140Z: launcher step-set diff (one line; seven-file digest b13c6dcc; 20 tests). I READ THE DIFF: ACCEPT (leg_s1_review/ORCHARD_LAUNCHER_RECEIPT_STEP_SET.json); told evalx ($N) to submit the step-200 direct read now (token bffa0d6ef, producer 8365bd3b). evalx BLOCKER 0140Z: the native loader needs the 19.3 GB base checkpoint plus 43.2 GB for the export and its extraction (> 62 GB before the runtime) against 51.5 GB allowed on 0-28. ANSWER (same note): no new loading path; stream-extract the export (no archive kept), copy an already-extracted base snapshot and runtime node to node over InfiniBand, floor on 0-28 lowered to 125 GB free, or use another allowed node with >= 300 GB free. Re-armed evwait (b8jb4gm28)." >> $C/ORCH_HANDOFF.md; echo $N