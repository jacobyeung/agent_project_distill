<!-- recovered by seal_plan: transcript=71f94277 line=32964 utc=2026-11-14T18:50:13.117Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_PRECLEARED_reuse_gate_path_fix.md heredoc_quoted -->
# ORCH: pre-cleared. Fix the reuse gate's extractor path and submit under the standing order

Two copies of `orchard_stage.py` with the same sha256 (eb26cea5...) under different paths are the same extractor. Bind both to the sealed logical extractor hash as you propose. Conditions for submitting without another clearance from me:

- family 2b9d7815, the packet e702b65e2 and my control files are unchanged (same hashes as now);
- only controller-local files change (the reuse guard and its gate), and their CPU tests pass, including one that shows the gate still refuses an extractor whose bytes differ;
- the rest of my 18:4xZ order holds as written (account rule, one test-only call, one real submission, no retry).

Then submit and send the usual one event, with the changed files' paths and hashes in it. If anything else in the gate refuses, stop and tell me what it compared.