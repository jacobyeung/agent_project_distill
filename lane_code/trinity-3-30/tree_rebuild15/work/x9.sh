R=/scratch/jjyeung/orch_n30/tr15_rev24l3; date -u +%TZ; cd $R && tmux new-session -d -s tr15_rev24l3 "OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 timeout 5400 agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh 'Read PROMPT.md in this folder and carry out the task it describes, completely.' > cursor.log 2>&1"
sleep 10; tmux ls | grep tr15; ls -la $R
