set -eu
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w30f1
sha256sum -c s30f1_n_go.tar.sha256
tar cf - s30f1_n_go.tar s30f1_n_go.tar.sha256 BUILD_F1.json build.log tchk.log ship/pf.py ship/build.py ship/tchk.py u </dev/null | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/n30_mirror/tree_rebuild28 && tar xf - && sha256sum s30f1_n_go.tar'
echo END
