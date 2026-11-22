export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
echo "me $(id -u) $(id -un)"; getent passwd 2705094 | cut -d: -f1,3,5
sacct -j 174444 -X -P -o JobID,State,ExitCode,Start,End,Elapsed,NodeList,Reason 2>&1 | head -3
sacct -j 174444 -P -o JobID,JobName%20,State,ExitCode,Start,End 2>&1 | head -12
for f in REVIEW_REFUSED.json ckstop.json; do echo "== $f"; head -c 600 $X/o/174444/live/$f 2>/dev/null; echo; done
python3 - <<'PY' 2>/dev/null
import json,base64
for f in ('REVIEW_REFUSED.json','ckstop.json'):
    try:
        d=json.load(open('/project/community/jjyeung/okh7/x_22c714e1/o/174444/live/'+f))
        p=d.get('payload') if isinstance(d,dict) else None
        print(f, base64.b64decode(p).decode()[:500] if p else d)
    except Exception as e: print(f,'ERR',e)
PY
ls -la $X/o/174444/ | head -20; tail -5 $X/o/174444/j2.log | cut -c1-300; tail -5 $X/o/174444/live/j2.log 2>/dev/null | cut -c1-300
ls -lt ~/.bash_history 2>/dev/null; grep -n "scancel" ~/.bash_history 2>/dev/null | tail -3
