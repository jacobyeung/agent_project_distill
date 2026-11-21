E3 uses the sealed N kit with GO=false. Its offline strict-sink checks pass; real-service throughput and resume remain to be measured. The bundle requires 112 session names (108 + 4 for the final upload log).

Upload the following files beneath X=/project/community/jjyeung/okh7/x_22c714e1. Each file is below 5 MB.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
| e3/e3.sh | 1617 | 7bc226ac254ff641893e8b28cce3d6b96340bb84240a96181f3406cb16296497 |
| e3/e3.py | 14235 | c8ad02a3eb1ff223cb51441e6313d1360620ffb686604f0bf5552d9a810760ab |
| e3/observe.py | 3123 | d52a715764c26f1a666b85f6002bfd32318f72b4e71b96f31e24634aff0f52f2 |
| e3/run.sh | 282 | 98a27aae6fc5d467825aaa9a6be62d1732334f4f03bb7fb1ad85ddae30f1cc73 |
| e3/k.tgz | 3871402 | 69a20490b5303e095ed0c56c12cb4ff599cf8a045dc82161f547adeabd2006eb |
| e3/pins.json | 578 | c6c6c5098d486c753e2628f42981ab9bae162239b1670c62855f84e76726ea2c |
| e3/trinity.sh | 995 | 4335d3d21de10fa316da01bd547b5393a5b9a0585c2ea66ee40b40b2382e6edc |
| e3/trinity.py | 3343 | 845e64d5b81db45803892920fc49e4e4a3a72414054cd922fb7904daf048c5e5 |
| e3/readback.py | 2408 | 238ea609ea8124cedd3a12b944e5ebd3cbaa8e4bd086d25a96429da8e31ee0e6 |
| e3/SESSION_NAMES.template.list | 5608 | c60839b195a1f50d1c8c20b0cf0091b7bf4b0cd712b1049755e42688aab2fb72 |
| e3/STATUS_NAMES.template.list | 784 | bcd3bb9bc508ea2587552d9d6e7aa06e7ccfd6c064d7f51c481e519a16d00049 |

On trinity-1-18, the lane can first run the real-session interface:

    bash out/e3/trinity.sh <job_id> <sessions_file> <fresh_output_under_scratch>

The Trinity mode stages a 3 MiB checkpoint-like payload and 3 MiB export, uses a private root and a full 16 MiB tmpfs, and leaves E3.json plus logs under the supplied output directory. The build tested this exact interface with fake sessions and a method-only strict-sink adapter. This build used no network.

The Orchard CPU test requires hold, mint, release:

    sbatch --hold "$X/e3/e3.sh"
    # Install the complete fresh session mapping for the returned numeric job ID.
    scontrol release <job_id>

The job requests preempt, four CPUs, 16G and one hour. Its name is a15_cot_ap86b407cde192. Allow under one minute to submit held, 5–10 minutes to mint/install, and under one minute to release; queue time is unknown. Mint every name in SESSION_NAMES.template.list after replacing <job> with the allocation ID. Install X/n_s/sess_<job>.json with directory mode 0700 and file mode 0600, owned by the job user. Never print session values. Every cache use requires the exact 112-name set.

The Orchard job creates a 2 GiB random checkpoint-like payload on node-local disk. The build never creates that payload on Trinity. The job uploads ckstop, m100, o and u, four parts each, while X has zero free bytes. It verifies returned name, generation, size and MD5 against receipts and local SHA256; the readback tool also checks CRC32C. The u object contains the final upload diagnostics, including archive attempts and later data retries. Its four 512 KiB parts total 2 MiB; concatenate them in part order. Blank lines pad the two log snapshots. Part 0 becomes durable after the archive attempt, and parts 1–3 carry the final tail. The terminal response to u itself is verified through its receipt and remote metadata.

The observer patches methods on the original HTTPSConnection class. Its socket-free constructor check runs in each observer process. On ckstop part00, the observer closes the connection and raises a controlled interruption after GCS acknowledges a nonfinal chunk. A subsequent status query must return that Range, a subsequent data request must start at the acknowledged offset, and the part must finish with a valid receipt. E3.json records these events in resume_real, including real_service. Only status=PASS with real_service=true can justify the 1.5x stop-window factor. Offline PASS with real_service=false is protocol evidence only.

The real 2 GiB test uses the copier's normal 8 MiB chunks. Small Trinity/offline payloads use aligned 256 KiB chunks so a part has a nonfinal prefix. E3 records per-part receipt seconds and MB/s, total duration from the first part's start to the last part's completion, final-pass duration, SLURM_TMPDIR and free bytes. Total duration includes the forced retry delay. The interrupted part's receipt duration describes its successful resumed attempt; consult resume_real.events for its preceding attempt. No measured fixture rate is a real GCS rate.

STATUS_NAMES.template.list lists the 16 consumed part names, including all four u parts. The complete preparation set is 112 names. For independent remote readback on the credentialed node:

    python3 -I -s -B readback.py E3.json --bucket <bucket>

The readback tool performs serial, generation-pinned requests with an 8 MB/s limit and keeps credentials out of arguments and output. No real readback ran in this build.
