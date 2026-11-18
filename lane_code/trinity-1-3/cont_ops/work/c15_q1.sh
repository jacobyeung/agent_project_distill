export TZ=UTC
K=/project/community/jjyeung/okh7/x_69d2930d
ls -la $K/runs/673bc60f/inputs/ 2>&1 | head; ls -la $K/runs/673bc60f/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/ 2>&1 | head; ls -la $K/runs/673bc60f/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared 2>&1 | head
ls $K/runs/673bc60f/ 2>&1 | head -20
ls -la $K/o/ | grep 673bc60f | head
squeue -u jjyeung -h -o '%i %j %P %T %r %M %L' 2>&1
