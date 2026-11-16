set -e
ls -la /scratch/jjyeung/n30_mirror/tree_rebuild/
cd /scratch/jjyeung/n30_mirror/tree_rebuild && sha256sum tree_rebuild_b5_ba346bd9.tar && cat tree_rebuild_b5_ba346bd9.tar | ssh -o ConnectTimeout=20 trinity-3-30.ib "cat > /scratch/jjyeung/orch_n30/b09_rlkit/work/tree_b5/tree_rebuild_b5_ba346bd9.tar && sha256sum /scratch/jjyeung/orch_n30/b09_rlkit/work/tree_b5/tree_rebuild_b5_ba346bd9.tar"
