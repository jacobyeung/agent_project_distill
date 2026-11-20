O=/project/community/jjyeung/okh7/x_22c714e1/o/173680; cd $O; date -u +%TZ
nice -n 10 python3 -I -s -B - <<'PY'
import gzip,json,random
O='/project/community/jjyeung/okh7/x_22c714e1/o/173680'
d=json.load(gzip.open(O+'/rd0/rdiff.json.gz'))
uf=[]
for e in d['N']:
    if e['P']['key'][3]=='U_Faithful': uf.append(e['P']['i'])
for e in d['P_absent']:
    if e['key'][3]=='U_Faithful': uf.append(e['i'])
uf.sort(); sel=sorted(random.Random(20261121).sample(range(len(uf)),min(20,len(uf)))); want=sorted(uf[j] for j in sel)
ps=json.load(open(O+'/p_sample.json')); got=sorted(r['i'] for r in ps['rows'] if r['class']=='U_Faithful')
print('UF P rows',len(uf),'selection equal',want==got, 'U_Faithful field',d['U_Faithful'])
PY
