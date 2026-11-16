<!-- recovered by seal_plan: transcript=71f94277 line=32419 utc=2026-11-14T16:11:42.423Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ANSWER_local_check_scope.md heredoc_quoted -->
# ORCH answer: no runtime copy, no Orchard CPU job; scope the local check to what failed

You are right not to mock the bootstrap. My order reached too far. Scope of the permanent local check:

1. Stage the exact five uploaded objects locally as the job stages them, and run the job's own input-pin validation over every pin it checks. This is the step that failed in 169537 and it needs only file hashing.
2. Run everything else in the job's path before the production interpreter is needed, as far as the local Python can execute it unchanged. Stop there.
3. For the bootstrap and runtime import path, do not execute it locally. Instead prove by pins that every file and object it uses (bootstrap sources, runtime, NumPy, FLA and Triton archives, the closure) is byte-identical to what pilot 169521 used, which passed bootstrap, loaded the model and ran parity on the real node. Record that equality in the check's output. If any of those pins differs from 169521's, stop and tell me.

No copy of the 8.1 GB runtime, no Orchard CPU job (it would take our one `general` slot), no relaxation beyond this. Then pilot 5 as ordered: the event with the cause (already confirmed, thank you), the new family sha, object name and generation, token, and the check's record.