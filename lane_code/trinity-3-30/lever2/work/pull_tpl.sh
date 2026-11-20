set -euo pipefail; [[ "$(hostname -s)" == trinity-2-28 ]]
R=/scratch/jjyeung/orch_n30/lever1_c/r1/returned; mkdir -p $R; cd $R; test ! -e 0.gz
URI=__URI__; GEN=__GEN__; SHA=__SHA__; BYTES=__BYTES__
setsid nohup bash -c "bash -c 'kill -STOP \$\$; /home/jjyeung/google-cloud-sdk/bin/gcloud storage cat \"$URI#$GEN\"; exit \$?' | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 | (set -C; cat > $R/0.gz); echo PIPE_RC \${PIPESTATUS[*]}; date -u +%FT%TZ; stat -c %s $R/0.gz; echo '$SHA  0.gz' | (cd $R && sha256sum -c -)" > $R/pull.log 2>&1 < /dev/null &
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
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane lever2_r1_depth --pid $ROOT --member-pid $RL --rl-pid $RL \
  --expected-bytes $BYTES --tier 3 --kind copy --nominal-mbps 8 --io-weight 1 --allow-resume --priority 900
