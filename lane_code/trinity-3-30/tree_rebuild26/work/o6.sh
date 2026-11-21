export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR_20; exit 1; }
[ "$(sha256sum jn6.sh.new | cut -c1-16)" = 0c0e5d3b35cbb580 ] || { echo BAD; exit 1; }
test ! -e a24m4z12/jn6_4ed2704d.sh && mv jn6.sh a24m4z12/jn6_4ed2704d.sh && mv jn6.sh.new jn6.sh && chmod 700 jn6.sh && sha256sum jn6.sh
sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:10:00 --job-name=a15_cot_ape242523a2eb1 $X/jn6.sh
sleep 45; sacct -u $USER -n -X --starttime now-3minutes -o JobID,JobName%24,State,ExitCode,NodeList | tail -2
J=$(sacct -u $USER -n -X --starttime now-3minutes -o JobID,JobName%24 | grep e242523a2eb1 | awk '{print $1}'); echo J=$J
cat $X/o/$J/j2.log; ls -la $X/o/${J}_live; cat $X/o/${J}_live/live.json; grep '^job\|^limit\|^step' $X/o/${J}_live/mem.txt; cat $X/o/${J}_live/alarm.txt 2>&1 | head -3
grep "^job\|^limit\|gate_copy" $X/o/${J}_live/mem.txt $X/o/${J}_live/gate.txt; ls $X/o/${J}_gate 2>&1 | head -2
