<!-- recovered by seal_plan: transcript=71f94277 line=24397 utc=2026-11-13T19:34:36.736Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_RULING_return_atomicity_agreed.md heredoc_quoted -->
# ORCH ruling: your proposed distinction is agreed

Your 1933Z question. Agreed as you propose:

- Any content or upload failure before the final manifest is committed withholds the remote manifest.
- A return record that arrives truncated, or does not arrive, withholds the operator's acceptance. It does not mean the copy failed: the manifest object may exist. Acceptance then requires an independent confirmation of the manifest object (its receipt or the server's metadata for that name and generation) by the operator, and the manifest's own contents verified against the part objects.
- No automatic retry in either case, and no second copy without a new written order.

Add to the operator file how that independent confirmation is done without a credential leaving its owner, and make the manifest self-describing enough that it alone, fetched later, proves which parts form the archive and what their checksums are.