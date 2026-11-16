# Read-only donor row scanner for job 169097

**Use this operator file with the unchanged reviewed bundle 1a565f85 and scanner source 5c1f4408. The operator's read-only size check must pass first. This lane has not contacted Orchard or run the production scan.**
The bundle contains two standard-library Python files. The node runs only `scan_donor_rows.py`, received through standard input; nothing is installed in the job or written on its node.

## Safety and limits
- The scanner verifies every configuration, preparation, index/order and database pin before use. It rejects missing inputs, changed files, path escapes, wrong counts and active WAL/journal files.
- Every database connection uses `mode=ro&immutable=1`. The scanner issues only SELECT statements, creates no locks/journals/shared-memory files, and leaves the trainer's readers open. It does not modify the trainer or its namespace.
- The worker is one standard-library Python process. It restricts affinity to at most two CPUs, address space to 4 GiB and CPU time to 900 seconds. This command selects an 840-second SIGALRM deadline, inside Slurm's 15-minute limit. The bootstrap sets the core-dump limit to zero. The wrapper sets nice 19 and idle I/O priority; idle priority may have no effect under the node's I/O scheduler.
- The worker streams row/target content. It loads only bounded JSON metadata and source/index mappings, not SQL tables. No torch, model, GPU, external package, cache, temporary file, or network access is needed.
- A read-only scan can still contend for CPU, page cache and local disk bandwidth. The safety tests prove no file mutation and concurrent read compatibility, not zero training-performance impact.
- Six retained CPU tests cover byte/list/size/mtime preservation, another process's open read transaction, missing/changed pins, count/path refusal, stdin execution, native fingerprint agreement and the acceptance envelope.
- The independent safety review ran 22 checks: 21 passed and one ordinary-reader WAL case refused by design. The scanner and bundle bytes remain unchanged.

## Expected WAL refusal
If a trainer connection keeps a `rows.sqlite-wal` file open, this scanner refuses even when that file has zero bytes. It also refuses an existing journal. The operator must report the affected database path, the size check's `-wal`/`-shm` presence and sizes, the scanner's complete REFUSED JSON, and the step exit status to ORCH.
Do not change a production database's journal mode or checkpoint it to force acceptance. Do not retry automatically. A nonempty WAL may contain committed data absent from the pinned main file, so ignoring it would not attest the trainer's row view.
The tested zero-byte-WAL alternative is private and is not included in this bundle or authorized for the job.

## Local measured cost
One approved serial pass read the four databases under `/scratch/jjyeung/orch_cd/legs1_dbs/ap/`; no data was copied.
| Input | File bytes | Rows streamed | SHA seconds | Row seconds |
|---|---:|---:|---:|---:|
| `1742c666/s/q127808/vxm_m4/rows.sqlite` | 1,298,710,528 | 154,723 | 2.353 | 15.669 |
| `5e1d07a4/f/h/r16/rows.sqlite` | 1,348,722,688 | 76,277 | 2.439 | 27.911 |
| `8865619b/u/7c9f2d84/rows.sqlite` | 218,099,712 | 25,020 | 0.392 | 2.823 |
| `f02f16ad/s/a2v3/rows.sqlite` | 4,891,635,712 | 66,934 | 8.819 | 202.858 |
Total: **263.27 seconds**, **23,449,600 bytes peak RSS**, **7,757,185,024 physical read bytes** and **16,657,441,491 logical read characters** from `/proc/self/io`. All 322,954 rows canonicalized; input size/mtime/ctime stayed unchanged.
The benchmark hashes each file once and streams an ordered SQL cursor. Production follows the admitted source/index mapping with indexed SELECTs; that lookup overhead and Orchard contention are not measured here.
Production also holds its JSON index maps in memory; the measured 23.45 MB is not a production RSS claim. The 4-GiB address-space cap remains binding.
At the measured rates, 194,987 pose rows cost about 591 seconds of row processing; hashing the stated 25.9 GB of pose sources costs about 47 seconds. Scaling the other local row kernels adds about 35 seconds, plus their file hashes.
Budget roughly **12 minutes at these local rates**, not a production guarantee. Large a3 rows, weaker CPUs or idle-I/O contention can exceed the **14-minute scanner limit**. Timeout means no accepted attestation; do not retry automatically.
The measured kernels are unchanged in the bundled scanner; its added stdin source-hash path has separate passing tests.

## Exact node command
Run this from the off-node operator shell after extracting the bundle into the current directory. Redirections below are in that shell, not on the compute node.
The two physical roots and interpreter are the sealed launcher's defaults (`launch_s1/b/c.sh:18–23,54–58,334–366`); the operator's size check must confirm them first. A changed `TK_RUNS_DIR`, unavailable interpreter or out-of-root symlink is a refusal, not permission to guess another path.

```sh
set -o noclobber
BUNDLE="$PWD/donor_row_scanner_07ca49df"
CFG='{"path":"/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json","sha256":"78341acb36ffd03b9cec6de65effc9fafcbe8bccdc1dfb43e9da7bd88af47560"}'
PREP='{"path":"/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/prepared/s1_receipt.json","sha256":"34cf26a691728802db8d47766c42bd4045c5481fe1f27c09a486abafaec1a3d6"}'
/usr/local/bin/srun --jobid=169097 --overlap --immediate=60 --gres=none \
  --ntasks=1 --cpus-per-task=2 --mem=4G --time=00:15:00 \
  /usr/bin/env CUDA_VISIBLE_DEVICES= \
  /usr/bin/ionice -c 3 /usr/bin/nice -n 19 \
  /tmp/jjyeung/okit_8865619b/root/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python -I -s -B -S -c \
  'import hashlib,resource,sys; resource.setrlimit(resource.RLIMIT_CORE,(0,0)); source=sys.stdin.buffer.read(); exec(compile(source,"<donor_row_scanner>","exec"),{"__name__":"__main__","SCANNER_SOURCE_SHA256":hashlib.sha256(source).hexdigest()})' \
  --inputs /tmp/jjyeung/okit_8865619b/runs/469ddece/inputs \
  --ap-root /tmp/jjyeung/okit_8865619b/root/aws/u/ap \
  --config-pin "$CFG" --wall-seconds 840 \
  < "$BUNDLE/scan_donor_rows.py" > donor_row_scan_169097_full.json
```

Require exit code zero and exactly one valid JSON document. Preserve any refusal output as evidence; it is not an attestation.
The stdout document is one UTF-8 JSON line, about 2.3 KB on the review fixture and somewhat larger with production paths; acceptance caps it at 65,536 bytes. It contains hashes and counts, not the training rows. The operator owns the return transport and its completeness checks.

## Self-check and warm-start pin
The full document has schema `s1-donor-row-order-v1` and fields `config`, `preparation`, `rows`, `scanner`, and `resources`.
`rows` contains the ordered stream list, each stream's count/content SHA, and a digest of that list. `scanner` contains the code SHA, explicit stream order/counts and the pose mapping's ordered JSON pin plus its two indexed source-database pins. The full 194,987-pair map is represented by its authenticated content pin, not duplicated into the small output.
The acceptance tool checks the code SHA, both exact donor pins, ordered counts **20,239 / 194,987 / 57,136 / 114,904**, row digest, two-source pose mapping and resource bounds. It emits the minimal envelope accepted by the existing optional warm-start consumer:

```sh
python3 -I -s -B "$BUNDLE/accept_scan.py" \
  --input donor_row_scan_169097_full.json \
  --scanner-source "$BUNDLE/scan_donor_rows.py" \
  --config-pin "$CFG" --preparation-pin "$PREP" \
  > donor_row_order_469ddece.json
```

Require exit code zero again. Mirror **both** JSON files off-node. Hash the exact bytes of `donor_row_order_469ddece.json`; its absolute staged path and SHA256 become `warm_start.donor_row_order`.
The full scan keeps source/resource/map evidence; the minimal envelope keeps the existing four-field consumer schema unchanged. Do not pin a refusal document or the full evidence document as that minimal consumer input.
This bundle captures evidence only. It neither approves the new warm-start binding rule nor authorizes a seal, release or training launch.
