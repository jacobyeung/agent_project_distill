W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; mkdir -p /scratch/jjyeung/orch_n30/n_review/r1d
date -u +%TZ
echo "== rt24h"; ls -la $W/work/rt24h; sha256sum $W/work/rt24h/RESULT.json; cat $W/work/rt24h/RESULT.json | head -c 12000; echo
echo "== REPORT head"; head -c 5000 $W/work/rt24h/REPORT.md
echo "== b diffs 24m4e -> 24m4h"; for f in a ep i pl rb rd rg z; do echo "#### $f.py $(sha256sum < $W/w24e/out/kit_n_go/b/$f.py|cut -c1-16) -> $(sha256sum < $W/w24h/out/kit_n_go/b/$f.py|cut -c1-16)"; diff -u $W/w24e/out/kit_n_go/b/$f.py $W/w24h/out/kit_n_go/b/$f.py > /scratch/jjyeung/orch_n30/n_review/r1d/diff_$f.txt; wc -l < /scratch/jjyeung/orch_n30/n_review/r1d/diff_$f.txt; done
echo "== kit qd vs n_go b/"; diff <(sort -k2 $W/w24h/out/kit_qd/SHA256SUMS.txt) <(sort -k2 $W/w24h/out/kit_n_go/SHA256SUMS.txt)
ls $W/w24h/out/ $W/w24h/work | head -40
