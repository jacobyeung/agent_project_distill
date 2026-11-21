set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w27fix; SRC=$F/src; T=$F/t1; K=$W/w26fix2/n_go
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME=/tmp/q_22c714e1/cache/hf XDG_CACHE_HOME=/tmp/q_22c714e1/cache PYTHONDONTWRITEBYTECODE=1
PY="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
date -u +%FT%TZ; hostname -s
test ! -e $T || { echo T1_EXISTS; exit 1; }
mkdir -p $T/s $T/ns/q_22c714e1 $T/ns/c7d31ddd
tar xf $K/k/t_e047002134f979bd.tar -C $T/s && echo "tree extracted: $(ls $T/s | wc -l) top entries; kit seal $(sha256sum $K/SHA256SUMS.txt | cut -c1-16)"
nice -n 10 timeout 300 $PY $SRC/build_layout.py $T/ns $SRC/proc9.tgz $W/ext/m400real 2>&1 | cut -c1-900
echo "== T1 on kit 06d9a1b5 (unfixed), job path names inside a namespace"
nice -n 10 timeout 500 bash $SRC/ns.sh $T/ns $PY $SRC/probe.py $T/s $K/b $SRC t1_old > $T/t1_old.out 2> $T/t1_old.err; echo "rc=$?"
cut -c1-2500 $T/t1_old.out; echo "-- stderr tail"; tail -5 $T/t1_old.err | cut -c1-400
date -u +%FT%TZ
