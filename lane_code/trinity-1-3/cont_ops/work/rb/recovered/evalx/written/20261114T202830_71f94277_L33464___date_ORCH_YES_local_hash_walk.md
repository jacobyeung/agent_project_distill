<!-- recovered by seal_plan: transcript=71f94277 line=33464 utc=2026-11-14T20:28:30.869Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_YES_local_hash_walk.md heredoc_quoted -->
# ORCH: yes, run the reuse validation now

Approved as you describe: one serial command at low CPU and IO priority, about 3 GB of reads on local /scratch, hard links instead of a second copy, fresh extraction of only the code object and the step-544 artifact metadata.

Standing rule for the rest of this task: reads of files on this node's local /scratch up to 20 GB in one serial low-priority command need no clearance from me. The ask-first rule is for /home and /data* and for large writes.

The CPU checks you report (all 300 admitted operands pass the runtime universe; nine normal streams byte-identical; the runaway stops after 2,048 sampled tokens, the forced close, 64 answer slots and end of sequence) are what I asked for. Send the diff event as soon as the validation is done so the review can start.