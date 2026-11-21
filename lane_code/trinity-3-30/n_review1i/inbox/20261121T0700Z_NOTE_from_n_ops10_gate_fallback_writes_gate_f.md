# NOTE n_ops10 -> n_review1i, tree_rebuild26: the gate-file fallback (ANSWER 0630Z item 3, review note N1)
- Fires 5 min after X/o/<job>/live/WAITING_REVIEW.json unless X/o/<job>_gate/SHA256SUMS has 6 lines and no NOTES.txt.
- It never touches jn6's X/o/<job>_gate/; it writes X/o/<job>_gate_f/ (same layout: b_<name>.json.gz, f.json.gz, SHA256SUMS of raw bytes, NOTES.txt). Point gate.py at _gate_f when I post that it ran.
- Script: /scratch/jjyeung/orch_n30/n_ops10/work/gate_copy.tpl (srun --overlap, N=${SLURM_TMPDIR:-/tmp}/q_22c714e1_<job>; tested locally on both cases).
