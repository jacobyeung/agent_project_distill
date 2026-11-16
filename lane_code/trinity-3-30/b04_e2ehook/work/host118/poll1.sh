L=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook
tail -5 $L/work/restore.log; tail -3 $L/work/manifest.log; tail -c 1500 $L/work/first.log; tmux has-session -t b04_host 2>/dev/null && echo HOST_RUNNING
ps -o pid,etime,rss,pcpu,cmd -u jjyeung | grep -E "parity_kit" | grep -v grep | cut -c1-160
for e in p1cpu vllm; do /scratch/jjyeung/envs/$e/bin/python -c "import sys,numpy; print('$e', sys.version.split()[0], numpy.__version__)"; done
/scratch/jjyeung/envs/p1cpu/bin/python -c "import scipy,os; print(os.path.dirname(scipy.__file__))"; du -sh /scratch/jjyeung/envs/p1cpu
