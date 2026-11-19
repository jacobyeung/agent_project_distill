TZ=UTC sacct -j 173389 -X -n -o JobID,State,Elapsed; ls -la /project/community/jjyeung/okh7/a15_cot_apdd982cd5c4b25/a/c 2>&1 | tail -5; TZ=UTC squeue -p general -h -o '%i %u %T %M %l %R' | head -8
