<!-- recovered by seal_plan: transcript=71f94277 line=30795 utc=2026-11-14T10:45:31.550Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ANSWER_bounded_return_fetch_is_sufficient.md heredoc_quoted -->
# ORCH answer: the accepted paced fetch is sufficient; no governor wrapper

The governor rule covers copies into /home and /data*. A bounded return lands on local /scratch, is at most 256 MiB, and is paced at 8 MB/s (40 MB takes five seconds), the same way the step-100 and step-200 returns were fetched. Fetch the step-400 return now with the accepted launcher fetch, unchanged. Build no wrapper.

One condition, already your practice: if main's notice snapshot shows an active pause or download request at fetch time, wait for it to clear before any return above 100 MB. No event in reply; continue to the step-400 packet.