<!-- recovered by seal_plan: transcript=71f94277 line=22608 utc=2026-11-13T16:29:19.627Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/20261113T1633Z_ORCH_ORDER_project_space_attribution_and_rate_alarm.md  -->
# ORCH order (2026-11-13T16:33Z): attribute the project free-space drop, add a rate alarm, raise the candidates list

I read your snapshot of 16:24:58Z. The rate probe (job 169107) is a clear PASS for the slot: 275 MB/s write with sync, 284 MB/s re-read. Put it in the runbook.

Your free-space series shows something else. It was flat near 644.4 GB from 15:45Z to 16:15Z, then 628.0 GB at 16:22:14Z (the probe's own reading before it wrote), 618.7 GB after the probe's 8 GB, 617.8 GB at 16:24:58Z. About 17 GB went in seven minutes before the probe wrote anything, and about 0.9 GB in the 80 seconds after it. At that pace the filesystem would not hold the end slot (111 GB plus the wrapper's 20 GB margin) by tomorrow morning.

1. **Attribute it in your next routine call (one batched call, bounded).** Sizes of our own few folders on the project filesystem that can grow: the persistent root, the kit's `o/` folder, `distill/okit/` top-level entries, and the eval lane's working folders if you know them. No recursive inventory of the staged inputs or of anyone else's space. Tell me whether the drop is ours, and if so which process writes it. If none of ours grew, say so; then it is other tenants of the shared filesystem.
2. **Rate alarm, in addition to the 300 GB and 200 GB lines.** From the series, compute the trailing 30-minute rate at each routine check. Alert me when the projected time to reach 150 GB free is under eight hours, and again under three hours. Alert at 400 GB as well.
3. **The candidates list is no longer lowest priority.** I need `out/PROJECT_SPACE_CANDIDATES_20261113.md` within the hour: what of ours on the project filesystem no kit, run or record needs any more, each with its path, size and why it is safe, largest first, with the total. It is for the user, who alone can remove anything; write a removal script beside it in the same form as the Trinity ones (header DRAFT=1, one guarded line per item, a dry-run mode that only lists). No lane runs it.
4. The eval lane's transfers and reads stay under 20 GB on that filesystem; tell me if they would exceed it.

Production checks stay first. Nothing here changes the running job.
