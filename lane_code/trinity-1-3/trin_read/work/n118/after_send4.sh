cd /scratch/jjyeung/orch_n30/trin_read/build || exit 1
hostname -s; date -u +%FT%TZ
/usr/bin/python3 -B trinity_read.py selfcheck --root ../root --bwrap /usr/bin/bwrap > ../work/selfcheck_118_t3.json 2> ../work/selfcheck_118_t3.err; echo selfcheck_rc=$?
python3 -c "import json;d=json.load(open('../work/selfcheck_118_t3.json'));print({k:v for k,v in d.items() if not isinstance(v,(dict,list))})" 2>&1 | cut -c1-600
tail -c 600 ../work/selfcheck_118_t3.err
tmux has-session -t trr_yield 2>/dev/null && echo relay_running || { tmux new-session -d -s trr_yield 'bash /scratch/jjyeung/orch_n30/trin_read/work/n118/relay.sh'; echo relay_started; }
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ' '
