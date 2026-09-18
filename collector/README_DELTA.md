r1315 combines the tolerant collector pool with dense and sparse instance grounding.
The pool admits 64 workers; failed workers retain receipts and bounded recovery.
Sparse CSR membership preserves overlapping instances and rejects malformed encodings.
The sparse donor and loader bytes have explicit admission pins and an exact file census.
Coordination heartbeats retry timeouts three times with 1s and 2s backoff.
An exhausted retry batch leaves the controller running and tries again on its next heartbeat.
After 25 minutes without confirmation, the controller writes BLOCKED and stops owned workers with rc=2.
Ownership refusal and non-timeout coordination errors still fail closed.
The original agent/work identity, source identity hash and production run root remain fixed.
The scientific triplet retains its r1313 names and bytes to preserve the requested teacher.
The preparer contract, membership, model, prompts, tools and output budgets remain fixed.
Existing attempt directories remain repeat-spend refusals; no attempted question is silently repeated.
CONTRACT.json pins all other package files; its SHA-256 must be supplied externally.
No paid API calls, GPU jobs, production bind or launch form part of package validation.
