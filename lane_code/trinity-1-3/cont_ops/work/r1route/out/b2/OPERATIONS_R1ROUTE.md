# R1 step-200 operator commands

Package directory: `/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85`. All scripts run on the Orchard login node through the lane's existing `ossh.sh`. The scripts are inert deliverables; no placement, pull, CPU job, or GPU submission ran during this build.

Place A and B first. Run A's pull/fill and wait for `a/1.txt` to contain `0`; inspect `a/0.log` on failure. Then run B's pull/fill. B has no download command: it reuses A's verified four parts and rechecks their hashes. Neither script retries a failed transfer. The real S1 receipt must already exist at the bound preparation path.

```bash
# Set the delivery directory inside the script sent to Orchard; do not export a local path.
{ printf '%s\n' 'D=/project/community/jjyeung/okh7/a15_cot_ap<delivery_hex>'; cat o_place.sh; } | bash ossh.sh 'bash -s'
bash ossh.sh 'bash -s' < o_pullfill.sh
# After fill succeeds:
bash ossh.sh 'bash -s' < o_cpucheck.sh
# After the CPU job completes successfully:
bash ossh.sh 'bash -s' < o_sub.sh
# After the GPU job finishes:
bash ossh.sh 'bash -s' < o_fetch.sh
```

The GPU script refuses unless the exact CPU receipt passes, the general queue for `jjyeung` is empty, and the return pool holds at most 75,000,000 bytes. It submits one GPU for `02:30:00` and saves the job ID in `a/8.txt`. Run A and B sequentially. A local fixture receipt cannot authorize these commands.

Transfer `a/f/0.tgz` and `a/f/EXIT.json` through the lane's authorized transfer procedure into `/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out/b2/f`. Then run locally:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops/work/r1route/out/b2
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py --archive f/0.tgz --exit f/EXIT.json --out /scratch/jjyeung/orch_n30/cont_ops/work/r1route/out/b2/ret
```

After both returns are unpacked:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops/work/r1route/out
OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --a b1/ret --b b2/ret --out scores
```

The scorer prints each baseline read and keeps missing items explicit. The camera denominator is always 450. Partial returns cannot certify H3. The room gate uses `mra_answer` against job 172456, separately for the 36 and 98 items.
