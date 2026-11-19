TZ=UTC squeue -p advanced -h -o '%i %u %j %q %T %M %l %N %b' | head; echo --; TZ=UTC squeue -u jjyeung -h -o '%i %j %P %T %M %R'
sacctmgr -n show qos adv_4gpu_qos format=Name,MaxWall,MaxTRESPU%40,GrpTRES%30 2>&1 | head -3
TZ=UTC sacct -j 173389 -X -n -o JobID,State,Elapsed; ls -la /project/community/jjyeung/okh7/a15_cot_apdd982cd5c4b25/a/c 2>&1 | tail -4
