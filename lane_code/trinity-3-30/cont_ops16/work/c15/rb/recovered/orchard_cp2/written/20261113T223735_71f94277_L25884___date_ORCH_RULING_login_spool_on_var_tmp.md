<!-- recovered by seal_plan: transcript=71f94277 line=25884 utc=2026-11-13T22:37:35.256Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_RULING_login_spool_on_var_tmp.md heredoc_quoted -->
# ORCH ruling: put the login-side spool on the login host's local root disk (`/var/tmp`), if the bundle takes the path as a parameter

Your 2236Z BLOCKER. The gate is right to refuse a memory filesystem with a few MB free; the dry test did its job.

- The login host's root filesystem, which holds `/var/tmp`, had about 4.25 GB free at 18:41Z (the eval lane's read-only check). The spool holds the helper's raw return and an end receipt, a few KB to a few hundred KB.
- **Authorized:** use a private folder under `/var/tmp` on the login host as the spool parent (mode 0700, a name carrying the run and the attempt nonce), **provided** the bundle accepts the spool location as an argument or parameter of its documented commands, with no change to any file of the bundle. Run the same harmless dry test there first: the login-side disk check must accept it (a local ext4, xfs or btrfs entry selected by the folder's own mount id), at least 1 GB must be free, and the detached launch-and-fetch round trip must return a trivial command's output intact. Record the selected mount line.
- If the bundle hard-codes `/tmp` on the login side, or the check refuses `/var/tmp` too, stop and post the evidence; the change then belongs to leg_s1_canary and I route it.
- The spool files stay where they are written; list them (path, size) in your RESULT for the user's removal list. Nothing else changes: the node side still uses the job's private `/tmp`, which is a local ext4 mount.
- The hold on the cheap run itself stands until I name the replacement bundle.