# Removal candidates (lane r1_ops; agents cannot delete; for the user)
Keep: work/snap_d8b03fd1/out (proof 1 archive), work/snap_2c67f1f2/out (proof 2 archive), work/drv/*.sh *.py *.out, ORCHARD_LEDGER.jsonl, STATUS.md.
- work/snap_1ec4a936, work/snap_841f0637, work/snap_a6b70ef2 (superseded frozen review copies, ~3.3 GB)
- work/snap_d8b03fd1/work/{test_*,pre_submit_*,fix*_*,audit_*,deploy_*,derive_*} and work/snap_2c67f1f2/work/{same} (test scratch written by my reruns)
- work/drv/{tests_local*,builders_*,guards_*,fixture_*} (driver test scratch, ~1.6 GB)
- work/ex1130, work/ex1130b (superseded extracted archives)
- work/snap_8246a4dd (243M) and work/drv_p3 test scratch: removable once R1 has launched and the S2 proof is done
- /scratch/jjyeung/orch_n30/r1_pkt/out/p_13d5fd61.tar (+ its copy in work/snap_a5dc8f30/out/): stray archive from a python-3.6 rerun of package_operator (01:00Z, r1_ops3); not a packet.
- work/chk11_summary.txt, work/chk11_local.log first run (python 3.6 failure; superseded by chk11_summary2.txt).
- (r1_ops3, 04:45Z, lane at 11 GB of 12 GB) superseded snapshots/drivers, all superseded by snap_9dd2fbb7 (A, running) and snap_6a5c7d00 (C): work/snap_1ec4a936, snap_782f303d, snap_841f0637, snap_a6b70ef2, snap_d8b03fd1, snap_f719b05f, snap_2c67f1f2, snap_8246a4dd, snap_a5dc8f30, snap_c1_fcc9a6f3, snap_c60b9015 (after C3 review GO); work/drv, drv_p2, drv_p3; work/ex1130, ex1130b, ex_6f8ed106, ex_c5f3847d. Keep snap_fac07052 (base of A reviews), snap_0647a0df (packet B fallback, mirrored), snap_9dd2fbb7, snap_6a5c7d00, drv_p4, drv_p5, drv_c1.
- /tmp/r1ops4_mirror.tar (732 MB on trinity-1-3 /tmp; transfer copy of the mirror, r1_ops4 05:58Z): removable now.
