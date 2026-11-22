hostname -s; date -u +%FT%TZ; df -h /scratch | tail -1
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; ls $W | tr '\n' ' '; echo
ls $W/w34 | tr '\n' ' '; echo; ls $W/w30f1 | tr '\n' ' '; echo
ls $W/w24z11b/work/build24m4x2 | tr '\n' ' '; echo
/scratch/jjyeung/envs/p1cpu/bin/python -c "import torch,sys;print(sys.version.split()[0],torch.__version__)"
ls $W/w30f1/tree | head -40 | tr '\n' ' '; echo
cat $W/w30f1/*.md 2>/dev/null | head -60
ls /scratch/jjyeung/envs
