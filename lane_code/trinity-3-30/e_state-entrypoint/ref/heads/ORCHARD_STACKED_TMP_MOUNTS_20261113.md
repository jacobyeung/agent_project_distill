# Orchard stacked /tmp mounts

## Question and answer

How should an Orchard helper identify the filesystem that serves its working directory when mountinfo lists several mounts at `/tmp`?

Open the directory, read that descriptor's `mnt_id` from `/proc/self/fdinfo`, and require one corresponding mountinfo entry. Then apply the helper's existing filesystem and job-private scope checks to that entry. A pathname-prefix match does not identify the active mount when mountpoints overlap.

## Evidence

The retained filesystem probe on `orchard-community-2`, job 169107, records:

```text
372 225 0:37 / /tmp rw,relatime - tmpfs tmpfs rw,size=193206200k,inode64
753 372 9:127 /job_tmp/169107/.169107/_tmp /tmp rw,relatime - ext4 /dev/md127 rw,discard,stripe=2048
```

Its observed `/tmp` free space is 6,016,811,442,176 bytes. The source receipt is `/scratch/jjyeung/orch_cd/orchard_cp2/out/PROJECT_RATE_169107_RESULT.json`, SHA256 `3cc2930cd7c4c0748687dae680c7cc00876085341fa0035e0376aaaa22f71219`.

The state-copy bootstrap with SHA256 `d39ea48fe433806ed6eba36bcd8e509d311dcab9c87dcbb041ff30dc9a99dba7` uses `max((len(mountpoint), filesystem_type))`. Both entries have the same mountpoint length, so it selects `tmpfs` lexically and raises `LOCAL_DISK_REQUIRED`.

Calling that exact function with only the retained mountinfo reproduces the refusal. The test makes no connection, job step or live filesystem query. Its receipt is `/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_PREPARATION_169097/mount_selection_regression.json`, SHA256 `be898cd4e87d73e89bccaf57e9dfb990d8ad9468a66419ef1c58e18593c12f6c`.

Evalx's kernel-mount-ID implementation is described by `/scratch/jjyeung/orch_cd/evalx/work/milestone/ORCHARD_MOUNT_CONFIRMATION_REQUEST.json`. Its patch has SHA256 `742196ffc668353a6925b66e6f2c26693db6bb35e09f36d475002198b328ac34`.

## Alternatives and reasons

- **Longest pathname prefix:** insufficient when two entries have the same mountpoint.
- **Filesystem-name ordering, input-line ordering or largest mount ID:** none binds the selected entry to the directory the process actually opened.
- **Allowing tmpfs to make the refusal disappear:** changes the storage policy without proving which filesystem serves the path.
