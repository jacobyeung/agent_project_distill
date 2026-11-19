# Orchard-only checks

| Check | Why Orchard remains required | Readable failure |
|---|---|---|
| Allocated job ID, destination ownership/modes, pool write permissions, disk space, namespace/bwrap | Requires the actual Slurm allocation and pool paths | Exact EXIT trap preserves return status, node and exception tail. |
| Python/package/CUDA receipt and full staged restore/RGB rehearsal | Requires the actual job venv and complete authenticated archives; local CPU fixtures cannot attest them | CPU job stderr and receipt are retained; failed CPU evidence blocks GPU submission. |
| GPU memory, production trainer ranks, scheduler USR1 delivery and final export/checkpoint | Requires GPUs, scheduler delivery and actual trainer inputs | Batch trap and signal forwarding capture diagnostics; a tiny local child cannot prove trainer export. |

The CPU job repeats package checks before GPU submission. Local release receipts are separately named and cannot replace its evidence. The local suite tests the exact trap/tail with an injected early exception, and tests cooperative USR1/end-slot handling. It does not establish scheduler signal delivery or the root cause of the historical three-second B4 failure.
