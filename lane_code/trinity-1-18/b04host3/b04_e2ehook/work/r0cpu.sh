#!/bin/bash
H=/scratch/jjyeung/orch_n30/b04host3; L=$H/b04_e2ehook; OV=$H/pyoverlay
export PYTHONPATH=$OV PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp
cd $L && OMP_NUM_THREADS=24 nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -B -m parity_kit.run_parity --settings $L/parity_kit/settings_r0dev_nosam.json --arm own_depth --device cpu --out $L/parity_kit/gpu_results/cpu_r0dev_first --keys $L/work/keys_r0cpu.txt 2>&1 | grep -v -i "warn\|fast path" | tail -20
echo "CPU_RC=${PIPESTATUS[0]}"
