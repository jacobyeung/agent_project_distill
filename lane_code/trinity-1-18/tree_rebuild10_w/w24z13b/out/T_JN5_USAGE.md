Submit `jn5.sh` itself after placing it at X/jn5.sh with the existing kit at X/n.

```sh
sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:10:00 --job-name=a15_cot_ap3788c8ec4ed7 X/jn5.sh
```

X denotes `/project/community/jjyeung/okh7/x_22c714e1`. The expanded command is:

```sh
sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:10:00 --job-name=a15_cot_ap3788c8ec4ed7 /project/community/jjyeung/okh7/x_22c714e1/jn5.sh
```

Expected exit status: 3. Expected refusal: `fewer than 4 H100; stop before staging`.
The screened logs are `X/o/<job>/j2.log` and `X/o/<job>/j2.err` (there is no `live/` component).
If the final publisher fails or times out, `X/o/<job>/j2.fallback.log` receives the fixed refusal and `status=3`.
The fallback writes only fixed wrapper labels and shell exit statuses; it never copies raw log text. Every label also passes the existing kit screen unchanged.

The EXIT trap is installed before node-directory creation, log redirection, and publisher creation.
It captures the original status and pipeline statuses, ignores TERM/USR1 during final publication, stops the periodic session, and makes one final j2 attempt.
GNU timeout sends KILL at 120 seconds for that attempt and at 15 seconds for the fallback, within the 600-second Slurm warning interval.
The trap never waits on the periodic worker's IO. The j2 once mode returns failure when publication raises an exception.
A blocked destination cannot be guaranteed to accept a fallback; its timeout still lets the wrapper preserve its status.

With zero GPUs, the wrapper refuses before v.py, resolve.py, l.py, or job.sh runs. The periodic publisher reads only the kit's screening code and metadata before that guard.
The wrapper's SBATCH header, job name `a15_cot_apb2edfac4`, ROOT, node-local Slurm log paths, and child TERM/USR1 forwarding remain intact.
The submission name above is a separate random name for the forced-refusal test.

Local checks use fake GPU output and a private X; no scheduler or Orchard submission was run.
They execute the actual generated j2.py periodic loop, including a repeated-tick check with a shortened interval passed as an argument.
The signal fixture is a real three-process tree with signal forwarding and child reaping; it does not run the workload in the kit.
The resolver refusal uses an empty pool. The separate l.py failure runs the real l.py with a read-only stdout descriptor under pipefail.
The blocked-publication check runs the actual publisher against a FIFO and uses the full 120-second deadline.
Healthy-publisher cases are regression controls that jn4 already passes; injected setup/publisher faults provide the fail-before/pass-after comparisons.
See `work/build24m4z13b/results.json`, `tests.log`, `extra.log`, and per-case logs. The first harness failure and its output are retained in `first_failure.log`; it counted an uncommitted `.part` file as a published result.
Live Slurm grace handling and deployed Orchard bytes remain untested here. Job 173991's refusal is user-supplied evidence, not a result of this build.
