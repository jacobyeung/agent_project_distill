set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; W2=$W/w26fix2; SRC=$W2/work/src; K0=$W/w26fix/n_go; K=$W2/n_go
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
P1="nice -n 10 timeout 600 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
cp -a $K0 $K || exit 1
echo "== torch envs"; PY=""
for e in p1cpu vllm sam3_capretry_native_v1; do r=$(nice -n 10 timeout 300 /scratch/jjyeung/envs/$e/bin/python -I -s -B -c 'import sys,torch;print(sys.version.split()[0],torch.__version__)' 2>&1 | tail -1); echo "$e: $r"; [ -z "$PY" ] && echo "$r" | grep -q '^3\.1[2-9]' && PY=/scratch/jjyeung/envs/$e/bin/python; done
echo "PY=$PY"; T="nice -n 10 timeout 600 $PY -I -s -B"
echo "== build"; $P1 $SRC/patch2.py $K $SRC/fw.py && $P1 $SRC/bfix.py $K0/BUILD.json $K || { echo BUILD_FAIL; exit 1; }
echo "== test tree"; cp -a $W/w26fix/tree $W2/work/ttree; TT=$W2/work/ttree
if $T -c "import sys;sys.path.insert(0,'$TT');import student_pilot.carrier_c1_run" > $W2/work/realimport.log 2>&1; then echo "real module imports: append stub"; cat $SRC/stub.txt >> $TT/student_pilot/carrier_c1_run.py
else echo "real module does not import:"; tail -3 $W2/work/realimport.log; cp $SRC/stub.txt $TT/student_pilot/carrier_c1_run.py; fi
cd $W2/work
echo "== T before (kit $K0)"; $T $SRC/t_fw.py $TT $K0 $W2/work before 2>&1 | tee $W2/work/t_before.log | cut -c1-1500
echo "== T after (kit $K)"; $T $SRC/t_fw.py $TT $K $W2/work after 2>&1 | tee $W2/work/t_after.log | cut -c1-1800
echo "== T5 seal/diff/parse"
$P1 -c "import sys;sys.path.insert(0,'$K/b');import z;print('seal new',z.seal('$K'))" 2>&1 | tail -2
$P1 -c "import sys;sys.path.insert(0,'$K0/b');import z;print('seal old',z.seal('$K0'))" 2>&1 | tail -2
sha256sum $K/SHA256SUMS.txt $K/BUILD.json $K/b/a.py $K/b/fw.py
diff -rq $K0 $K; echo "diff rc=$?"
diff $K0/b/a.py $K/b/a.py > $W2/work/A_PY.diff; diff $K0/SHA256SUMS.txt $K/SHA256SUMS.txt > $W2/work/SHA256SUMS.diff; cat $W2/work/SHA256SUMS.diff
$P1 -c "
import json,base64,sys
o=[json.loads(open(p).read()) for p in ('$K0/BUILD.json','$K/BUILD.json')]
d=[json.loads(base64.b64decode(x['payload'])) for x in o]
print('BUILD outer keys same',sorted(o[0])==sorted(o[1]),'outer diffs',[k for k in o[0] if o[0][k]!=o[1][k]])
print('payload diffs',[k for k in set(d[0])|set(d[1]) if d[0].get(k)!=d[1].get(k)],d[1]['kit_sha256'])
import ast;[ast.parse(open(p).read()) for p in ('$K/b/a.py','$K/b/fw.py')];print('parse ok')
"
stat -c '%a %n' $K/b/fw.py $K/b/z.py $K/b/a.py
echo "== word check"; grep -n -i -E "student|distill|carrier|habitat|vsi|bench|r1|n30|tree_rebuild" $K/b/fw.py | grep -v -E "^[0-9]+:\s*from student_pilot|^[0-9]+:    from student_pilot" ; echo "(word check end)"
echo "== tar"; ls $W/w26fix; for t in $W/w26fix/*.tar; do [ -f "$t" ] && tar tf $t | head -3; done
tar cf $W2/s26fix2_n_go.tar -C $W2 n_go && sha256sum $W2/s26fix2_n_go.tar && tar tf $W2/s26fix2_n_go.tar | head -3
echo "== packet"; P=$W2/work/packet; mkdir -p $P/old $P/new $P/scripts $P/logs
cp $K0/b/a.py $K0/SHA256SUMS.txt $K0/BUILD.json $P/old/; cp $K/b/a.py $K/b/fw.py $K/SHA256SUMS.txt $K/BUILD.json $P/new/
cp $W2/work/A_PY.diff $W2/work/SHA256SUMS.diff $P/; cp $SRC/* $P/scripts/; cp $W2/work/t_before.log $W2/work/t_after.log $W2/work/realimport.log $P/logs/
du -sk $P
echo ALLDONE
