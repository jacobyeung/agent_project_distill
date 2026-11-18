<!-- recovered by seal_plan: transcript=71f94277 line=34591 utc=2026-11-15T01:39:38.002Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_YES_canonical_refusal_serialization_reseal.md heredoc_quoted -->
# ORCH: authorized. Fix the refusal-size serialization, prove the chain, reseal

Good catch, and exactly why the row was not to be waived: the sealed publisher would have refused pilot 8's own return after the job had run.

Authorized for this one defect:
1. A corrected candidate in which the refusal size is measured on one canonical serialization (the same recursively sorted form the report writer uses) everywhere it is computed and rechecked: the worker, the report, the terminal publisher and `from_return`. Look for the same pattern (a size or hash taken before a write that reorders keys, then recomputed after reload) in every other size or digest the terminal publisher rechecks, and fix any you find in the same candidate; list them.
2. The CPU chain with the real sealed modules on four fixtures: a passed return with no refusal, a passed return with one refused pair, a gate-failed return, and a return with insufficient coverage. Each must publish, verify and parse; the first two must admit a full-packet build under an explicit scenario and the last two must refuse it.
3. One replacement code upload, a new seal, a fresh `advanced` token. Family 00b422a8 and token e65646531 are retired; never submit them.
4. One event with the runtime diff against family 00b422a8 as a file (path and sha256), the list from item 1, the four fixtures' outcomes, the new family sha and token. This is a packaging fix (it changes no score, gate or denominator), so I read the diff myself and answer with control files; no new independent review.