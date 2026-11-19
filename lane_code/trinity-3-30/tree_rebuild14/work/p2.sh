W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_n_go; B=$W/w24/work/build24d; date -u +%TZ
python3 -B -c "import json,base64,sys;d=json.load(open('$K/k/j.json'));open('/tmp/tr14_j.sh','wb').write(base64.b64decode(d['payload']))"; wc -l /tmp/tr14_j.sh
grep -n -E "metrics|gsutil|gcloud|export|ckpt|checkpoint|t\.log|trap|torchrun|distributed|save_every|7200|EXPORT|steps|DONE|marker|max_steps|stop" /tmp/tr14_j.sh | cut -c1-260 | head -70
echo "== a.json"; head -c 1500 $K/k/a.json; echo; echo "== p.json"; head -c 1200 $K/k/p.json; echo
echo "== x.py"; cat $K/b/x.py | head -60
echo "== t.py"; head -c 2500 $K/b/t.py; echo; echo "== u.py"; head -c 2000 $K/b/u.py; echo
echo "== GO_TRAIN"; head -c 1500 $B/GO_TRAIN.json; echo; tail -5 $B/go_train_launch.log | cut -c1-300; head -30 $B/go_train.py
