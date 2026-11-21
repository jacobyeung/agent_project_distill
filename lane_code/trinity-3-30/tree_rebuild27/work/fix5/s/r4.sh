W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w27fix/n_go
python3 -I -c 'import json,base64,sys;v=json.load(open(sys.argv[1]));sys.stdout.write(base64.b64decode(v["payload"]).decode())' $K/k/j.json
