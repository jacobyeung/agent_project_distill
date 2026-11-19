import base64
p='/scratch/jjyeung/orch_n30/swarm_build/work/prompts/'
e=lambda f: base64.b64encode(open(p+f,'rb').read()).decode()
s=f'''R=/scratch/jjyeung/orch_n30
date -u +%TZ; free -g | sed -n 2p
mkdir -p $R/sb_fullinv/prompts $R/sb_fullinv/out $R/sb_fhalias/prompts $R/sb_fhalias/out $R/sb_ph2chk/work/tmp
echo {e('sb_fullinv.md')} | base64 -d > $R/sb_fullinv/prompts/sb_fullinv.md
echo {e('sb_fhalias.md')} | base64 -d > $R/sb_fhalias/prompts/sb_fhalias.md
printf 'sb_fullinv\\nsb_fhalias\\n' >> $R/sb_queue/queue.txt; cat $R/sb_queue/queue.txt | tr "\\n" " "; echo
cat $R/sb_cursor_probe/AGENTS.md > $R/sb_ph2chk/AGENTS.md
echo {e('sb_ph2chk.md')} | base64 -d > $R/sb_ph2chk/PROMPT.md
cd $R/sb_ph2chk && tmux new-session -d -s sb_ph2chk "TMPDIR=$R/sb_ph2chk/work/tmp OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 timeout 5400 agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh 'Read PROMPT.md in this folder and carry out the task it describes, completely.' > cursor.log 2>&1"
sleep 2; tmux ls -F "#{{session_name}}" | grep "^sb_" | tr "\\n" " "; echo
'''
open('/scratch/jjyeung/orch_n30/swarm_build/work/sh/w58.sh','w').write(s)
