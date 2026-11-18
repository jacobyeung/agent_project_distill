export TZ=UTC
cd /project/community/jjyeung/b01ec87a6f29b
Q=$(squeue -u jjyeung -p general -h -o '%i %j %T'); echo "general-ours: [$Q]"; [ -n "$Q" ] && { echo "REFUSE: job of ours on general"; exit 1; }
sha256sum 0.tgz PACKAGE.json a/1.json
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00 > /dev/null; echo "check rc=$?"
A_N=1 A_T=05:00:00 bash SUBMIT.cmd; echo "submit rc=$?"
tail -1 LEDGER.jsonl | cut -c1-400
squeue -u jjyeung -p general -o '%i %j %T %M %l %b %r'
