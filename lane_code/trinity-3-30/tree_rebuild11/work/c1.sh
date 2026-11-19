W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; L=$W/w19; date -u +%TZ; tmux ls | grep -E "tr10|tr11"
cat $L/work/build19/DELIVERY.json | head -c 1500; echo
ls $L/work/build19 | head -60
sed -n 1,40p $L/work/build19/run.sh 2>/dev/null | cut -c1-200
grep -n "final_focused" $L/work/build19/*.py $L/work/build19/*.sh $L/work/build19/*.json 2>/dev/null | head -10 | cut -c1-300
python3 -c "import json;d=json.load(open('$L/work/build19/proofs/final_focused/TESTS.json'));print(list(d.keys())[:20]); print({k:d[k] for k in d if k in ('command','modules','argv','cmd')})" 2>&1 | cut -c1-1500
