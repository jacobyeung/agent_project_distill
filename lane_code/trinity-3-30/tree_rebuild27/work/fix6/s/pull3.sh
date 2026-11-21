export TZ=UTC; date -u +%TZ 1>&2
timeout 80 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134 && tar czf - --ignore-failed-read n2/eva.jsonl log/tr.log log/train.log log/accept.log log/smi_train.log log/c4a.log log/rv2.log log/postc.log n2k/p/rv.json n2/p/q/p/data_receipt.json 2>/dev/null | base64 -w 76; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader 1>&2; pgrep -u $(id -u) -af "u2.py|c4.py|post|rv.py|torch.distributed" 1>&2; true'
squeue -j 174134 -h -o "%i %T %M %N" 1>&2
