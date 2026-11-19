W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W
C=$W/work/conf16/pkg; D=$C/work/build16/rt16.py
python3 - "$D" <<'PY'
import sys
s=open(sys.argv[1]).read()
old="kwargs={'metadata':[file_pin(prep)],'replicas':{file_pin(parent)['sha256']:str(parent)}}"
assert old in s
new=old+"\nimport glob\nfor f in glob.glob('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_runtime/okh7/**/*.json',recursive=True):kwargs['replicas'][file_pin(Path(f))['sha256']]=f"
s=s.replace(old,new)
open(sys.argv[1],'w').write(s)
PY
cd $C && timeout 900 bash work/build16/run.sh work/build16/rt16.py 2>&1 | python3 -c "
import sys,json
t=sys.stdin.read()
try:
  d=json.loads(t[t.index('{'):]);print(json.dumps(d['real'],indent=1));print(json.dumps(d['refuse'],indent=1))
except Exception as e: print(t[-3000:])"
