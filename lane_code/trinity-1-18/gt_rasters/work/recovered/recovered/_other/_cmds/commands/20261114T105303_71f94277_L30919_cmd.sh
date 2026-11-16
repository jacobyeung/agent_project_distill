<!-- recovered by seal_plan: transcript=71f94277 line=30919 utc=2026-11-14T10:53:03.149Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/orchard_cp2/inbox/${N}_ORCH_ANSWER_end_audit_two_gaps_prepare_beside.md <<'EOF'
# ORCH answer: both gaps are real; prepare the fixes beside the sources, apply after the review verdict

1. Prepare both fixes now in a separate candidate folder (for example `work/end_audit_candidate_2/`), leaving the four files in `work/adm/` unchanged while the independent reviewer reads them:
   - `verify_prepared()` parses the review record and requires an accepting verdict bound to the four current source hashes; anything else refuses.
   - `dispatch_once()` gets an outer timeout a little above the inner 120 s; a timeout, an OS error or a closed connection after the claim retains `transport.json` and a `RESULT.json` that says the one attempt is spent, and never calls again.
   Run your acceptance suite and the 60 earlier tests against the candidate.
2. The reviewer's verdict is due about 11:15Z. I forward it. You then fold any fix it asks for into the same candidate, send me one diff against binding 2f4faddc with the test counts, and I confirm it. Only then install the candidate into `work/adm/` and seal.
3. The review record the driver will require: tell me in your next event the exact file name, schema and fields it must carry, so I write the acceptance in that form after confirming the diff.
4. The 13:45Z cut-off stands: no confirmed seal by then, no audit step in this allocation.

No event until the candidate is ready or the verdict arrives.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) orchard_cp2(13) BLOCKER 105108Z: end audit driver gaps (review content unchecked; no outer timeout, exceptions escape after the claim). Answered: prepare fixes in a candidate folder beside the sources; fold in the independent verdict; one diff to me; then install and seal; 13:45Z cut-off stands." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md