W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
tar tf /scratch/jjyeung/n30_mirror/r1_ops6/cprime_build_32337655.tar | grep -E "benchmark_scene_exclusions|66c427e2|remove_[0-9]|/k/[^/]+$" | head -60
echo "== census14 inputs"; grep -nE "LOC|/scratch|derive|r1_pkt" $W/w14/work/build14/census14.py | head -20
ls $W/w14/work/build14/proofs | tr '\n' ' '
