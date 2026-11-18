cd /scratch/jjyeung/n30_mirror/tree_rebuild; ls -la tree_rebuild_b14_094933b3.tar
cat tree_rebuild_b14_094933b3.tar | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "cd /scratch/jjyeung/orch_n30/r1_ops6/rec/tree_rebuild_w && tar xzf - work/base/tree_b01ce449 && du -sh work/base/tree_b01ce449"
echo rc=$?
