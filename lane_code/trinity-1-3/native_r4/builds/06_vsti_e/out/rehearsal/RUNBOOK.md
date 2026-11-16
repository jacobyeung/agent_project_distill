Run outside the sandbox on trinity-1-3:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/06_vsti_e
./work/py out/rehearsal/run_rehearsal.py --fixture-tower
```

The command uses host bwrap only through host_bwrap=True, private shared memory, and the production token/error-response loop. The namespace result is separate from the CPU fallback result. This harness does not certify the Orchard binding set or GPU path.
