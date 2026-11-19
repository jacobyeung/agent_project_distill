# Checks that still require Orchard

Every Trinity-runnable gate, including complete script planning and receipt predicates, must pass before place or fill can execute. A missing authenticated local mirror fails preflight. The wrapper does not substitute a CPU fixture for missing production bytes.

| Check | Why Orchard is required | Failure evidence |
|---|---|---|
| Fresh token directory and real package modes | The Trinity ledger cannot establish Orchard storage state; atomic mkdir rejects a spent token | Bounded place call captures stderr and its exit code; no automatic retry |
| Allocated node ID, node-local free space, filesystem/namespace and bwrap support | These depend on the allocated node and its mount policy | CPU stdout/stderr in a/4.log and a/4.err; local per-call logs retain the job ID |
| Real staging, pinned job venv, export restore and RGB admission | Trinity fixtures do not contain the full weights/RGB set or the production 3.12 job environment | Native CPU checks run before GPU submission; CPU.json is required |
| Real pool write, quota and persistence | The local 4 MiB write test proves guard behavior, not community pool access | Native guard/entry receipt and pool errors; GPU BATCH capture |
| CPU scheduling and sacct accounting | Trinity cannot emulate scheduler state or actual CPU completion | Submit and polling use separate timeout-bounded calls; logs preserve stdout/stderr. Only sacct exit 75 is retried, at most three consecutive errors, at least 60 seconds apart. Transport timeout/drop stops immediately |
| General queue availability, duplicate GPU submission, real return-pool contents | These are live shared state | Native sealed GPU script checks them and fails before submission |
| Slurm delivery of --signal=B:USR1@1800 to the batch shell | Local signals exercise the real wrapper and read runner, but not Slurm signal routing or scheduler teardown | BATCH EXIT trap preserves node line, exit status and last 60 log lines in a/x<job> |
| Real GPU execution and production trainer-rank stop cooperation | No GPU or training task is run here; the read runner fixture does not prove trainer ranks honor a stop file | Native CPU receipts precede GPU work; returned journals and BATCH capture expose partial/failing runs |

Python 3.6.8 is a Trinity check: the wrapper executes generated place code, the native fill helper and the native 3.py check under this node's real /usr/bin/python3 -I -s -B. Every generated Python body also compiles there. The 3.12 staged job environment remains Orchard-specific.

Every remote command includes timeout (maximum 300 seconds). CPU submission ends immediately; Trinity polls in short calls. The final GPU call checks COMPLETED and a nonempty CPU.json again after a 60-second interval, then runs all native receipt/queue/pool checks. No ssh session is held for the CPU wait. Local per-call JSON logs retain return code, stdout and stderr. A remote shell EXIT trap prints the phase exit code and source line; the GPU batch trap preserves the underlying failure text even before a result archive exists. The unexplained three-second B4 failure has no claimed root-cause repair.
