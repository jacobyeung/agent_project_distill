O=/project/community/jjyeung/okh7/x_22c714e1/o/173661; U=/project/community/jjyeung/okh7/x_22c714e1/u
cd $O || exit 1; date -u +%TZ; ls -la . rd0 live | grep -v '^total'
for f in routing_selection.json db_bytes.json rd0/rdiff_summary.json rdiff.log dbb.log a6.json r1.json; do [ -f $f ] && echo "@@@ $f $(sha256sum < $f | cut -c1-64) $(stat -c %s $f)"; done
sha256sum rd0/rdiff.json.gz rdiff.py
echo "@@@ rdiff.log"; tail -c 3000 rdiff.log; echo; echo "@@@ dbb.log"; cat dbb.log; echo "@@@ db_bytes"; head -c 4000 db_bytes.json; echo
echo "@@@ r.log reconstruction lines"; grep -n -i "reconstruct\|R1_RECON\|4e8e6c04\|import\|P_TRAINED\|child\|selection_differs" r.log | cut -c1-300 | tail -30
nice -n 10 python3 -I -s -B - <<'PY'
import gzip,json,hashlib,random,sqlite3,struct,os,collections
O='/project/community/jjyeung/okh7/x_22c714e1/o/173661'; U='/project/community/jjyeung/okh7/x_22c714e1/u'
s=json.load(open(O+'/rd0/rdiff_summary.json'))
print('SUMMARY',json.dumps({k:v for k,v in s.items() if k not in ('removal_files','P_schema','N_schema')}))
rf=s['removal_files']; pins=[r['sha256'] for r in rf]; print('REMOVAL_ORDER',[p[:8] for p in pins], [r.get('defects') for r in rf])
d=json.load(gzip.open(O+'/rd0/rdiff.json.gz'))
N=d['N']; A=d['P_absent']
c=collections.Counter()
keys=set()
for e in N:
    kt=json.dumps(e['key']); assert kt not in keys; keys.add(kt)
    p=e['P']; ident = p is not None and p['content_sha256']==e['content_sha256'] and p['key']==e['key']
    assert ident==e['identical'],e
    c['N']+=1; c['N_ident']+=ident; c['N_mismatch']+= not ident; c['N_noP']+= p is None; c['N_listed']+=bool(e['removal_list_sha256s'])
    if p is not None and p['i']!=e['i']: c['N_i_differs']+=1
    if e['key'][3]=='U_Faithful': c['UF_N']+=1
for e in A:
    kt=json.dumps(e['key']); assert kt not in keys; keys.add(kt)
    c['A']+=1; L=e['removal_list_sha256s']; c['A_listed']+=bool(L); c['A_unlisted']+= not L
    assert (e['removal_list_sha256']==L[0]) if L else e['removal_list_sha256']=='none'
    for h in L: c['A_list_not_pinned']+= h not in pins
    if e['key'][3]=='U_Faithful': c['UF_A']+=1; c['UF_A_unlisted']+= not L
    for h in L[:1]: c['A_first_'+h[:8]]+=1
print('RECOUNT',dict(c)); print('UF',d['U_Faithful'])
print('A_sources',collections.Counter(e['key'][3] for e in A).most_common(20))
print('N_sources',collections.Counter(e['key'][3] for e in N).most_common(30))
rng=random.Random(20261120)
matched=[e for e in N if e['identical'] and e['key'][3]!='U_Faithful']; uf=[e for e in N if e['key'][3]=='U_Faithful']
sm=rng.sample(matched,min(20,len(matched))); su=rng.sample(uf,min(20,len(uf))); sa=rng.sample(A,min(20,len(A)))
json.dump(dict(matched=[e['P']['i'] for e in sm],U_Faithful=[e['P']['i'] for e in su if e['P']],P_absent=[e['i'] for e in sa]),open('/dev/stdout','w')); print()
nsha=s['inputs']['N']['sha256']; ndb=U+'/'+nsha; print('NDB',ndb,os.path.exists(ndb))
def packed(values):
    out=bytearray(b'rdiff-v1\x00')
    for v in values:
        if v is None: t,b=b'n',b''
        elif type(v) is int: t,b=b'i',str(v).encode()
        elif type(v) is float: t,b=b'f',struct.pack('>d',v)
        elif type(v) is str: t,b=b't',v.encode()
        else: t,b=b'b',v
        out.extend(t+struct.pack('>Q',len(b))+b)
    return out
if os.path.exists(ndb):
    db=sqlite3.connect('file:'+ndb+'?mode=ro',uri=True)
    print('schema',db.execute("select type,name,sql from sqlite_master").fetchall()[:8])
    first=None; tc=collections.Counter(); tot=0
    for i,row,target in db.execute('SELECT i,row,target FROM rows ORDER BY i'):
        r=json.loads(row); tot+=1
        if first is None: first=r; print('ROWKEYS',sorted(r)[:40])
        tc[(r.get('question_type') or r.get('type') or r.get('task'), (r.get('s1_source') or {}).get('name') is not None)]+=1
    print('NDB rows',tot,'types',tc.most_common(30))
    for label,sample in (('matched',sm),('U_Faithful',su)):
        ok=0
        for e in sample:
            v=db.execute('SELECT i,row,target FROM rows WHERE i=?',(e['i'],)).fetchone()
            r=json.loads(v[1]); k=[r.get('dataset'),r.get('scene'),r['qid'],(r.get('s1_source') or {}).get('name')]
            h=hashlib.sha256(packed(v)).hexdigest()
            good = k==e['key'] and h==e['content_sha256'] and e['P'] and h==e['P']['content_sha256']
            ok+=bool(good)
            if not good: print('SPOT_FAIL',label,e['i'],k,e['key'],h[:12],e['content_sha256'][:12])
        print('SPOT',label,ok,'/',len(sample))
lists={}
for r in rf:
    p=U+'/'+r['sha256']
    lists[r['sha256']]=open(p,'rb').read() if os.path.exists(p) else None
print('LISTS_PRESENT',{h[:8]:(v is not None and hashlib.sha256(v).hexdigest()==h) for h,v in lists.items()})
ok=0
for e in sa:
    h=e['removal_list_sha256']; raw=lists.get(h)
    hits=[k for k in e['removal_keys'] if raw is not None and all((str(x).encode() in raw) for x in (k if isinstance(k,list) else [k]) if x not in (None,''))]
    ok+=bool(hits)
    print('ABSENT',e['key'],h[:8],'keys',json.dumps(e['removal_keys'])[:200],'hit',bool(hits))
print('SPOT P_absent list-bytes hits',ok,'/',len(sa))
PY
