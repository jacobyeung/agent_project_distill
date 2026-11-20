E3 is an offline-validated CPU diagnostic awaiting real-session execution. Its local dry run uses a 4 MiB substitute and passes all 15 checks. The submitted driver creates a 2,147,483,648-byte random payload only on the allocated node. No real GCS rate is claimed by this build.

Upload these six files beneath X = `/project/community/jjyeung/okh7/x_22c714e1`. Each is below 5 MB; k.tgz contains the complete sealed N kit with GO=false.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
| e3/e3.sh | 1551 | `4ebf248c61d1a88939d0271b4d2d9fd90d3ed9428d05abdd8680502ff7e6aa28` |
| e3/e3.py | 12761 | `de570043da4528d39d552bcf767cc9a008d5be16cd6fac2fee8197fafda78a58` |
| e3/observe.py | 1883 | `32193c8d0d7d6f02b00046db3fdfb08fdef6975b80a06ef988bef704e93879bc` |
| e3/run.sh | 282 | `98a27aae6fc5d467825aaa9a6be62d1732334f4f03bb7fb1ad85ddae30f1cc73` |
| e3/k.tgz | 3869740 | `fc449d2fd586c107927a5dca95f25c4370e217071a0043c46a071435027de59b` |
| e3/pins.json | 325 | `31a7dceaddced1776d24e9a6004155b9e5c8294dee740bc075626d366f34f0b9` |

The three launch steps are:

1. **Hold:** `sbatch --hold "$X/e3/e3.sh"` and record its numeric job ID. Submission should take less than one minute; queue delay is unknown.
2. **Mint:** n_ops8 creates 108 fresh resumable sessions for that job ID and installs `X/n_s/sess_<job>.json`, owned by the submitting user, with directory mode 0700 and file mode 0600. Allow approximately 5–15 minutes for this operator step; this is an estimate, not a measured mint rate. Never print capability values.
3. **Release:** after validating the complete session mapping, run `scontrol release <job>`. Release should take less than one minute. Expect roughly 12–20 execution minutes at adequate upload rates; the allocation allows one hour and queue delay is additional.

The fixed job name is `a15_cot_ap04edabbeceeb`. The job requests preempt, one CPU-only task, four CPUs and 16G. It places Slurm stdout/stderr and runtime logs on node-local storage. It writes only E3.json and logs.tgz under real `X/o/<job>/`, using temporary names during replacement. SLURM_TMPDIR, its available bytes and `df -B1` output appear in E3.json; allocation-local diagnostics remain available if publication fails.

Mint every value of sealed k/y.json `objects`, suffixed with `.j<job>.part00-of-04` through `.part03-of-04`. SESSION_NAMES.template.list enumerates all 108 names. The fixture uses m100, ck00, ckstop and o for the inherited checks, plus ck01 for the rate payload: 20 objects. The ck01 parts each contain 536,870,912 bytes in the real run. The other 88 sessions are required by prepare but unused by the fixture. Failed allocations need new job IDs and new sessions.

The driver verifies its pins, complete kit membership, hashes, BUILD seal and the kit's checker. It probes unshare -Urm and tmpfs, installs the real sessions in a private 16 MiB X before filling it to zero free bytes, and executes pc.sh/pc.py with the sealed gc.py helper. Production uploads use GCS status queries and 16 MiB Content-Range requests, bounded upload quanta, atomic receipts and server-confirmed resume offsets. Completed parts are skipped. The observer records only returned name, size, generation, md5Hash and crc32c; it never records session URLs.

The final fixture retries full-X publication for 140 seconds without consuming the allocation's full deadline. It then uploads the rate payload through the same Copier.send and writer path. E3.json reports local SHA256, bytes, response fields and receipts for every part. Its rate table gives decimal MB/s and seconds for each of the four ck01 parts and their total. The total includes copier overhead; it excludes random-payload generation. Per-part time includes retries from that part's first attempt.

All 14 E2 checks remain required, including archive_while_full, final_order, automatic_recovery and exact archive recovery. The rate check is the fifteenth. Final order is stop checkpoint, exports (stop export first when identified), logs, exit archive, then ordinary checkpoints. The private X grows to 64 MiB for recovery; the same publisher must recover within its unchanged 600-second cadence. The local dry run uses a transport simulator and accelerates the copier polling clock; its MB/s values are not network measurements.

On trinity-3-30, n_ops8 can run the operator-side reader in its credentialed shell after copying the small report through the authorized channel:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E3.json --bucket BUCKET
```

The reader uses the bucket selected during minting. It pins each generation, reads serially at no more than 8 MiB/s, compares name, size, SHA256, md5Hash and the returned crc32c field, and verifies the concatenated four-part exit archive. Its token travels through curl stdin and is never printed. It requires 20 objects. Concatenate each object's four parts in numeric order to restore its bytes. RESULT.json is inside the gzip-compressed exit archive.

The readback helper SHA256 is `9455899a9d7c1df2fdb61aa09216aac2ebe27016b35b6bf9249506a9d31ecb74`. It, this usage file and the session template are operator-side helpers, not additional Orchard uploads.

The N launch remains NO-GO for the two source-scope guarantees in ../NEEDS_OTHER_FILE_24M4Z5.md. E3 tests publication and rate with synthetic payloads; it does not test training, immediate native stop identification or preservation of a shell variable lost before publication.
