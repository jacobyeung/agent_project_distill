f=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173966/173966/logs.tgz
for m in l07.log l09.log l10.log; do echo "=== $m $(tar xzOf $f $m | wc -l) lines"; tar xzOf $f $m | sed -E 's#https://[^ "]*#<URL>#g; s#(upload_?id|session|uri)([^,}]*)#\1<masked>#gI' | grep -a -v '^$' | head -6 | cut -c1-500; done
python3 -c "
import json;d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173966/173966/E3.json'))
c=d.get('checks',d); r=[x for x in (c if isinstance(c,list) else c.items())]
import re
s=json.dumps(d); i=s.find('\"rate'); print(re.sub(r'https://[^\" ]*','<URL>',s[i:i+900]))"
