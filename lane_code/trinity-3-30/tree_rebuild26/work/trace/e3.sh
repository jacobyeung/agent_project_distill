set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w26fix/tree; K=$W/w24/work/build24k
echo "== admit body"; sed -n 20,60p $T/student_pilot/s1_admission.py; sed -n 133,330p $T/student_pilot/s1_admission.py
echo "== tar top"; tar tf $W/w26fix/n_go/k/t_e047002134f979bd.tar | cut -d/ -f1-2 | sort -u | grep -v '^student_pilot/' | head -40
echo "== static cuda queries in tree"; grep -rn --include=*.py -E 'cuda\.(is_available|device_count|init|_lazy_init|current_device|get_device|synchronize|set_device|mem_get_info|memory_allocated)|pin_memory|_cuda_getDeviceCount|torch\.device\(.cuda|is_initialized' $T | head -120
echo "== envs p1cpu"; ls /scratch/jjyeung/envs/p1cpu/bin | grep -i python; /scratch/jjyeung/envs/p1cpu/bin/python -V
echo "== rehearsal_cpu_python_k6"; ls -la $K/rehearsal_cpu_python_k6 | head; file $K/rehearsal_cpu_python_k6 2>/dev/null | head -3
echo "== go k6"; head -60 $K/go_rehearsal_k6.sh
echo "== rk6"; ls $K/rehearsal_k6 | head -60
