exec 3>&1 1>&2
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/orchard_tower2x && ls -la && cat REPORT_K2.md >&3
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv
ls /scratch/jjyeung/envs
