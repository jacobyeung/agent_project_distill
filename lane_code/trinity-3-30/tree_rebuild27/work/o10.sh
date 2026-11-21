export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/174113; date -u +%TZ
sacct -j 174113 -o JobID%15,State,ExitCode,Elapsed,End,MaxRSS -P | head -5; ls -la $O | tail -n +2 | awk '{print $5,$NF}' | tr '\n' ' '; echo
cat $O/RESULT.json 2>/dev/null; echo
python3 -c "
import json;d=json.load(open('$O/q0.json'))
for k in ('status','refusal','steps','forward','stage'):print(k,'=',str(d.get(k))[:900])
print('keys',list(d)[:30])" 2>&1 | head -20
tail -c 1500 $O/q.log 2>/dev/null; echo; tail -5 $O/q.steps 2>/dev/null | cut -c1-200; tail -4 $O/j2.log | cut -c1-300
