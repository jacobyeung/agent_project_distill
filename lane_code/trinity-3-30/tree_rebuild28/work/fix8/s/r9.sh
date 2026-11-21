set -eu
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w30f1
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import sys;sys.path.insert(0,'n_go/b');import z;print('z.seal',z.seal('n_go'))"
tar cf s30f1_n_go.tar n_go
sha256sum s30f1_n_go.tar | tee s30f1_n_go.tar.sha256
ls -la s30f1_n_go.tar
ssh -o ConnectTimeout=20 trinity-3-30.ib 'mkdir -p /scratch/jjyeung/n30_mirror/tree_rebuild28'
tar cf - s30f1_n_go.tar s30f1_n_go.tar.sha256 BUILD_F1.json build.log tchk.log ship | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/n30_mirror/tree_rebuild28 && tar xf - && sha256sum s30f1_n_go.tar'
