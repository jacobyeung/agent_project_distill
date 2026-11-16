<!-- recovered by seal_plan: transcript=71f94277 line=25640 utc=2026-11-13T22:03:46.590Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_URGENT_runtime_link_check_local_first.md <<'EOF'
# ORCH, urgent: find the offending runtime link on CPU first, locally if the archives are here; then fix, I confirm, one more attempt

Your 2201Z BLOCKER. The mount fix worked on the real node (job 169307 selected the ext4 job mount), and runtime group 0 staged in 20.5 s. The refusal in group 1 ("Runtime symlink escapes its archive") is the extractor judging a link by resolving it on the host.

**Find the member before another job touches a GPU:**
1. **Local first.** The three runtime groups were pushed to Orchard from Trinity. If the parts of group 1 (`50011a59.*`) and the other two groups exist on a Trinity `/scratch` you can read (your own or orchard_port's push sources), with the hashes in `ORCHARD_ASSETS.json`, run your extractor on all three on CPU here, into a private folder on `/scratch`, and name every link it would refuse with its target. That needs no Orchard job and no question. Stay within your lane's disk allowance; if the archives are larger than you may hold, read them in place and extract only the link entries (names and targets), not the files.
2. **If they are not local:** one CPU-only job on Orchard `general` is authorized for this preflight (no GPU, job-local storage, no export, at most 15 minutes), through the accepted launcher's submission path or the simplest equivalent; report the job id.

**The fix I expect, to be confirmed by me from the diff:** judge a link by its target computed within the extraction root (lexically, without resolving through the host's filesystem); a relative link that stays inside the root passes; an absolute target passes only if it is one of an explicit, pinned list of registered runtime links (list them, with why each is needed, for example the interpreter); everything else still refuses, and the refusal names the member and target. Keep every traversal guard. Tests: the real offending entry passes, a link escaping with `..` refuses, an unlisted absolute target refuses.

Then post the diff, digest and test log; I confirm within minutes and you make one more step-50 attempt. Step 100's export is authenticated and waiting; a correct read later is better than a fast one now.
EOF
cp $C/orchard_cp2/events/20261113T2201Z_BLOCKER_cheap_copy_mount_selection.md $C/leg_s1_canary/inbox/20261113T2201Z_BLOCKER_orchard_cp2_cheap_copy_mount_selection.md
cat > $C/leg_s1_canary/inbox/${N}_ORCH_URGENT_fix_mount_selector_in_state_copy.md <<'EOF'
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
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> $C/ORCH_HANDOFF.md <<EOF
$T orch-home-distill-79: evalx BLOCKER 2201Z: corrected rehearsal job 169307 (orchard-community-2, 21:55:03-21:56:25Z) PASSED the mount gate on the real node (kernel mount 801, /dev/md127 ext4, root /job_tmp/169307/.169307/_tmp), staged runtime group 0 in 20.5 s, then FAILED extracting runtime group 1: 'Runtime symlink escapes its archive' (the extractor resolves relative link targets on the host); no export fetch, no generation; GPU clean at exit. ORDERED ($N): find the offending link on CPU, locally if the runtime archives are on Trinity, else ONE CPU-only general job (15 min) authorized; fix = judge links lexically within the extraction root + a pinned allowlist of absolute runtime links; I confirm the diff; then one more step-50 attempt.
$T orch-home-distill-79: orchard_cp2 BLOCKER 2201Z: the state-copy bundle's operator_transport.py:local_disk has the same stacked-mount defect (max((len(mountpoint), fstype)) picks the hidden tmpfs -> LOCAL_DISK_REQUIRED); reproduced with the held real mount lines before any launch; no sessions minted. Ordinary save completed at step 105 (75.7 s); training at step 107, steps 130-133 s; RUN.json retained (93 B, sha 7f9b2593). ORDERED leg_s1_canary ($N): fix by kernel mount id, check every mount selector in the bundle, new bundle + diff for my read; the operator's order will be amended.
EOF
echo done $N