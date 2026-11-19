Run inside P's allocation after the export upload finishes, before allocation cleanup.
For a non-stop milestone, run `python -m launch_r1.p_export_receipt --run-pins r.json --artifact artifact.json --output h.json --trainer-commit <commit>`.
`r.json` must contain exact `{path,sha256}` pins named `config`, `binding`, and `preparation`; `SLURM_JOB_ID` supplies the allocation identity.
Expected receipt fields: `schema=p-export-only-v1`, `step`, `stop_step`, `checkpoint_status="no checkpoint at this milestone"`, `job_id`, `trainer_commit`, `pins`.
`pins` binds artifact/config/binding/preparation, heads, full_weights, its index and every shard, stream receipts and any stream indices.
Keep every JSON byte unchanged; persist the metadata plus one export-weights tar, and obtain h.json's trusted SHA-256 independently.
Stage P's pinned model manifest and tokenizer/config metadata separately for the in-job opener witness.
N admits this receipt only through mode q with `r1_training.proof_mode="q"`; its training launch refuses it.
The producer and reader refuse the configured stop step; at step 600 use the unchanged `launch_r1.p_handover_receipt` with checkpoint metadata and RNG files.
