set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w27fix; SRC=$F/src; T=$F/t1; K0=$W/w26fix2/n_go; K=$F/n_go
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME=/tmp/q_22c714e1/cache/hf XDG_CACHE_HOME=/tmp/q_22c714e1/cache PYTHONDONTWRITEBYTECODE=1
P1="nice -n 10 timeout 600 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
PV="/scratch/jjyeung/envs/vllm/bin/python -I -s -B"
date -u +%FT%TZ; hostname -s
test ! -e $K || { echo KIT_EXISTS; exit 1; }
cp -a $K0 $K || exit 1
echo "== build"; $P1 $SRC/patch3.py $K $SRC && $P1 $SRC/bfix.py $K0/BUILD.json $K || { echo BUILD_FAIL; exit 1; }
$P1 -c "import sys;sys.path.insert(0,'$K/b');import z;print('seal new',z.seal('$K'))" 2>&1 | tail -2
$P1 -c "import sys;sys.path.insert(0,'$K0/b');import z;print('seal old',z.seal('$K0'))" 2>&1 | tail -2
sha256sum $K/SHA256SUMS.txt $K/BUILD.json $K/b/a.py $K/b/pl.py $K/b/mg.py $K/b/pf.py
diff -rq $K0 $K; echo "diff rc=$?"
mkdir -p $F/work
diff $K0/b/a.py $K/b/a.py > $F/work/A_PY.diff; diff $K0/b/pl.py $K/b/pl.py > $F/work/PL_PY.diff; diff $K0/SHA256SUMS.txt $K/SHA256SUMS.txt > $F/work/SHA256SUMS.diff; cat $F/work/SHA256SUMS.diff
$P1 -c "
import json,base64,ast
o=[json.loads(open(p).read()) for p in ('$K0/BUILD.json','$K/BUILD.json')]
d=[json.loads(base64.b64decode(x['payload'])) for x in o]
print('BUILD outer diffs',[k for k in o[0] if o[0][k]!=o[1][k]],'payload diffs',[k for k in set(d[0])|set(d[1]) if d[0].get(k)!=d[1].get(k)],d[1]['kit_sha256'])
[ast.parse(open('$K/b/'+n).read()) for n in ('a.py','pl.py','mg.py','pf.py')];print('parse ok')
"
stat -c '%a %n' $K/b/mg.py $K/b/pf.py $K/b/z.py $K/b/pl.py $K/b/a.py
find $K -name __pycache__ | wc -l
echo "== tree build check (launch_r1.build.verify, as a.py runs it)"
$P1 -c "
import sys;sys.path.insert(0,'$T/s')
from pathlib import Path
from launch_r1.build import verify
print('build.verify',verify(Path('$K')))" 2>&1 | tail -3 | cut -c1-300
echo "== replica: add N's real pose stream receipts"
for f in $SRC/pose/*; do h=$(basename $f); [ "$(sha256sum < $f | cut -d' ' -f1)" = "$h" ] && cp -n $f $T/ns/q_22c714e1/p/q/u/$h; done; ls $T/ns/q_22c714e1/p/q/u | wc -l
mkdir -p $T/ns/q_22c714e1/p/i
echo "== T2 item-1 test on the fixed bytes (vllm env: torchvision present; CVD=''; NVML-based availability, no driver query)"
PYTORCH_NVML_BASED_CUDA_CHECK=1 nice -n 10 timeout 500 bash $SRC/ns.sh $T/ns $PV $SRC/t2.py $T/s $K/b $SRC > $F/work/t2.out 2> $F/work/t2.err; echo "rc=$?"
cut -c1-1500 $F/work/t2.out; echo "-- stderr tail"; tail -4 $F/work/t2.err | cut -c1-300
echo "== T-guard (vllm env, driver entry points stubbed)"
(cd $F/work && nice -n 10 timeout 300 $PV $SRC/t_guard.py $T/s $K/b > $F/work/t_guard.out 2> $F/work/t_guard.err; echo "rc=$?")
cut -c1-1200 $F/work/t_guard.out; echo "-- stderr tail"; tail -4 $F/work/t_guard.err | cut -c1-300
echo "== T3 wiring: real plan_payload + stage hook on a synthetic handover with the real processor files"
T3=$F/t3; mkdir -p $T3/ns/q_22c714e1
PYTORCH_NVML_BASED_CUDA_CHECK=1 nice -n 10 timeout 500 bash $SRC/ns3.sh $T3/ns $T/ns/c7d31ddd $PV $SRC/t3.py $T/s $K/b $SRC $T/ns/q_22c714e1/p/q/u > $F/work/t3.out 2> $F/work/t3.err; echo "rc=$?"
cut -c1-1500 $F/work/t3.out; echo "-- stderr tail"; tail -6 $F/work/t3.err | cut -c1-400
echo "== fix_spawn regression (t_fw.py, p1cpu) on the new kit"
mkdir -p $F/work/fwreg && (cd $F/work/fwreg && $P1 $W/w26fix2/work/src/t_fw.py $W/w26fix2/work/ttree $K $F/work/fwreg after > $F/work/t_fw_after.log 2>&1; echo "rc=$?")
grep -E "^(T1_wrapper_installed|T4_equal|T3_|DONE|block_exec)" $F/work/t_fw_after.log | cut -c1-330
find $K -name __pycache__ | wc -l
date -u +%FT%TZ
