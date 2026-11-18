# R1 step-200 operator commands: package A

Package: `/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a`. Delivery: a separate `/project/community/jjyeung/okh7/a15_cot_ap<hex>` directory created by the operator. Place only this package's `1.tgz` in that delivery directory. The delivery directory must differ from both package directories. No remote action ran during this rebuild.

The operator can create a delivery directory on the Orchard login node with:

```bash
D=/project/community/jjyeung/okh7/a15_cot_ap$(/usr/bin/python3 -I -s -B -c 'import os; print(os.urandom(8).hex())')
mkdir -m 700 "$D"
printf '%s\n' "$D"
```

Transfer `1.tgz` there through the lane's authorized transfer procedure. In the following local commands, set `D` to that exact remote directory and use the lane's existing `ossh.sh` path:

```bash
# Run from the lane directory containing ossh.sh. Replace the quoted path.
D='/project/community/jjyeung/okh7/a15_cot_ap<hex>'
{ printf 'D=%q\n' "$D"; cat /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A/o_place.sh; } | bash ossh.sh 'bash -s'
```

Place **both A and B** before filling either. Run A's fill first; B must wait until A finishes successfully. A downloads the four parts sequentially once. B reads the same files under A's `a/e/` directory and checks them again. Retain A's files through both jobs.

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A/o_pullfill.sh
```

The fill starts under `nohup`. Check its completion with this read-only command, at most once per minute:

```bash
bash ossh.sh 'test "$(cat /project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a/a/1.txt)" = 0'
```

On failure, inspect `/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a/a/0.log`; there is no retry loop. A requires the handoff's `.done` object, 21,583,032,320 bytes, and SHA256 prefix `795ef9ef`. The fill computes and compares the entire SHA256 against `.done`. The full handoff SHA and `.done` bytes were not supplied locally.

The fill requires the exact config (`3b0051c4…`), S1 receipt (`4c0dd9d6…`) and data receipt (`7f654d2f…`). The physical receipt is `x_69d2930d/runs/673bc60f/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json` beneath `/project/community/jjyeung/okh7`. Its internal logical path remains unchanged. The exact data receipt is absent from the rebuild workspace; fixture receipts cannot pass the delivered package's fill.

After fill completes, submit the allocated CPU check:

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A/o_cpucheck.sh
```

Wait for the CPU job to complete successfully. Then submit this package's GPU job:

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A/o_sub.sh
```

The script requires the exact CPU receipt, an empty `jjyeung` general queue, and a return pool of at most 75,000,000 bytes. It requests one GPU for `05:00:00` and records the job ID in `a/8.txt`. Run the A and B GPU jobs sequentially. Fixture receipts do not authorize submission.

After the GPU job finishes:

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A/o_fetch.sh
```

Transfer `/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a/a/f/0.tgz` and `EXIT.json` into `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A/f/` through the lane's authorized transfer procedure. Unpack locally:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py --archive f/0.tgz --exit f/EXIT.json --out /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/A/ret
```

Scoring requires the authentic job-171253 and job-172456 returns, which are missing here. Restore them under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/bases/b1/work/ret` and `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/bases/b2/work/ret`, plus the authentic job-172456 `scores.json` under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/bases/b2/work/scores`. The base payloads, plans, and operator bytes are already reconstructed there. Do not use the synthetic fixtures under `gates/` or `test_tmp/` as baseline returns.

```bash
cd /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --baseline-root bases --self-test --out baseline_check
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --baseline-root bases --a A/ret --b B/ret --out scores
```

The scorer uses job 171253 read 0 for camera and dev-S1 room, read 1 for distance, and job 172456 read 0 for both room sets. It preserves the 450-camera and 107-non-metre populations, 10,000 physical-room bootstrap draws, both confidence intervals, and room `mra_answer`. Partial results cannot certify H3. Review `../REPORT.md` and `R2_OPERATOR_DIFF.patch` before remote execution.
