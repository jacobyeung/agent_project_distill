J=174160; echo "$(TZ=UTC sacct -j $J -X -n -o JobID,Partition,State,Start,End,Elapsed,ExitCode,NodeList | tr -s ' ')"
ls /project/community/jjyeung/a3b73b53d92a7/a | tr '\n' ' '; echo
cat /project/community/jjyeung/a3b73b53d92a7/a/4.txt 2>&1
tail -c 600 /tmp/aa3b73b53d92a71.ex2NCVZS.log; echo
TZ=UTC squeue -u jjyeung -h -o '%i %P %T %M %j %N'
TZ=UTC sacct -u jjyeung -X -n -S 2026-11-21T13:50 -o JobID,JobName%22,Partition,State,Elapsed,ExitCode | tr -s ' '
df -BG --output=avail /project/community | tail -1
