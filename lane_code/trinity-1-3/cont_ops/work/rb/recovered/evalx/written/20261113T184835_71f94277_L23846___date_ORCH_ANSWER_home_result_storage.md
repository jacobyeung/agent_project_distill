<!-- recovered by seal_plan: transcript=71f94277 line=23846 utc=2026-11-13T18:48:35.781Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ANSWER_home_result_storage.md heredoc_quoted -->
# ORCH answer: small result archives under Orchard /home are approved, with caps

Approved: `/home/jjyeung/okit/evalx_results/<token>/` on Orchard for the compressed result archive and exit receipt of each read.

- At most 64 MiB per read and 512 MiB in total under that folder. The user's home quota on Orchard is 25 GB and it filled once (2026-11-04), which blocked the user's login; nothing else of yours goes under `/home` there, no caches, no logs beyond the exit receipt.
- If a write there fails for quota or space, mark the return incomplete (as you plan) and tell me; do not fall back to another location on your own.
- Fetch each archive to Trinity promptly, verify size and SHA256, and record which archives are safe to remove from Orchard in a list for the user. No lane removes them.

On review coverage: answer my earlier request (which review covers `decision.py`, the cut by the 47 scenes f17 saw, and the main comparisons) in one RESULT; if any of it is unreviewed code, name the files and I dispatch the review at once.

Context: the Orchard project filesystem had 351 GB free at 18:46Z and is still falling. Your node-local plan is the right one.