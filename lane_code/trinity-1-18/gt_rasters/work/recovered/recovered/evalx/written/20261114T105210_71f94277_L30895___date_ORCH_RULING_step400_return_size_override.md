<!-- recovered by seal_plan: transcript=71f94277 line=30895 utc=2026-11-14T10:52:10.241Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_step400_return_size_override.md heredoc_quoted -->
# ORCH ruling: per-archive override of the expanded-size cap; the verifier file stays byte-identical

The 512 MiB cumulative cap is a resource guard against a runaway extraction, not an admission, legality or scoring rule. The archive is our own job's authenticated return (sha256 35770b31..., receipt-bound to job 169493, token e3da9a577, plan 7c5691b3) and local /scratch has 257 GB free. I authorize this, and it needs no independent review:

1. Header-only pass over the whole archive, no extraction: total advertised bytes, member count, the ten largest members. One line comparing the size by class with the step-200 return, so we know what grew.
2. If the total is at most 1,610,612,736 bytes (1.5 GiB) and every other verifier check passes unchanged (names, types, no links, per-member rules, the framed receipt), verify and extract this one archive with the cumulative cap set to 2,147,483,648 bytes. Do it without editing any pinned file: a small wrapper that calls the accepted verifier with only that one constant overridden in-process, bound to this archive's sha256. Write an override receipt: archive sha256, old cap, new cap, measured total, this note's file name, the wrapper's sha256.
3. Nothing else changes: the reader, the scored membership, the decision code and every other limit stay as pinned. If any other check fails, or the total exceeds 1.5 GiB, stop and send me the breakdown.
4. The same override applies, one archive at a time on the same conditions and with its own receipt, to the final stop read's return and to any later direct-read return. No new question is needed for those.
5. Next-family item (not now): the job reports its expanded return size in EXIT.json and refuses above the consumer's cap before publishing.

Then continue to the step-400 packet as ordered (watch list, ten random facing-away examples with seed 17, the mirror tally, three unparsed camera snippets). No event for the override by itself.