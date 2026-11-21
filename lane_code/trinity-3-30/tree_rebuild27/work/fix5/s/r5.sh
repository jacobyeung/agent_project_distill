W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w27fix/n_go
echo "=== rv.py 36-66 239-330"; sed -n 36,66p $K/b/rv.py; sed -n 239,330p $K/b/rv.py
echo "=== pl.py 355-380"; sed -n 355,380p $K/b/pl.py
echo "=== ep.py 1-70"; sed -n 1,70p $K/b/ep.py
echo "=== o.py"; cat $K/b/o.py
echo "=== kit json"; python3 -I -c 'import json,sys;v=json.load(open(sys.argv[1]));print(v.get("namespace"),v.get("n_root"))' $K/k/p.json
python3 -I -c 'import json,base64,sys;v=json.load(open(sys.argv[1]));r=json.loads(base64.b64decode(v["payload"]));print({k:r[k] for k in r if k!="source"})' $K/k/a.json
echo "=== w26t5 x"; ls $W/w26t5/work/x $W/w26t5/work/x/a2 2>&1; du -sh $W/w26t5/work/x/a2/n $K; head -3 $W/w26t5/work/x/a2/n/SHA256SUMS.txt
ls /scratch/jjyeung/envs/p1cpu/bin/python; tmux ls 2>&1 | head; nproc; free -g | head -2
