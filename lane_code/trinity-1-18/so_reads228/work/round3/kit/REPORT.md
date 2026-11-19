VERDICT: PARTIAL Third-review fixes are implemented; validation and final packaging are in progress.

## Review round 3: finding -> fix -> test

The operator uses the package namespace and d/v/py; a dependency probe precedes card access. Staging uses a private logical root. Exact validation evidence is being collected.

## Coordinator shipping

In the coordinator's existing trinity-2-28 session, require the kit path to be absent:

```bash
test ! -e /scratch/jjyeung/orch_n30/reads228/kit
```

On trinity-1-18, through the coordinator's rate limiter and existing SSH master:

```bash
tar -C /scratch/jjyeung/orch_n30/so_reads228/out -cf - . | timeout 600 ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/reads228/kit && tar -C /scratch/jjyeung/orch_n30/reads228/kit --skip-old-files -xf -'
```

Verify the delivery manifest separately on trinity-2-28, then use coordinator228.sh --stage-only. Wait for a free card before coordinator228.sh --run-only CARD RUN.
