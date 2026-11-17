export TZ=UTC
cd /project/community/jjyeung/b01ec87a6f29b
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00; echo "check rc=$?"
A_N=1 A_T=05:00:00 nice -n 19 bash SUBMIT.cmd --test-only; echo "test rc=$?"
tail -1 LEDGER.jsonl
squeue -u jjyeung -p general -o '%i %j %T' 
