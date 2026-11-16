<!-- recovered by seal_plan: transcript=71f94277 line=25884 utc=2026-11-13T22:37:35.256Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; sed -n '14,30p' $C/orchard_cp2/events/20261113T2236Z_BLOCKER_login_tmpfs_refuses_dry_test.md | cut -c1-700; cat > $C/orchard_cp2/inbox/${N}_ORCH_RULING_login_spool_on_var_tmp.md <<'EOF'
# ORCH ruling: put the login-side spool on the login host's local root disk (`/var/tmp`), if the bundle takes the path as a parameter

Your 2236Z BLOCKER. The gate is right to refuse a memory filesystem with a few MB free; the dry test did its job.

- The login host's root filesystem, which holds `/var/tmp`, had about 4.25 GB free at 18:41Z (the eval lane's read-only check). The spool holds the helper's raw return and an end receipt, a few KB to a few hundred KB.
- **Authorized:** use a private folder under `/var/tmp` on the login host as the spool parent (mode 0700, a name carrying the run and the attempt nonce), **provided** the bundle accepts the spool location as an argument or parameter of its documented commands, with no change to any file of the bundle. Run the same harmless dry test there first: the login-side disk check must accept it (a local ext4, xfs or btrfs entry selected by the folder's own mount id), at least 1 GB must be free, and the detached launch-and-fetch round trip must return a trivial command's output intact. Record the selected mount line.
- If the bundle hard-codes `/tmp` on the login side, or the check refuses `/var/tmp` too, stop and post the evidence; the change then belongs to leg_s1_canary and I route it.
- The spool files stay where they are written; list them (path, size) in your RESULT for the user's removal list. Nothing else changes: the node side still uses the job's private `/tmp`, which is a local ext4 mount.
- The hold on the cheap run itself stands until I name the replacement bundle.
EOF
cp $C/orchard_cp2/events/20261113T2236Z_BLOCKER_login_tmpfs_refuses_dry_test.md $C/leg_s1_canary/inbox/20261113T2236Z_BLOCKER_orchard_cp2_login_tmpfs_refuses_dry_test.md
cat > $C/leg_s1_canary/inbox/${N}_ORCH_NOTE_login_spool_location.md <<'EOF'
# ORCH note: the login host's `/tmp` is a memory filesystem; say how the login-side spool location is chosen

The operator's harmless dry test of the login-side disk check refused (its BLOCKER is copied into your inbox): the login host's `/tmp` is tmpfs (6.6 GB, nearly full). I ruled that the spool goes under `/var/tmp` on the login host (local root disk, about 4 GB free), provided the bundle takes the spool parent as an argument with no file change.

In your replacement bundle's RESULT, state plainly: which argument or operator-file field sets the login-side spool parent, that `/var/tmp/<private folder>` is a valid value, and that nothing on the node side depends on it. If the login side hard-codes `/tmp`, make the parent a required argument in the replacement bundle (a two-line change) and include it in the diff. Keep the node side on the job's private `/tmp`.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: orchard_cp2 BLOCKER 2236Z: the authorized login-side dry test of the state-copy bundle refused LOCAL_DISK_REQUIRED: the login host's /tmp is tmpfs (mount id 48, 6.58 GB); nothing created, no session minted. RULING ($N): spool under /var/tmp on the login host (local root disk, ~4.25 GB free at 18:41Z) if the bundle takes the spool parent as a parameter without a file change; same dry test first; else stop and I route to the canary lane. Canary lane told to state the parameter (or make it one) in the replacement bundle. Project free 449.7 GB at 22:34Z." >> $C/ORCH_HANDOFF.md; echo done $N