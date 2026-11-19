W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21e; Q=$C/pkg/work/build21/kits/q
cat $C/cf21e.log; grep -n -i -A8 'resolve' $C/pkg/work/build21/OPERATOR.md | head -60 | cut -c1-400
cat $C/pkg/work/build21e/UPLOAD_DIFF.json | head -c 1500; echo
cd $Q && sha256sum BUILD.json SHA256SUMS.txt b/z.py k/p.json && tar cf $W/work/k21e.tar BUILD.json SHA256SUMS.txt b/z.py k/p.json && stat -c %s $W/work/k21e.tar && sha256sum $W/work/k21e.tar
grep -n 'x.py\|bootstrap\|def ' $Q/b/x.py | head; head -c 1200 $C/pkg/work/build21e/LISTING_TEMPLATE.json
