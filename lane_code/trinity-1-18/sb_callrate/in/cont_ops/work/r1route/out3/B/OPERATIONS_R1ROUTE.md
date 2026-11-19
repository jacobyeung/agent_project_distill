# R1 step-200 operator commands: package B

Package: `/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85`. Delivery: a separate `/project/community/jjyeung/okh7/a15_cot_ap<hex>` directory created by the operator. Place only this package's `1.tgz` in that delivery directory. The delivery directory must differ from both package directories. No remote action ran during this rebuild.

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
{ printf 'D=%q\n' "$D"; cat /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/o_place.sh; } | bash ossh.sh 'bash -s'
```

Place **both A and B** before filling either. Run A's fill first; B must wait until A finishes successfully. A downloads the four parts sequentially once. B reads the same files under A's `a/e/` directory and checks them again. Retain A's files through both jobs.

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/o_pullfill.sh
```

The fill starts under `nohup`. Check its completion with this read-only command, at most once per minute:

```bash
bash ossh.sh 'test "$(cat /project/community/jjyeung/okh7/a15_cot_apb9188e9225a85/a/1.txt)" = 0'
```

On any transfer failure, stop and inspect `/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85/a/0.log`; there is no retry loop. A and B require object `q8/8865619b/673bc60f_m200.tar`, exactly 21,583,032,320 bytes and SHA256 `795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b`. A checks the receipt before pulling; both fill helpers enforce these constants before and after scanning. The delivery manifest seals the fill helper. A's single sequential `gsutil cp` command sets `Boto:num_retries=0`, one metadata attempt, one process/thread, and disables sliced downloads. Do not relaunch a failed transfer.

The fill requires the exact config (`3b0051c4…`), S1 receipt (`4c0dd9d6…`) and data receipt (`7f654d2f…`). The physical receipt is `x_69d2930d/runs/673bc60f/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json` beneath `/project/community/jjyeung/okh7`. Its internal logical path remains unchanged. All three exact preparation files pass the local preparation check. The full export tar is not local; the Orchard fill must authenticate every part and the whole archive.

After fill completes, submit the allocated CPU check:

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/o_cpucheck.sh
```

Wait for the CPU job to complete successfully. Then submit this package's GPU job:

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/o_sub.sh
```

The script requires the exact CPU receipt, an empty `jjyeung` general queue, and a return pool of at most 75,000,000 bytes. It requests one GPU for `02:30:00` and records the job ID in `a/8.txt`. Run the A and B GPU jobs sequentially. Fixture receipts do not authorize submission.

After the GPU job finishes, fetch with the sealed helper. It checks the requested token, plan, job, synthetic flag, completion status, archive length and digest, and the pool receipt before creating output. The delivery wrapper also routes `3.py fetch` through this helper:

```bash
bash ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/o_fetch.sh
```

Transfer `/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85/a/f/0.tgz`, `EXIT.json`, `RETURN_RECEIPT.json`, and the recorded job ID `a/8.txt` into `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/f/` through the lane's authorized transfer procedure. Unpack locally:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B
RET=$(/scratch/jjyeung/envs/p1cpu/bin/python -B -c 'import sys; print(sys.argv[1]+format(int(sys.argv[2]),"08x"))' "$(cat TOKEN)" "$(cat f/8.txt)")
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py --archive f/0.tgz --exit f/EXIT.json --return-token "$RET" --out /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/ret
```

The authenticated job-171253 and job-172456 baseline returns are installed under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/bases/b1/work/ret` and `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/bases/b2/work/ret`. The regenerated room scores at `bases/b2/work/scores/scores.json` match SHA256 `9d3809d30712dc75c17857cb97d77dcd1cfd9fe6912d5676fdc0bc25cee04aa8`. Baseline self-comparison passes. The accepted bootstrap source is absent; the re-review must resolve that reference check. The separately labelled independent reference passes, but does not recover the accepted source.

```bash
cd /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --baseline-root bases --self-test --out baseline_check
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --baseline-root bases --a A/ret --b B/ret --out scores
```

The scorer uses job 171253 read 0 for camera and dev-S1 room, read 1 for distance, and job 172456 read 0 for both room sets. It preserves the 450-camera and 107-non-metre populations, 10,000 physical-room bootstrap draws, both confidence intervals, and room `mra_answer`. Partial results cannot certify H3. Review `../REPORT.md` and `R3_OPERATOR_DIFF.patch` before remote execution.
