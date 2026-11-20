from common import *
records=[
 dict(case='config-only candidate',output='ValueError: P_EXPORT_CONFIG_DIFFERENCE:max_pixels',state='Required CASE b blocker; all eight authenticated comparisons reproduce it',evidence='work/build24m4n/CONFIG_TESTS.json'),
 dict(case='initial comparison metadata',output='ValueError: P_EXPORT_HEAD_INIT_UNVERIFIED',state='Resolved by authenticating missing metadata from the supplied inside-workspace archive; unmocked comparison now recorded',evidence='work/build24m4n/METADATA_RECOVERY.json'),
 dict(case='initial synthetic duplicate fixture',output='ValueError: frame_pair_gap_seconds is only valid for paired frame_layout',state='Fixture corrected to use None for duplicate layout; final synthetic tests pass'),
 dict(case='initial native planner fixture',output='ValueError: R1_STAGING_PATH_MISSING:/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/data2root',state='Helper supplies empty read-only frame-root mountpoints; final planner and real mount tests pass'),
 dict(case='initial helper environment scan',output='ENV_UNRESOLVED:rcj/x.py:497:environment:environment capability escapes supported literal operations: subprocess.STDOUT',state='Replaced the symbolic stderr constant with its identical literal -2; scanner unchanged and passes'),
 dict(case='initial launch mount',output="bwrap: Can't mkdir parents for /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24n2/work/build24m4n/mount_k/node: Read-only file system",state='Helper precreates the job-root mountpoint under its scratch view; final real mount tests pass',evidence='attic/build24m4k/MOUNT_TESTS_initial.log'),
 dict(case='second launch mount',output="bwrap: Can't mkdir /tmp/q_22c714e1: Read-only file system",state='Helper mounts private /tmp, installs its job-local alias, then remounts /tmp read-only; final real mount tests pass',evidence='attic/build24m4k/MOUNT_TESTS_second.log'),
 dict(case='shell setup quoting',output="syntax error near unexpected token `('",state='The setup script was written through apply_patch and ran successfully'),
]
J.write(D/'FAILURES.json',dict(records=records,expected_negative_tests=['processor_resolution_pin_missing','P_EXPORT_CONFIG_DIFFERENCE:max_pixels','R1_SAMPLE_TOO_LARGE','R1_SAMPLE_GATE_FAILED','R1_PUBLICATION_INCOMPLETE','rdiff full production hash mismatch'],expected_negatives_passed=True,cluster_killed_work=False,production_run=False))
print('Failure evidence written; production blocker remains explicit')
