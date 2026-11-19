import re,html,sys
s=open(sys.argv[1]).read()
t=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S)
t=re.sub(r'<[^>]+>','\n',t); t=html.unescape(t)
L=[l.strip() for l in t.split('\n') if l.strip()]
i=L.index('Quick Access')+1
nodes=[]
while L[i].startswith('trinity-'): i+=1
cur=None
while i<len(L):
    l=L[i]
    if re.fullmatch(r'trinity-\d+-\d+',l) and i+1<len(L) and L[i+1].startswith('Updated'):
        cur={'n':l,'upd':L[i+1][11:],'gpus':[]}; nodes.append(cur); i+=2; continue
    if cur and l=='Jobs':
        i+=1
        while i+2<len(L) and re.fullmatch(r'\d+',L[i]) and 'NVIDIA' in L[i+1] or (i+2<len(L) and re.fullmatch(r'\d+',L[i]) and ('GeForce' in L[i+1] or 'RTX' in L[i+1] or 'A100' in L[i+1] or 'Tesla' in L[i+1])):
            g={'id':L[i],'name':L[i+1],'avail':L[i+2],'jobs':[]}; i+=3
            while i<len(L) and '·' in L[i]: g['jobs'].append(L[i]); i+=1
            cur['gpus'].append(g)
        continue
    i+=1
for n in nodes:
    free=[f"{g['id']}:{g['avail']}" for g in n['gpus'] if not g['jobs']]
    names=sorted(set(g['name'].replace('NVIDIA ','') for g in n['gpus']))
    print(n['n'], n['upd'], len(n['gpus']), names, 'FREE', free, 'jj', sum(1 for g in n['gpus'] for j in g['jobs'] if 'jjyeung' in j))
