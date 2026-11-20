The lane can place the depth package at `/project/community/jjyeung/a09fdd101cc93`. This builder has not placed, submitted, or fetched anything.

| Artifact | Bytes |
| --- | ---: |
| `out/delivery.tgz` | 6,265,674 |
| Installed package files | 6,408,339 |
| Installed `BUILD.json` | 105,338 |
| Streamed `orchard/o_place.sh` | 8,497,090 |
| Conservative delivery + installed files + descriptor | 12,779,351 |

Delivery SHA256: `05615e93e885a84f948fdfa60c767dac22e055a5eef65e324df924a0ead1a6ee`.

The job uses `a15_cot_apa09fdd101cc93`, general, `--gres=gpu:1`, `--cpus-per-task=16`, `--mem=200G`, and `--exclude=orchard-community-4`. The worker checks for an H100 before model loading. The inherited submission checker requires a minimum 40-minute allocation; the worker has a 30-minute cap and stops at least 120 seconds before allocation end. The forecast is 16.75 worker minutes and 28.75 minutes including unmeasured staging/publication allowances.

Run these commands from the authorized lane holding this directory. Wait for each background script's printed log to report completion before starting its dependent step. Check job status at most once per minute. The scripts refuse an existing destination and use one-use submission locks; do not retry a killed or failed command automatically.

```bash
cd /scratch/jjyeung/orch_n30/lever1_c/r1
sha256sum --check --quiet SHA256SUMS
ssh orchard 'bash -s' < orchard/o_place.sh
# Wait for verified placement.
ssh orchard 'bash -s' < orchard/o_cpu.sh
# Wait for the CPU job and its authenticated CPU.json receipt to pass.
ssh orchard 'bash -s' < orchard/o_sub_hand.sh
# Wait for the GPU job to finish.
ssh orchard 'bash -s' < orchard/o_fetch.sh
# Wait for the authenticated fetch into the package's a/f directory.
mkdir -p returned
ssh orchard 'bash -s' < orchard/o_get.sh | pv -q -L 8000000 > returned/receipts.tgz
tar -xzf returned/receipts.tgz -C returned
```

`returned/4.json` is the depth upload receipt: URI, immutable generation, SHA256, size, and verification status. `returned/5.json` contains camera/scale parity. The small `returned/0.tgz` contains normal job receipts. Failed camera/scale parity does not suppress the depth return.

Retrieve the depth gzip through the lane's governed stream, using `returned/4.json`. Expected compressed size is 40 MB; the conservative budget is 80 MB and the enforced cap is 1,000,000,000 bytes. The supplied transport uses one GCS stream, an 8 MiB/s throttle, and the direct InfiniBand destination on trinity-2-28. It creates only `r1/returned/0.gz`, refuses overwrite, and verifies bytes and SHA256.

From the authorized transport session on trinity-3-30, with the script and receipt available locally:

```bash
bash orchard/pull_depth.sh returned/4.json
```

This prints a stopped process-group ID. The governor must register and resume that group before any bytes move. No governor API is assumed. The builder did not run this script. Internet ingress shares the user's cluster allowance; coordinate it with other streams.

After the authenticated return lands on this node:

```bash
cd /scratch/jjyeung/orch_n30/lever1_c/r1
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B relift.py \
  --depth returned/0.gz --receipt returned/4.json --out out/RELIFT.json
```

The CLI first checks all 150 items at the registered 0.00 m printed-gap tolerance. Each of the two operands inherits its item's gap-match flag; at least 95% must match. Failed parity writes a STOP result and evaluates no intervention cells. Missing depth writes `depth return missing` and exits successfully. `--half-only` explicitly tests float16-only sensitivity under the same gate; the default reconstructs the exact served depth from float16 plus its lossless residual.

Rebuild and CPU-test locally:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build_depth.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_all.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/check_imports.py
```

`build_depth.py` authenticates the exact T1 delivery and capture, preserves all serving/evaluator source bytes, and reseals the worker, plan, operator, batch bundle, descriptors, and scripts. It reads the named sibling inputs and writes under `r1/`. The package uses the existing pinned Orchard input archives; it does not place weights or frame archives again.
