set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w27fix; SRC=$F/src; T=$F/t1; K=$F/n_go
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME=/tmp/q_22c714e1/cache/hf XDG_CACHE_HOME=/tmp/q_22c714e1/cache PYTHONDONTWRITEBYTECODE=1
PP="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
date -u +%FT%TZ
OVL=$F/ovl2; WHL=/scratch/jjyeung/orch_n30/sb_f64/work/wheels/torchvision-0.26.0+cpu-cp312-cp312-manylinux_2_28_x86_64.whl
if [ ! -d $OVL ]; then mkdir -p $OVL && nice -n 10 $PP -m zipfile -e $WHL $OVL; fi
echo "wheel sha256 $(sha256sum < $WHL | cut -c1-64)"
export T27_OVL=$OVL
nice -n 10 timeout 200 $PP -c "
import sys;sys.path.append('$OVL')
import torch,torchvision;print('torchvision',torchvision.__version__,'with torch',torch.__version__)
from transformers.utils import is_torchvision_available;print('transformers sees torchvision',is_torchvision_available())" 2>&1 | tail -3 | cut -c1-300
echo "== T2 item-1 test on the fixed bytes (p1cpu + torchvision 0.26.0+cpu overlay, CVD='')"
nice -n 10 timeout 500 bash $SRC/ns.sh $T/ns $PP $SRC/t2.py $T/s $K/b $SRC > $F/work/t2.out 2> $F/work/t2.err; echo "rc=$?"
cut -c1-1300 $F/work/t2.out; echo "-- stderr tail"; tail -4 $F/work/t2.err | cut -c1-300
echo "== T3 wiring: real plan_payload + stage hook on a synthetic handover with the real processor files"
T3=$F/t3c; mkdir -p $T3/ns/q_22c714e1
nice -n 10 timeout 500 bash $SRC/ns3.sh $T3/ns $T/ns/c7d31ddd $PP $SRC/t3.py $T/s $K/b $SRC $T/ns/q_22c714e1/p/q/u > $F/work/t3.out 2> $F/work/t3.err; echo "rc=$?"
cut -c1-1500 $F/work/t3.out; echo "-- stderr tail"; tail -8 $F/work/t3.err | cut -c1-500
echo "pycache in kit: $(find $K -name __pycache__ | wc -l); seal $(sha256sum < $K/SHA256SUMS.txt | cut -c1-16)"
date -u +%FT%TZ
