D=/project/community/jjyeung/okh7/x_22c714e1/t_fa5d00a8e996
python3 -c "
import json
n=0
for l in open('$D/r.txt'):
    l=l.strip()
    if l.startswith('{\"case\": \"job\"'):
        d=json.loads(l); d.pop('marks',None); print(json.dumps(d)[:700]); n+=1
        if n==2: break
"
