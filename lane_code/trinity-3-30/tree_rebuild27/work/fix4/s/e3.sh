F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix; SRC=$F/src; PV=/scratch/jjyeung/envs/vllm/bin/python
date -u +%TZ
ls -la /scratch/jjyeung/envs/vllm/bin/python* | cut -c1-200; readlink -f $PV
ls -la /scratch/jjyeung/envs/vllm/lib/ | head; ls /scratch/jjyeung/envs/vllm/lib/python3.12/os.py /scratch/jjyeung/envs/vllm/lib/python3.12/encodings/__init__.py 2>&1 | head -3
cat /scratch/jjyeung/envs/vllm/pyvenv.cfg 2>&1 | head -5
mkdir -p $F/work/diag
echo "-- A: -I"; bash $SRC/ns4.sh $F/work/diag a15sim $PV -I -c 'import sys;print(sys.prefix,sys.base_prefix)' 2>&1 | tail -2 | cut -c1-200
echo "-- B: -B -s"; bash $SRC/ns4.sh $F/work/diag a15sim $PV -B -s -c 'import sys;print(sys.prefix,sys.base_prefix)' 2>&1 | tail -2 | cut -c1-200
echo "-- C: -B -s with PYTHONPATH"; PYTHONPATH=$F/ovl_fla bash $SRC/ns4.sh $F/work/diag a15sim $PV -B -s -c 'import sys;print(sys.prefix,sys.base_prefix)' 2>&1 | tail -2 | cut -c1-200
echo "-- D: outside sandbox -B -s"; $PV -B -s -c 'import sys;print(sys.prefix,sys.base_prefix,sys.path[:4])' 2>&1 | tail -2 | cut -c1-300
echo "-- env"; env | grep -i "^PYTHON\|CONDA\|VIRTUAL" | cut -c1-200
head -12 $F/work/sim1/e.txt | cut -c1-200
