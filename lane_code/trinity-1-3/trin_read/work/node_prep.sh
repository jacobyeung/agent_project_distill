# runs on the target node after send_node.sh: selfcheck, relay, card reading
cd /scratch/jjyeung/orch_n30/trin_read/build || exit 1
hostname -s; date -u +%FT%TZ; df -h /scratch | tail -1; /usr/bin/bwrap --version; ls /data3/shared/scripts/vnice/vnice.sh
/usr/bin/python3 -B trinity_read.py selfcheck --root ../root --bwrap /usr/bin/bwrap > ../work/selfcheck_$(hostname -s).json 2>/dev/null; echo selfcheck_rc=$?
python3 -c "import json;d=json.load(open('../work/selfcheck_$(hostname -s).json'));print(d['passed'],{k:v.get('passed') for k,v in d['checks'].items()},len(d['checks']['pieces'].get('errors',[])),sum(1 for f in d['portability']['findings'] if f.get('fails')))"
tmux has-session -t trr_yield 2>/dev/null || tmux new-session -d -s trr_yield 'bash /scratch/jjyeung/orch_n30/trin_read/work/n118/relay.sh'
bash ../work/cardpoll/read.sh
