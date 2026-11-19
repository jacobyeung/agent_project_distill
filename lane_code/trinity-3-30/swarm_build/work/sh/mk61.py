import base64
p='/scratch/jjyeung/orch_n30/swarm_build/work/prompts/'
e=lambda f: base64.b64encode(open(p+f,'rb').read()).decode()
s='R=/scratch/jjyeung/orch_n30\nfree -g | sed -n 2p\n'
for w in ['sb_ktchk3','sb_fhrev']:
    s+=f'''mkdir -p $R/{w}/work/tmp; cat $R/sb_cursor_probe/AGENTS.md > $R/{w}/AGENTS.md
echo {e(w+'.md')} | base64 -d > $R/{w}/PROMPT.md
cd $R/{w} && tmux new-session -d -s {w} "TMPDIR=$R/{w}/work/tmp OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 timeout 5400 agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh 'Read PROMPT.md in this folder and carry out the task it describes, completely.' > cursor.log 2>&1"
'''
s+='sleep 2; tmux ls -F "#{session_name}" | grep "^sb_" | tr "\\n" " "; echo\n'
open('/scratch/jjyeung/orch_n30/swarm_build/work/sh/w61.sh','w').write(s)
