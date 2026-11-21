export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/174134; date -u +%TZ
squeue -j 174134 -h -o "%i %T %M %N"; ls -la --time-style=+%H:%M:%S $O | tail -n +2 | awk '{print $5,$7}' | tr '\n' ' '; echo
head -5 $O/HOLD.txt | cut -c1-200; cat $O/RESULT.json 2>/dev/null; echo
python3 -c "
import json;d=json.load(open('$O/q0.json'))
for k in ('status','refusal','steps','forward'):print(k,'=',str(d.get(k))[:1500])" 2>&1
echo ==== TB; wc -c $O/tb.txt; cat $O/tb.txt | tail -c 7000
