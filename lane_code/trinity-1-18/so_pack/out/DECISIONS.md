# Release contract

- The forbidden-word rule covers operational names, Slurm fields, argv, environment values, workdirs, delivery members and runtime paths. It excludes private archive contents, decoded bundles, code comments, stdin bodies and log contents. Stale identities are checked recursively in all bytes.
- Every generated phase uses umask 077. Placement creates 0700 directories and 0600 files. The batch extracts only under its 0700 /tmp allocation directory; the native process guard checks job descendants.
- All local gates and all operational-script preflights finish before transport. Submission uses timeout-bounded calls, local polling at intervals of at least 60 seconds and an 8,000,000-byte/s stream cap. Failed transport is never retried.
- The explicit-token builders are added files under so_pack_builders. Native builders and embedded operational assets retain their input bytes. Their token switches default off.
- A SHA-pinned Trinity token ledger is mandatory. Explicit tokens are checked before the builder starts; random tokens are checked immediately after the builder returns. Orchard mkdir remains the live collision guard.
- Login placement and fill run under /usr/bin/python3 3.6.8. The job payload targets Python 3.12. Local receipts cannot replace the allocated native CPU proof.
- Missing authenticated source/export/dependency mirrors block release. A model stub establishes only its stated rehearsal scope.
