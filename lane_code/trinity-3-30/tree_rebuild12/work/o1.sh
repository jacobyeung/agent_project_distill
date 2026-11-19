export TZ=UTC; date -u +%TZ; P=/project/community/jjyeung
squeue -u $USER -o '%.10i %.12P %.22j %.8T %.10M %.6D %R' 2>&1 | head; 
sinfo -p preempt,general -o '%P %a %l %D %t %G' 2>&1 | head -12
sinfo -p preempt -N -O 'NodeList:20,StateCompact:8,Gres:30,GresUsed:40,CPUsState:16,FreeMem:10' 2>&1 | head -20
ls -la $P/okh7/x_ee227714/o/ 2>&1 | grep -i m400 | head; ls -ld $P/okh7/l_94a76bda $P/okh7/l_3d48eea0 $P/okh7/x_22c714e1 2>&1; ls -ld $P/distill/okit $P/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar 2>&1; df -h $P | tail -1
