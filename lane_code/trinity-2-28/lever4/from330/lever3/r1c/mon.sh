P=/project/community/jjyeung/a38bd627f901e
echo "$(date -u +%T) cpu_log: $(tail -c 300 /tmp/aa38bd627f901e1.7h3336BE.log | tr '\n' ' ')"
for k in 4 8; do J=$(cat $P/a/$k.txt 2>/dev/null); [ -n "$J" ] && { echo "a/$k.txt job=$J $(TZ=UTC sacct -j $J -X -n -o State,Elapsed,ExitCode,NodeList,Start | tr -s ' ')"; TZ=UTC sstat -j $J.batch -n -o AveCPU,MaxRSS,MaxDiskRead 2>/dev/null | tr -s ' ' | head -1; }; done
ls $P/a | tr '\n' ' '; echo; df -BG --output=avail /project/community | tail -1
for f in 25.json CPU.json; do [ -f $P/a/$f ] && { echo "$f $(stat -c %s $P/a/$f)B"; head -c 400 $P/a/$f | strings | head -c 400; echo; }; done
for f in 19 24 21; do echo "-- a/$f $(stat -c %s $P/a/$f)B"; tail -c 400 $P/a/$f | strings | tail -4 | cut -c1-200; done
