<!-- recovered by seal_plan: transcript=71f94277 line=27422 utc=2026-11-14T01:40:29.461Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_CONFIRMED_launcher_step_set_b13c6dcc_submit_step200.md heredoc_quoted -->
# ORCH: launcher step set confirmed (digest b13c6dcc); submit the step-200 read now

Receipt: `/scratch/jjyeung/orch_cd/leg_s1_review/ORCHARD_LAUNCHER_RECEIPT_STEP_SET.json`. Package and submit step 200 once (token bffa0d6ef), producer 8365bd3b, reader fb2796c5. Report the job id and staging as before; put the watch list from my 0115Z ruling in the first lines of the packet.

# ORCH answer to BLOCKER 0140Z (native storage on trinity-0-28)

Do not build a new loading path. Make the ordinary path fit, in this order of preference:

1. **Keep no archives on the node.** Stream the export's parts through the hash and straight into the extractor, so only the extracted members land on `/scratch` (about 21.6 GB, not 43 GB). If the hash at the end of the stream differs, leave the files, move the folder aside under a name ending `_BAD`, and report; never remove it.
2. **Base checkpoint without an archive.** If an extracted copy of the base snapshot already sits on a Trinity node's `/scratch` (the forward probe on trinity-1-8 loaded one), copy that folder node to node over InfiniBand with the tar pipe (`tar cf - ... | ssh <node>.ib "tar xf -"`), which is not rate-limited and reads nothing from the file server. Verify the copied files against the snapshot's manifest. Only if no extracted copy exists, say where the 19.3 GB archive would come from and its cost.
3. **Reserve.** With 1 and 2 the footprint is about 41 GB plus the runtime. I lower the floor on trinity-0-28 `/scratch` from 150 GB to **125 GB free** (the cluster rule asks for 100 to 200), which gives you about 76 GB. Check free space before each stage and stop if another user has taken the margin.
4. **Or another node.** If the dashboard shows an allowed node (never 0-8, 0-23, 3-23; leave 0-18 free) with an empty large card and at least 300 GB free on `/scratch`, prefer it and tell me which; same limits, under vnice.

The runtime closure is the probe's interpreter plus its GPU-site overlay paths, as you say; copy those node to node as well if they already exist on trinity-1-8. State the final footprint before the download starts.