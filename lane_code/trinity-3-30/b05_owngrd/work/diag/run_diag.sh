S=/dev/shm/jjyeung/b05; cd $S/lane/code; mkdir -p $S/diag
cat > $S/diag/diag600.py <<'PYEOF'
__DIAG__
PYEOF
uptime; free -g | head -2
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 XDG_CACHE_HOME=$S/cache TORCH_HOME=$S/cache/torch HF_HOME=$S/cache/hf PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
tmux new-session -d -s b05_diag "nice -n 10 $S/envs/allospatial_1111_v1/bin/python $S/diag/diag600.py > $S/diag/diag600.log 2>&1; echo rc=\$? >> $S/diag/diag600.log"
sleep 5; tmux ls | grep b05; ls -la $S/pilot $S/pilot/export
