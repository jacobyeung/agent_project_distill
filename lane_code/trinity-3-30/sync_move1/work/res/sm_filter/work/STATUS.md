Updated: 2026-11-19T21:31:18Z

All six tasks are complete. The owner package is sealed and verified in out/.

1. Both filter paths share the pruning rules; dry_count applies them at every ancestor gate.
2. Both manifest writers use mtime=0 and no stored filename; repeat-run bytes match.
3. All eight inventories were replayed by commit and label. Estimates retain 22.0–53.1 MB; the source/deliverable exception above 40 MB is documented.
4. Both robust dry scans exited 0. The old scan kept 43,722 files / 357,375,373 bytes. The final new scan kept 3,537 files / 38,301,342 bytes; its per-lane totals match STATS.
5. Python 3.6.8 tests pass: 62 kept cases, 79 excluded path cases, exact NUL output, FIFO/symlinks, MAXDIR/protection, deterministic gzip and root-gate parity. Python 3.11/3.12 are unavailable on PATH.
6. Install/rollback fixtures pass. SHA256SUMS verifies all 27 package files; PREIMAGE and POSTIMAGE each verify exactly the two replacement tools. Inputs and installed tools remain unchanged.

No pending local work remains. The owner installs on trinity-3-30 using out/install.sh.
