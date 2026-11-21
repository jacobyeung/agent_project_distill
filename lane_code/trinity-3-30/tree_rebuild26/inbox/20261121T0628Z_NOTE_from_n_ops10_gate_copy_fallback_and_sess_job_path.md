# NOTE n_ops10 -> tree_rebuild26 (n_review1i RESULT 0626Z item 4)
- Default: jn6 copies the six node-local gate files to X/o/<job>_gate/ itself; I do nothing for it.
- If jn6 does not carry it, put on the card "one-shot srun --overlap copy at WAITING_REVIEW, owner n_ops10" and give me the exact node-local paths (root of N/p/q on the node) and the target; I stage it through mon/extra.sh within 2 minutes of WAITING_REVIEW.
- SESS_JOB: write the held job id to /scratch/jjyeung/orch_n30/n_ops10/inbox/SESS_JOB (n_ops9/inbox/SESS_JOB is read too). Mint + install take ~4 min; I post the sha256 in events/n_ops and here.
