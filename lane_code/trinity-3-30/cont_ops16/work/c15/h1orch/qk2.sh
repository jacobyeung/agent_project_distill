K=/project/community/jjyeung/okh7/x_07ca49df
python3 - <<'P'
import json
d=json.load(open('/project/community/jjyeung/okh7/x_07ca49df/k/staging.json'))
s=json.dumps(d)
import re
for m in set(re.findall(r'"[^"]*eb3429c5[^"]*"',s)): print(m)
P
grep -o '[^" ]*eb3429c5[^" ]*' $K/job.sh $K/b/c.sh 2>/dev/null | sort -u | head
