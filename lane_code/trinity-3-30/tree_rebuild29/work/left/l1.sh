export TZ=UTC; date -u +%TZ
sacct -u jjyeung -X -S 2026-11-21T00:00 -n -P -o JobID,JobName%30,Partition,NodeList,State,Start,End | grep -v "None assigned" | tail -40
squeue -u jjyeung -h -o '%i|%j|%P|%T|%N'
sinfo -p preempt -h -o '%N|%T|%C' | head
