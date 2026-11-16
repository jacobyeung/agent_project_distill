<!-- recovered by seal_plan: transcript=71f94277 line=25640 utc=2026-11-13T22:03:46.590Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_URGENT_fix_mount_selector_in_state_copy.md heredoc_quoted -->
# ORCH, urgent: the state-copy bundle's mount selector fails on the real node layout; fix it and every selector like it

The operator reproduced, before launching anything, that `operator_transport.py:local_disk` rejects Orchard's real `/tmp` (its BLOCKER is copied into your inbox as `20261113T2201Z_BLOCKER_orchard_cp2_cheap_copy_mount_selection.md`; regression receipt `orchard_cp2/out/STATE_COPY_PREPARATION_169097/mount_selection_regression.json`). The node stacks two mounts on `/tmp`:

```text
372 225 0:37 / /tmp rw,relatime - tmpfs tmpfs rw,size=193206200k,inode64
753 372 9:127 /job_tmp/<job>/.<job>/_tmp /tmp rw,relatime - ext4 /dev/md127 rw,discard,stripe=2048
```

`max((len(mountpoint), filesystem_type))` picks the hidden tmpfs. The eval lane hit the same class of defect in a real job an hour ago and fixed it by selecting the mount through the kernel mount id of an open handle on the directory (`/proc/self/fdinfo/<fd>`, field `mnt_id`), then applying its unchanged checks to that single mountinfo entry (its diff: `/scratch/jjyeung/orch_cd/evalx/work/milestone/ORCHARD_MOUNT_FIX.patch`). That fix passed on the real node (job 169307 selected the ext4 mount).

1. Fix `local_disk` the same way, and **check every place in the bundle that picks a mount or a filesystem from the mount table** (login side and node side): list each, say whether it had the same defect, and fix those that did. Keep the filesystem allowlist and the scope gates as they are; record the selected entry and all `/tmp` entries in the evidence, on success and on refusal.
2. Tests with the real lines above (both orders), a network filesystem control that still refuses, and the reviewer's and operator's regressions.
3. Deliver a new bundle with the diff against cc25e95e; say which files changed and that the validator, return record and upload code did not. I read the diff myself and then amend the operator's order.

The ordinary save completed at step 105 (the operator's 21:54Z snapshot); the cheap run's window is open until about 23:30Z, so deliver as soon as the tests pass.