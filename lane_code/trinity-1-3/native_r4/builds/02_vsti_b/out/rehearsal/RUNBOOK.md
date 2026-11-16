Run outside the sandbox on the assigned compute node:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b
./work/py out/rehearsal/run_rehearsal.py --fixture-tower
```

The fixture flag applies to both the namespace command and its CPU fallback. A namespace failure is recorded separately from a passing library rehearsal.
