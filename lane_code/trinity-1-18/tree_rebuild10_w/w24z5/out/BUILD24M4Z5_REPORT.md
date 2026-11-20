NO-GO for the complete launch request: two source-scope guarantees require the edits documented in NEEDS_OTHER_FILE_24M4Z5.md.
The three kit-review findings are fixed; ten fail-before probes fail on 24m4z4 and pass on the new bytes.
All required local suites pass, including ENOSPC, archive, current/legacy copiers, final retries, TERM/USR1, wrapper, E3 dry run and 20-object readback.
Final publication retries all pending destinations in stop/export/log/archive/ordinary order; sessions and receipts are validated and atomic.
The resumable protocol test retains completed parts and resumes an interrupted part without resending bytes; real GCS remains untested.
The wrapper preserves its job name, forwards batch signals, publishes once after the child exits and returns the child status.
Known embedded rc/rr survive the final archive; missing early-exit rr is null. Immediate stop identification needs a native stop marker.
The 47-minute bulk window needs 100.18 MB/s with 25% headroom for a 113 GB checkpoint plus the conservative 113 GB export allowance.
N and N_GO are resealed; the full 15cdc127 archive diff changes only four files and seals per N kit. Q, QD, rcj and tree 9d2bbb8a are unchanged.
UPLOADS_24M4Z5, _GO and _E3 are separate and below 5 MB per file. The 2 GiB rate payload exists only in the pending Orchard job.
The package contains out/work, excludes canonical trees, verifies its members and writes its checksum last.
