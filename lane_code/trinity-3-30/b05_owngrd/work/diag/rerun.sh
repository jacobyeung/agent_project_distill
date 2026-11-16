S=/dev/shm/jjyeung/b05
tmux new-session -d -s b05_diag "cd $S/lane/code && env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 XDG_CACHE_HOME=$S/cache TORCH_HOME=$S/cache/torch HF_HOME=$S/cache/hf PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=$S/lane/code nice -n 10 $S/envs/allospatial_1111_v1/bin/python $S/diag/diag600.py > $S/diag/diag600.log 2>&1; echo rc=\$? >> $S/diag/diag600.log"
sleep 100; tmux ls | grep b05; grep -v -i "warn\|pynvml" $S/diag/diag600.log | tail -20 | cut -c1-300
