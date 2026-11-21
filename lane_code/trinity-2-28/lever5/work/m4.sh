P=/project/community/jjyeung/a3b73b53d92a7/a
/usr/bin/python3 -I -s -B - <<'PY'
import json
d=json.loads(bytes.fromhex(json.load(open('/project/community/jjyeung/a3b73b53d92a7/a/c/CPU.json'))['a0']))
print(sorted(d.keys()))
for k,v in d.items():
    if isinstance(v,dict): print(k, {kk:vv for kk,vv in v.items() if kk in ('passed','job','seconds','finite','error','returncode','child_returncode')})
    else: print(k, str(v)[:200])
PY
TZ=UTC squeue -u jjyeung -p general -h
