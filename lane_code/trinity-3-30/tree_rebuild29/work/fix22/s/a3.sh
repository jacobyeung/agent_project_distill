W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/w24y2 || exit 1
ls out | tr '\n' ' '; echo; ls work | tr '\n' ' '; echo
for d in out/kit_qd work/build24/kits/qd out/kits/qd; do [ -d $d ] && { echo "QD $d"; sha256sum $d/SHA256SUMS.txt; }; done
Q=$(for d in out/kit_qd work/build24/kits/qd; do [ -d $d ] && echo $d && break; done); echo "USING $Q" >&2
grep -rl -E "9d2bbb8a|5f2d77c4" $Q >&2
tar czf - -C $(dirname $Q) $(basename $Q)
