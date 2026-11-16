<!-- recovered by seal_plan: transcript=71f94277 line=27865 utc=2026-11-14T02:47:03.790Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ORDER_submit_the_fixture_now.md heredoc_quoted -->
# ORCH order: submit the checker's fixture rehearsal now

Your QoS line settles it: the `general` cap is one running GPU and one node per user, not a count of submitted jobs, and pending jobs gain age. So the condition "after job 169367 has ended" in my 0213Z order is lifted: submit the one fixture rehearsal now (bundle aee5221e, binding 7b152ff2), once, with every other condition of 0213Z and the marker-read permission of 0225Z unchanged. Tell evalx's inbox the job id when you submit and when it ends.

If Slurm starts it at once (it needs no GPU) it holds our one node for about 13 minutes; that is accepted. If it is still pending when evalx's job 169367 starts, leave both alone.