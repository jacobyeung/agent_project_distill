Apply `UPLOADS_24M4J.json` from its declared mixed baseline. Its qd delta is against 24m4h `62d8a7f5`; it includes the unapplied 24m4i qd configuration changes. The shared `u/` files from the q/n 24m4i overlay and the authenticated P archive must already exist.

Copy the manifest's kit files to `/project/community/jjyeung/okh7/x_22c714e1/`. Copy these two helpers to the same root (19106 bytes total):

- `out/rcj/rcj.sh` → `rcj/rcj.sh`
- `out/rcj/x.py` → `rcj/x.py`

Ensure `/project/community/jjyeung/okh7/x_22c714e1/j/` exists. Submit once from the qd directory:

```bash
cd /project/community/jjyeung/okh7/x_22c714e1/qd
sbatch --job-name=q24j ../rcj/rcj.sh
```

The command overrides `JOBNAME_PLACEHOLDER`. The script requests preempt, 16 CPUs, 128 GB and two hours, with no GPU or requeue. It creates a fresh directory under `SLURM_TMPDIR` (or `/tmp`), uses eight library threads, and runs offline.

The helper uses the qd resolver, handover reader and pinned staging implementation for 65 pins in the recipe/source closure, plus the Python runtime and staging helpers. It stages tokenizer/config metadata, the legacy database and row inputs; it does not stage checkpoint weights or frame payloads. It runs P's native reconstruction through rb.py and retains the complete `4e8e6c04…` file-hash gate.

The job writes `receipt.json`, `materialization.json`, `db_bytes.json`, `import_probe.json` and `timings.json` under `x_22c714e1/o/${SLURM_JOB_ID}/`. Missing artifacts receive an `UNAVAILABLE` record. Publication attempts each artifact independently before propagating failure. The database record contains its whole-file SHA256, byte size and 16-byte header in hex; the SQLite file stays in node-local `r/rows.sqlite`. Logs go to `x_22c714e1/j/` through the kit's name filter.

173626 staged from 05:09:40Z to 05:29:24Z (1184 s). Its first non-frame staging interval ended at 05:13:26Z (226 s); the remaining 958 s included frame and initialization work. Budget 3–6 minutes for this reduced staging as a heuristic, then measure `staging_seconds` and `build_seconds`. No Orchard execution or measured reconstruction time is claimed.
