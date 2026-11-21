X=/project/community/jjyeung/okh7/x_22c714e1; D=$X/o/174113; echo "REF2 $(date -u +%FT%TZ)"
cat $D/RESULT.json; echo
python3 - $D/q0.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
print("top keys:", list(d)[:40])
for k in ("status","refusal","reason","reasons","error","stage","code","detail","traceback"):
    if k in d: print(k,"=",str(d[k])[:1500])
PY
grep -n -iE 'error|refus|exception|traceback|Errno|denied|No space' $D/q.log | tail -15 | cut -c1-500
tail -c 2500 $D/q.log | tail -8 | cut -c1-400
df -B1 /project/community | tail -1
