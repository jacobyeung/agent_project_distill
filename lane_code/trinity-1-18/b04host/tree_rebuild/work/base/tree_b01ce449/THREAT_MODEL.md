# Threat model: source-validation receipts for provisional training manifests

Branch `trainer-srcreceipt-20260930`. The code under review is commit `95802aff8b0a0c6a6922a4e6f032d815b545d4cc`; this file adds documentation only.

## Purpose

On code-aws, the cluster cancels a GPU job whose GPUs stay idle for 30 minutes. For training sets of about 94,000 rows, `load_training` spends longer than that before step 1, because it re-reads and re-hashes every candidate payload, including 32 frames per row. `diagnostic seal-source` runs that complete admission once, in a CPU job, and writes a receipt beside the manifest. At GPU start, `load_training` accepts a matching receipt instead of repeating the payload reads.

## What the receipt path still checks at GPU start

- The manifest and protocol checks are unchanged: the protocol pin, `load_protocol` (settings, division, base, versions and the runtime closure that pins this validator's files by hash), division equality and source equality.
- The receipt must match exactly. It binds the manifest bytes, which are parsed and hashed from one buffer, together with the protocol pin, the candidate-source pin, the census digest, the division digest, the runtime-closure digest, the row and drop counts, and the clean code commit. The candidate index file is re-hashed.
- Every kept manifest row must be in the training division and hash to its frozen census `row_sha256`. The coverage, audit, count, `accepted_before_token_limits` and `training_ready` checks are unchanged.
- Every dropped row is fully re-checked. It is re-read from its own candidate payloads, bound to its census digest and re-tokenized by the unchanged drop checks.
- Every kept row's frames are re-hashed during `stage_frames`, both source and staged copy, before training reads them. Training consumes only the manifest rows and the staged frames.
- Without a receipt, or with `use_receipt=False`, admission is byte-for-byte the original full path.

## Out of scope

A coordinated adversarial rewrite of frozen artifacts on our own uid is out of scope. An example is a writer who changes a protocol's census digests, the manifest's protocol pin and the receipt together. The full path does not resist the equivalent attack either: a writer who rewrites the protocol's candidate-source pin, the index and the payload files defeats it. Both paths defend against accidental drift, not against a malicious writer with our permissions. The orchestrator accepted this residual on 2026-09-30, citing the user's 2026-09-23 closure-hash stopping rule. The review receipts are `20260930T185654Z_trainer73_srcreceipt_review` (round 1, fixed in 95802af) and `20260930T190530Z_trainer73_srcreceipt_review2` (round 2, residual accepted here).
