set -euo pipefail; W=/scratch/jjyeung/orch_n30/lever1_c/nogt
[[ "$(hostname -s)" == trinity-2-28 ]]
cd $W; cp out/ARKIT_MISSING_REFERENCE_INPUTS.txt ark_ref_list.txt; wc -l ark_ref_list.txt
for f in $(cat ark_ref_list.txt); do [ -e raw/$f ] && echo "EXISTS raw/$f" || true; done | head -3 || true
setsid nohup bash -c "bash -c 'kill -STOP \$\$; tar cf - -C / -T $W/ark_ref_list.txt; exit \$?' | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 | tee >(sha256sum > $W/ARK_REF_STREAM_src.sha) | (cd $W/raw && tar xf -); echo PIPE_RC \${PIPESTATUS[*]}; date -u +%FT%TZ" > $W/ark_ref_stage.log 2>&1 < /dev/null &
OUTER=$!
sleep 3
ROOT=""; RL=""
for p in $(pgrep -g $(ps -o pgid= -p $OUTER | tr -d ' ')); do
  c=$(cat /proc/$p/comm 2>/dev/null || true); s=$(awk '{print $3}' /proc/$p/stat 2>/dev/null || true)
  [[ "$c" == ratelimit ]] && RL=$p
  [[ "$c" == bash && "$s" == T ]] && ROOT=$p
done
echo "outer=$OUTER root=$ROOT rl=$RL"
[[ -n "$ROOT" && -n "$RL" ]]
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane lever2_ark_ref --pid $ROOT --member-pid $RL --rl-pid $RL \
  --expected-bytes 10000000 --tier 3 --kind copy --nominal-mbps 4 --allow-resume --priority 950
cat /scratch/jjyeung/orch_n30/lever1_c/arch5/arch_run.log
