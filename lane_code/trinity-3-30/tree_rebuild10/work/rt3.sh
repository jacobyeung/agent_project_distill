C=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/conf16/pkg; D=$C/work/build16/rt16.py
sed -i "s/kwargs\['metadata'\],{})/kwargs['metadata'],kwargs['replicas'])/g" $D; grep -c "kwargs\['replicas'\])" $D
cd $C && timeout 900 bash work/build16/run.sh work/build16/rt16.py 2>&1 | python3 -c "
import sys,json
t=sys.stdin.read()
try:
  d=json.loads(t[t.index('{'):]);print(json.dumps(d['real'],indent=1));print(json.dumps(d['refuse'],indent=1))
except Exception as e: print(t[-3000:])"
