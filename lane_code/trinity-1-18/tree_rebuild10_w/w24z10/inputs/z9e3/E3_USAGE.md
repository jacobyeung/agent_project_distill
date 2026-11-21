E3 validates the sealed N kit with GO=false. Both offline suites pass all 16 checks through the fixed HTTP observer. Real-session connectivity, GCS receipts, and real throughput require the lane's real run.

Upload the eight runtime files below X. Every file is below 5,000,000 bytes. The upload manifest also includes this guide, the name templates, readback.py, and TRINITY_READY.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
| e3/e3.sh | 1617 | `cf71474f4d7b07b192978612caf558d435275026cf47f833d056dd073ed52887` |
| e3/e3.py | 13250 | `559532d11b048fd157fabefb2b7c2c776fab083548fcad3f7890e8cc869927e8` |
| e3/observe.py | 1486 | `66d4d9942a0f0e015d323bcc41fb4ce86b78c323756f5bd3fa9f0c16c752b201` |
| e3/run.sh | 282 | `98a27aae6fc5d467825aaa9a6be62d1732334f4f03bb7fb1ad85ddae30f1cc73` |
| e3/k.tgz | 3870443 | `408766f0758faf572f2e69559d6a159eaba5fbd4807ebef148040eddc2b21e65` |
| e3/pins.json | 325 | `a84c73e9852399e467fa16fd8fd1e15566ff666ad299325491ca04ce31e0a7de` |
| e3/trinity.sh | 904 | `9b296c54c2551da7dafaef3a2911729a66fc4ae109936772e56a08f9e68e218c` |
| e3/trinity.py | 3343 | `409fa67ec34c13a03137bd1aa2fe79f10e8de4da0339111e0e8b7d5662f5213b` |

For the Trinity real-session run, install the e3 directory under /scratch and run on trinity-1-18:

```bash
nice -n 10 bash "$D/trinity.sh" JOB_ID SESSIONS_FILE /scratch/$USER/e3_JOB_ID
```

D is the installed e3 directory. Supply a numeric job ID, 108 fresh sessions for that ID, and a fresh or empty output directory. The runner fixes both random payloads at 1 MiB, regardless of a caller's E3_LOCAL_BYTES value. It requests no allocation and uses no GPU. It uses the fixed interpreter /scratch/jjyeung/envs/p1cpu/bin/python with -I -s -B, four numerical threads, and a memory limit below 16 GB.

The runner uses unshare -Urm and a private 16 MiB root with recursive bind mounts for the interpreter and system tools. It creates X at its sealed absolute path inside that root; it never creates /project on the host or rewrites p.json. E08 runs unchanged. Sessions enter private X before stage and enter its 16 MiB tmpfs before the fill. E3 checks zero free bytes, uploads through pc.sh/pc.py/gc.py, and grows X to 64 MiB for recovery. Stage, run, and finish all execute in the same namespace.

The output directory retains E3.json, logs.tgz, every runner/copier log under logs/, response metadata under obs/, and the local copier files under n/. The published copy in private X disappears with the namespace; the output files remain. E3.json carries all 16 checks, four stop-part rates, total rate, SLURM_TMPDIR, and free bytes. Session inputs and caches remain private, with the output directory mode 0700 and session files mode 0600. Session URLs are never printed or logged. Do not publish the private output directory as a diagnostic bundle; use E3.json and logs.tgz.

The offline Trinity test uses the shipped shell and a test copy of the driver that installs a transport/clock adapter after the real stage. The strict sink opens no sockets, retains the real HTTPSConnection constructor, and enforces status queries, Content-Range, 308/Range, chunk alignment, and final metadata. All 16 checks and 16 object receipts pass at the real X path with E08 unchanged. These results establish harness behavior, not TLS/DNS access, live session acceptance, genuine GCS checksums/generations, or WAN throughput. Only the lane's real run can establish those properties. A 1 MiB run does not measure sustained 2 GiB performance.

For the held Orchard CPU run:

```bash
X=/project/community/jjyeung/okh7/x_22c714e1
sbatch --hold "$X/e3/e3.sh"
```

The job name remains a15_cot_ap2da56272b86d. It requests preempt, four CPUs, 16G, one hour, and no GPU. While held, mint 108 fresh sessions for the returned job ID and install X/n_s/sess_<job>.json: a complete object-name-to-resumable-URL JSON mapping, directory 0700, file 0600, both owned by the submitting user. Replace <job> in SESSION_NAMES.template.list with that numeric ID. Never print the values. Release only this CPU test:

```bash
scontrol release <job>
```

The Orchard path retains its 3 MiB export and 2 GiB random checkpoint when E3_LOCAL_BYTES is unset. Its shell, run.sh, and k.tgz are byte-identical to the supplied inputs. The only e3.py hook makes E3_LOCAL_BYTES apply to both payloads when explicitly set. No 2 GiB payload was created on Trinity. The offline local suite uses 3 MiB payloads; the offline Trinity suite uses 1 MiB payloads.

Both modes verify pins, the kit manifest, BUILD, and the kit checker. The kit seal is bd20a9fe466f4829a801d58e7e5190cdce0478ac908bdad23aab6ec86a4ce6b9. The observer patches getresponse on the original HTTPSConnection class and forwards unchanged response bytes through its metadata wrapper. It retains the script allow-list and subprocess injection. It never replaces or subclasses a standard-library class.

E3.json retains all 14 E2 checks plus rate and upload_logging. Each rate row records bytes, seconds, start/end times, and MB/s. Total stop-upload duration spans the first part's start to the last part's finish; final-pass time is separate. Receipts include hashes and the final name, size, generation, md5Hash, and crc32c. The actual copier queries resumable offsets and uses 8 MiB chunks except the last. Final matching 200/201 metadata creates receipts. The archive remains capped at 50,000,000 bytes.

The explicit final pass allows 240 seconds, and recovery can wait 660 seconds. A slow or failed transfer produces FAIL. Local retry while X is full is expected; logs retain status, Range, masked errors, and the no-receipt marker when applicable. The archive freezes the log tails available at its creation; later attempts remain in the local/live upload log.

SESSION_NAMES.template.list lists all 108 preparation names. STATUS_NAMES.template.list lists the 16 consumed names: four parts each of ckstop, m100, o, and ck00. On the credentialed node, use the supplied status tool without displaying session values:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B mint_n.py status sess_<job>.json OBJECT_NAME
```

For independent readback on the credentialed node:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E3.json --bucket BUCKET
```

The reader serially fetches exact generations at at most 8 MiB/s, verifies sizes, MD5 and SHA256, compares CRC32C metadata, and reconstructs the archive hash. Credentials enter curl through stdin. The reader's SHA256 is `238ea609ea8124cedd3a12b944e5ebd3cbaa8e4bd086d25a96429da8e31ee0e6`. The Orchard fixture transfers about 4 GiB of checkpoint data because it exercises both checkpoint routes; allow roughly nine minutes for its capped readback, plus metadata requests. The Trinity fixture is smaller. No real-session upload or readback ran during this build. Training remains NO-GO.
