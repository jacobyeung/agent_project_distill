export TZ=UTC; date -u +%T
squeue -h -j 173049 -o '%i %j %T %M %R %N %S' 2>&1
sacct -n -j 173049 -X -o JobID,State,ExitCode,Elapsed,NodeList,MaxRSS 2>&1 | head -3
O=/project/community/jjyeung/okh7/pb_61e5cf9d; ls -la $O 2>&1 | tail -6
[[ -f $O/pb_report.json ]] && cat $O/pb_report.json
[[ -f $O/pb.log ]] && tail -5 $O/pb.log
squeue -h -j 173049 -t R | grep -q . && timeout 60 srun --overlap --jobid 173049 -n1 -N1 timeout 40 bash -c 'cat /tmp/jjyeung/pb_173049/pb.log; ls -la /tmp/jjyeung/pb_173049 | tail -12; df -BG /tmp | tail -1; free -g | sed -n 2p' 2>&1 | grep -v cgroup | tail -25
