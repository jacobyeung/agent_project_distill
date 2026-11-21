W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $W || exit 1
for d in w24z12/out/kit_n_go; do sha256sum $d/k/y.json; ls $d | head; grep -E ' (\./)?k/y\.json$' $d/SHA256SUMS* 2>/dev/null; done
ls w24z11b/out | head -40
grep -n -iE 'armed|out_dir|output|n_go' w24z11b/out/ARM_LAUNCH_24M4Z11B.md | head -20
ls -d w24z1[5-9]* 2>/dev/null
