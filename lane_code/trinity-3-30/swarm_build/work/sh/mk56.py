import base64
p = '/scratch/jjyeung/orch_n30/swarm_build/work/prompts/'
b = base64.b64encode(open(p + 'sb_ktchk2.md', 'rb').read()).decode()
s = f'''R=/scratch/jjyeung/orch_n30
echo "@@FILE ph2rev_REVIEW_VERDICT.md"; cat $R/sb_ph2rev/REVIEW_VERDICT.md
echo "@@FILE FIX3_REPORT.md"; cat $R/sb_ktfix2/out/FIX3_REPORT.md; cat $R/sb_ktfix2/out/sb_ktfix3.tar.sha256
echo "@@FILE launch.txt"
mkdir -p $R/sb_ktchk2/work/tmp
cat $R/sb_cursor_probe/AGENTS.md > $R/sb_ktchk2/AGENTS.md
echo {b} | base64 -d > $R/sb_ktchk2/PROMPT.md
cd $R/sb_ktchk2 && tmux new-session -d -s sb_ktchk2 "TMPDIR=$R/sb_ktchk2/work/tmp OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 timeout 5400 agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh 'Read PROMPT.md in this folder and carry out the task it describes, completely.' > cursor.log 2>&1"
sleep 2; tmux ls -F "#{{session_name}}" | grep "^sb_" | tr "\\n" " "; echo
'''
open('/scratch/jjyeung/orch_n30/swarm_build/work/sh/w56.sh', 'w').write(s)
