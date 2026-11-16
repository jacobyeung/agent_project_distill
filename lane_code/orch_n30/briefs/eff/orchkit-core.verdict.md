# Refute verdict for orchkit-core
refuted=False
reasons: The cited evidence checks out: pilots 169537 and 169589 were lost to stale pins (ORCH order 20261114T172706, "Faults 4 and 5 are one kind"), there are 21 pin groups with 2 disagreeing, and the 9 launcher forks and lost ledgers are real. 3-6 h/kit is only an estimate, double-counted with reader-harness. The pin invariant misses stale copies. provenance.py: not used by current launchers; scans /home.
fix (binding): Invariant: every 64-hex outside PINS.json fails unless in an allowlisted data field equal to a current entry. Prepare runs provenance only on a /scratch epoch checkout, Py3.6-safe, never on /home. Point pins audit at a full old kit (FAMILY/CONFIG/BATCH/MASK_CACHE) or drop the 21 comparison. Split 3-6 h between #3 and #5.
