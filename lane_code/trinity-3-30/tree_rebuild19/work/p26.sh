C=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/census24; cat $C/CANARY.md; echo ====; head -30 $C/CENSUS.md | cut -c1-400; python3 -c "
import json,collections
d=json.load(open('$C/CENSUS.json')); rows=d['rows'] if isinstance(d,dict) and 'rows' in d else d
print(type(d).__name__, len(rows)); 
k=[x for x in rows[0]] if rows else []; print(k)
c=collections.Counter((r.get('mark'),r.get('verdict')) for r in rows); print(c.most_common())
"
