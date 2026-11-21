set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w27fix; SRC=$F/src; T=$F/t1; K0=$W/w26fix2/n_go; K=$F/n_go
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME=/tmp/q_22c714e1/cache/hf XDG_CACHE_HOME=/tmp/q_22c714e1/cache PYTHONDONTWRITEBYTECODE=1
PP="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export T27_OVL=$F/ovl2
date -u +%FT%TZ
echo "== T4 load list"
nice -n 10 timeout 300 bash $SRC/ns.sh $T/ns $PP $SRC/t4.py $T/s $K/b $SRC $SRC/fd60ac2f525727836258ae7ea0705ff3a49163ae74320f7bf8a17b66cd69f0c7 > $F/work/t4.out 2> $F/work/t4.err; echo "rc=$?"
cut -c1-700 $F/work/t4.out; echo "-- stderr tail"; tail -4 $F/work/t4.err | cut -c1-300
echo "== deliver"
test -e $F/s27fix_n_go.tar && { echo TAR_EXISTS; exit 1; }
echo "pycache $(find $K -name __pycache__ | wc -l)"
$PP -c "import sys;sys.path.insert(0,'$K/b');import z;print('seal',z.seal('$K'))"
tar cf $F/s27fix_n_go.tar -C $F n_go && sha256sum $F/s27fix_n_go.tar && tar tf $F/s27fix_n_go.tar | head -3 && tar tf $F/s27fix_n_go.tar | wc -l
mkdir -p $F/vt && tar xf $F/s27fix_n_go.tar -C $F/vt && diff -r $F/vt/n_go $K && echo "tar round trip identical" && (cd $F/vt/n_go && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')
echo "== word check on new files"; grep -n -i -E "distill|carrier|habitat|vsi|bench|n30|tree_rebuild|qwen|dataset|teacher" $K/b/mg.py $K/b/pf.py; echo "(end)"
P=$F/packet; mkdir -p $P/old $P/new $P/scripts $P/logs $P/gpu_test
cp $K0/b/a.py $K0/b/pl.py $K0/SHA256SUMS.txt $K0/BUILD.json $P/old/
cp $K/b/a.py $K/b/pl.py $K/b/mg.py $K/b/pf.py $K/SHA256SUMS.txt $K/BUILD.json $P/new/
cp $F/work/A_PY.diff $F/work/PL_PY.diff $F/work/SHA256SUMS.diff $P/
for n in patch3.py bfix.py build_layout.py t27probe.py probe.py ns.sh ns3.sh t2.py t3.py t4.py t_guard.py run1.sh run2.sh run3.sh run4.sh run5.sh; do cp $SRC/$n $P/scripts/; done
cp $T/t1_old.out $P/logs/t1_unfixed_kit.out
for n in t2.out t3.out t4.out t_guard.out t_fw_after.log; do cp $F/work/$n $P/logs/; done
echo "$(sha256sum < $F/s27fix_n_go.tar | cut -c1-64)  s27fix_n_go.tar" > $P/TAR_SHA256.txt
du -sk $P; find $P -type f | wc -l
tar cf - -C $F packet | sha256sum | cut -c1-16
date -u +%FT%TZ
