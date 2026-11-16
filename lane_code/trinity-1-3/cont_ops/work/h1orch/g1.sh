export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
pgrep -f 't_c94bbc4e.sh' && { echo "o.sh still running"; exit 3; }
test -f $B/staging.json && grep -q PASS $B/staging.json || { echo "staging not PASS"; cat $B/staging.json; exit 3; }
test -e $B/gate.json && { echo "gate.json exists"; exit 3; }
cd $B && PY_GATE=/project/community/jjyeung/latency/envs/fit/bin/python3 BW_GATE=/project/community/jjyeung/cp4tk_rt/kit/bwrap nohup setsid nice -n 19 ionice -c3 bash $B/g.sh > $O/t_c94bbc4e.g.log 2>&1 < /dev/null &
echo started gate pid $!
