set +e
export TZ=UTC
echo "== host"; hostname; date -u
echo "== okit top"; ls -la /home/jjyeung/okit
echo "== links"; readlink -f /home/jjyeung/okit/j /home/jjyeung/okit/r
echo "== df"; df -h /home /project/community 2>&1
echo "== squeue"; squeue -u jjyeung -o "%.10i %.12P %.30j %.8T %.10M %.6D %R" 2>&1
echo "== sacct"; sacct -u jjyeung -S 2026-11-12 -X -o JobID,JobName%30,Partition,State,Start,End,Elapsed,ExitCode -n 2>&1 | tail -80
echo "== sacct 169526 169493"; sacct -j 169526,169493 -X -o JobID,JobName%30,WorkDir%90,State,Elapsed -n -P 2>&1
scontrol show job 169526 2>&1 | head -5
