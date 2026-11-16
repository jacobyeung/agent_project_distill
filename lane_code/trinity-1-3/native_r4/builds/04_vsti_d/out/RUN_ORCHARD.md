Orchard is the primary venue. No upload or submission ran during this build. `out/PACKAGE.json` pins `c.tar`, `d.tar` and `FAMILY.json`. `FAMILY.json` retains C8r's original assets, generations, return pool and sealed limits.

The operator places the archives at these shared paths, with second copies under the corresponding GCS names:

| Archive | Shared path | GCS name |
|---|---|---|
| Frozen tower weights/configuration | /project/community/jjyeung/okh7/d9c35d0a/a.tar | q8/d9c35d0a/a.tar |
| Prepared frames folder | /project/community/jjyeung/okh7/d9c35d0a/b.tar | q8/d9c35d0a/b.tar |
| Code | /project/community/jjyeung/okh7/d9c35d0a/c.tar | q8/d9c35d0a/c.tar |
| Reference and input metadata | /project/community/jjyeung/okh7/d9c35d0a/d.tar | q8/d9c35d0a/d.tar |

`a.tar` contains `model.safetensors` and `config.json` with the member hashes in the family. `b.tar` contains `frames/<cache-id>/selection.json` and PNGs. The family requires verified SHA, byte count and cloud generation for all four archives. Upload transport and its IO approval remain the operator's responsibility; no guessed pin is accepted.

Place `FAMILY.json`, the code extracted to `c/`, and a `g.json` mapping a/b/c/d to actual GCS generations in the shared directory below. These commands verify both copies and build the packet in shared storage:

```bash
cd /project/community/jjyeung/okh7/d9c35d0a
/usr/bin/python3 -s -B c/u.py --family FAMILY.json --generations g.json --out r.json
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r.json --out /project/community/jjyeung/okh7/d9c35d0a/p/5d648e9274d54fba92aef108 --token 5d648e9274d54fba92aef108 --deadline-utc 2026-11-16T16:15:00Z
sbatch /project/community/jjyeung/okh7/d9c35d0a/p/5d648e9274d54fba92aef108/a.sh
```

The packet script uses `--output=/dev/null` and references only the shared packet directory. It never refers to the login node's temporary directory. A packet built elsewhere must be transferred intact to its encoded shared destination before submission. Its compute-node work root is the allocation's private `/tmp/a15_<job>_<token>`, created by the wrapper itself.

The job requests one H100 in general. It stages the original authenticated bwrap and uses `root/bwrap` for proof and read namespaces. The read preserves Slurm's `CUDA_VISIBLE_DEVICES`; its `cuda:0` refers to the first visible allocated device. Host bwrap is available only through the explicit Trinity fallback flag. Shared memory binds a directory under the private job root.

Phases run in order: stage; tower on the read's frames; checkpoint scale/gravity; isolated historical proof; read canary; remaining camera items; other items. A proof divergence or exception becomes a receipt and does not stop the read. The canary independently gates continued decoding, including strict score recomputation and byte-equal response replay. Genuine read errors remain fatal.

The fixed canary leaves 96 camera and 344 other items. `code/budget.py` reserves 600 seconds for return and stops starting items an additional 1.25 times the maximum item duration early, with a 100-second floor. The subprocess kill occurs at deadline minus reserve. The GPU phases also retain C8r's 21,600-second cap. Missing items are returned explicitly.

Returns use `/project/community/jjyeung/okh7/n2r/<token>` and `gs://cmu-gpucloud-jjyeung/q8/n2r/<token>/`. They include manifests, prepared arrays, proof, canary, committed journals, merged records and completion; frame pixels and raw tower arrays stay out. The return archive cap is 300,000,000 bytes. The two publication channels remain independent.

For resume, keep the first archive unchanged at a shared project path. Put its absolute path and SHA256 in `s.json`, then use a new token and deadline:

```bash
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r.json --out /project/community/jjyeung/okh7/d9c35d0a/p/9ea1cfc0b79848029c0e53d4 --token 9ea1cfc0b79848029c0e53d4 --deadline-utc 2026-11-17T16:15:00Z --resume /project/community/jjyeung/okh7/d9c35d0a/s.json
sbatch /project/community/jjyeung/okh7/d9c35d0a/p/9ea1cfc0b79848029c0e53d4/a.sh
```

Resume verifies request/configuration/geometry/frame pins and skips committed keys. Its return is cumulative; do not merge the first archive twice. A failed preparation requires operator review. The wrapper never relaunches a killed job.

Build the named report locally after receiving the return, outside the Codex sandbox. This preserves the returned `/r` paths for hash checks and keeps report names off Orchard:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d
./work/py work/report_return.py --archive work/returned.tar.gz --root work/returned_report
```

The report appears in `work/returned_report/report/`. It requires the bound proof receipt, including a failed receipt when appropriate, names refused subtasks on the primary line, and shows observed-item scores and intervals on PARTIAL type/subtask rows. This local namespace command is provided for the operator; it was not executed against an Orchard return.

Unchecked: Orchard admission, staged bwrap execution, actual CUDA allocation, H100 tower/decoding/proof, remote transfers and deadline return duration. `out/UNEXECUTED.md` records these limits. Upload receipts remain pending in `out/ADDITIONS.pending.json`.

When the sealed GPU-phase cap expires before the absolute deadline, the wrapper passes an earlier effective deadline to the worker. The item-start margin is therefore preserved relative to either subprocess kill boundary.
