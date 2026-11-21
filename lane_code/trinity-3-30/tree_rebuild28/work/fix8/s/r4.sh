W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $W
ls w24z11b/work/build24m4x2/support.py w24z12/work/ 2>&1 | head -3
S=$(ls w24z11b/work/build24m4x2/support.py 2>/dev/null || ls w24z12/work/build24m4x2/support.py 2>/dev/null || ls work/build24m4x2/support.py 2>/dev/null)
echo "SUPPORT=$S"; sha256sum $S
grep -n "^def \|^class \|^J\b\|^J *=" $S | head -40
for f in cap reseal; do python3 - "$S" "$f" <<'PY'
import ast,sys
src=open(sys.argv[1]).read()
for n in ast.parse(src).body:
    if getattr(n,'name',None)==sys.argv[2]: print(ast.get_source_segment(src,n) if hasattr(ast,'get_source_segment') else src.splitlines()[n.lineno-1:n.end_lineno])
PY
done
sed -n 1,30p $S
[ -e w30f1 ] && echo "w30f1 EXISTS" || echo "w30f1 absent"
sha256sum w28fix/n_go/SHA256SUMS.txt w28fix/s28fix_n_go.tar
/scratch/jjyeung/envs/p1cpu/bin/python -c "import sys;print(sys.version)"; /scratch/jjyeung/envs/p1cpu/bin/python -c "import torch;print('torch',torch.__version__)" 2>&1 | tail -1
