export TZ=UTC; date -u
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28; H=$O/x_3fdda0fb
for f in 4.json archive.json review.json staging.json e.json p.json ids.json compare.json gate.json; do echo "== $f"; [ -f $B/$f ] && head -c 1500 $B/$f; echo; done
ls -la $B/e $B/p | head -30
echo "== H sums"; for f in $H/k/0.json $H/k/r.json $H/SHA256SUMS.txt $H/k/launch.json $H/k/archive.json $H/k/binding_evidence.json; do sha256sum $f; done
ls $H/k | wc -l; ls $H/k | tail -40
ls -la $B/q_6c18a2bf/o/native | head
squeue -u $USER -o '%i %j %P %T %M %R' | grep -v jjy_
