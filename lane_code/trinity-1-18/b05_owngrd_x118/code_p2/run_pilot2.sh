cd /dev/shm/jjyeung/b05/code_p2/code
export CUDA_VISIBLE_DEVICES=2 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 XDG_CACHE_HOME=/dev/shm/jjyeung/b05/cache TORCH_HOME=/dev/shm/jjyeung/b05/cache/torch TRITON_CACHE_DIR=/dev/shm/jjyeung/b05/cache/triton HF_HOME=/dev/shm/jjyeung/b05/cache/hf PYTHONDONTWRITEBYTECODE=1
/dev/shm/jjyeung/b05/envs/allospatial_1111_v1/bin/python -m owngrd.train --manifest /scratch/jjyeung/orch_n30/b05_owngrd/work/manifests/TRAIN_K1_113.json --labels /scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1 --teacher-root /scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full/teacher_k1 --out /dev/shm/jjyeung/b05/pilot2 --device cuda --hours 4 --accelerator-hour-cap 4 --steps 10000 --validate-every 200 --checkpoint-every 200 --val-items 192 --accumulate 8
echo rc=$?
