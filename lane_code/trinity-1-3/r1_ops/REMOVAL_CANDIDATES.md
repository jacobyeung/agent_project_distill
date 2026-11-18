# Removal candidates (lane r1_ops; agents cannot delete; for the user)
Keep: work/snap_d8b03fd1/out (proof 1 archive), work/snap_2c67f1f2/out (proof 2 archive), work/drv/*.sh *.py *.out, ORCHARD_LEDGER.jsonl, STATUS.md.
- work/snap_1ec4a936, work/snap_841f0637, work/snap_a6b70ef2 (superseded frozen review copies, ~3.3 GB)
- work/snap_d8b03fd1/work/{test_*,pre_submit_*,fix*_*,audit_*,deploy_*,derive_*} and work/snap_2c67f1f2/work/{same} (test scratch written by my reruns)
- work/drv/{tests_local*,builders_*,guards_*,fixture_*} (driver test scratch, ~1.6 GB)
- work/ex1130, work/ex1130b (superseded extracted archives)
- work/snap_8246a4dd (243M) and work/drv_p3 test scratch: removable once R1 has launched and the S2 proof is done
- /scratch/jjyeung/orch_n30/r1_pkt/out/p_13d5fd61.tar (+ its copy in work/snap_a5dc8f30/out/): stray archive from a python-3.6 rerun of package_operator (01:00Z, r1_ops3); not a packet.
- work/chk11_summary.txt, work/chk11_local.log first run (python 3.6 failure; superseded by chk11_summary2.txt).
