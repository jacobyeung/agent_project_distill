O=/project/community/jjyeung/okh7/x_22c714e1/o/173680; cd $O || exit 1; date -u +%TZ; sha256sum /project/community/jjyeung/okh7/x_22c714e1/rdiff.py
nice -n 10 python3 -I -s -B - <<'PY'
import gzip,json,hashlib,random,struct,collections
O='/project/community/jjyeung/okh7/x_22c714e1/o/173680'
s=json.load(open(O+'/rd0/rdiff_summary.json')); pins=[r['sha256'] for r in s['removal_files']]
d=json.load(gzip.open(O+'/rd0/rdiff.json.gz')); print('TOPKEYS',list(d))
N=d['N']; A=d['P_absent']; print('N0',json.dumps(N[0])[:600]); print('A0',json.dumps(A[0])[:600])
c=collections.Counter(); di=collections.Counter(); keys=set()
for e in N:
    kt=json.dumps(e['key']); assert kt not in keys; keys.add(kt)
    p=e['P']; ident = p is not None and p['content_sha256']==e['content_sha256'] and p['key']==e['key']
    c['N']+=1; c['N_ident']+=ident; c['N_noP']+= p is None; c['N_listed']+=bool(e['removal_list_sha256s'])
    if p: di[e['i']-p['i']]+=1
for e in A:
    kt=json.dumps(e['key']); assert kt not in keys; keys.add(kt)
    L=e['removal_list_sha256s']; c['A']+=1; c['A_listed']+=bool(L); c['A_unlisted']+= not L
    for h in L: c['A_list_not_pinned']+= h not in pins
print('RECOUNT',dict(c)); print('i_offset N.i-P.i top',di.most_common(8), 'distinct',len(di))
print('A_sources',collections.Counter(e['key'][3] for e in A).most_common(20))
print('A_listed_by',collections.Counter((e['removal_list_sha256s'] or ['none'])[0][:8] for e in A).most_common())
print('N_sources',collections.Counter(e['key'][3] for e in N).most_common(30))
print('A_datasets',collections.Counter(e['key'][0] for e in A).most_common(10))
ps=json.load(open(O+'/p_sample.json')); print('PS keys',[k for k in ps if k!='rows'],{k:ps[k] for k in ps if k!='rows'})
print('PS classes',collections.Counter(r['class'] for r in ps['rows']))
def packed(values):
    out=bytearray(b'rdiff-v1\x00')
    for v in values:
        if v is None: t,b=b'n',b''
        elif type(v) is int: t,b=b'i',str(v).encode()
        elif type(v) is float: t,b=b'f',struct.pack('>d',v)
        elif type(v) is str: t,b=b't',v.encode()
        else: t,b=b'b',v
        out.extend(t+struct.pack('>Q',len(b))+b)
    return bytes(out)
# rederive
uni=sorted(random.Random(20261120).sample(range(47898),60))
req=json.load(open('/project/community/jjyeung/okh7/x_22c714e1/rcj/P_SAMPLE_I.json')); print('uniform equal request',uni==req['uniform_positions'])
Pmap={}
for e in N:
    if e['P']: Pmap[e['P']['i']]=('N',e)
for e in A: Pmap[e['i']]=('A',e)
print('P i covered',len(Pmap))
Ai=[e['i'] for e in A]; selA=sorted(random.Random(20261122).sample(range(len(A)),min(20,len(A)))); wantA=sorted(A[j]['i'] for j in selA)
ok=collections.Counter(); keyof=lambda r:[r.get('dataset'),r.get('scene'),r.get('qid'),(r.get('s1_source') or {}).get('name')]
rows=ps['rows']; got=collections.defaultdict(list)
for r in rows: got[r['class']].append(r)
print('positions uniform got',[r['position'] for r in got.get('uniform',[])][:5], 'len',len(got.get('uniform',[])))
for r in rows:
    h=hashlib.sha256(packed((r['i'],r['row'],r['target']))).hexdigest()
    k=keyof(json.loads(r['row'])); src,e=Pmap.get(r['i'],(None,None))
    if e is None: ok[r['class']+'_noentry']+=1; continue
    ph = e['P']['content_sha256'] if src=='N' else e['content_sha256']; pk = e['P']['key'] if src=='N' else e['key']
    ok[r['class']+'_hash_eq']+= h==ph; ok[r['class']+'_key_eq']+= k==pk; ok[r['class']+'_'+src]+=1
    if src=='N': ok[r['class']+'_N_identical']+= e['content_sha256']==h
print('PS_CHECK',dict(ok))
print('P_absent selection equal',sorted(r['i'] for r in got.get('P_absent',[]))==wantA, wantA[:5])
PY
