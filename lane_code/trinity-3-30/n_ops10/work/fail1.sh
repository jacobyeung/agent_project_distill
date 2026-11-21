X=/project/community/jjyeung/okh7/x_22c714e1; D=$X/o/174101; echo "FAIL1 $(date -u +%FT%TZ)"
cat $D/RESULT.json; echo; cat $D/r1.json | head -c 600; echo; cat $D/a6.json | head -c 900; echo
python3 - $D/q0.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
def walk(o,p=''):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,p+'/'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o[:50]): walk(v,p+'[%d]'%i)
    else:
        s=str(o)
        if any(w in (p+s).lower() for w in ('error','refus','exception','traceback','reason','status','fail','ok')): print(p, '=', s[:400])
walk(d)
PY
grep -n -iE 'error|refus|exception|traceback|cuda|rlimit|fw\.py|child' $D/q.log | tail -25 | cut -c1-400
tail -5 $D/j2.log | cut -c1-300; tail -5 $D/q.steps | cut -c1-300
ls -la $X/o/174101_live | tail -n +4; df -B1 /project/community | tail -1; cat $X/o/n10_du_0915Z.txt 2>/dev/null | head -5; ls -la $X/o/n10_du_0915Z.txt* 2>&1
