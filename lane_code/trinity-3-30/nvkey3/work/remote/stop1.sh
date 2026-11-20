K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
echo "user stop order 0552Z (nvkey3 $(date -u +%FT%TZ))" > ctl/STOP; tmux kill-session -t nvk3_chain && echo killed_nvk3_chain
for f in 60_v6bA_first30 61_v6bN_first30 62_v6bI_first30; do [ -f queue/$f.jsonl ] && mv queue/$f.jsonl queue_done/$f.stopped_by_user.jsonl; done
ls queue/ queue_done/ | tr '\n' ' '; echo; date -u +%T; cat meter/METER.json; echo; tail -3 runner.log
