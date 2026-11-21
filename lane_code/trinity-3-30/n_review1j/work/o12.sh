TZ=UTC date +%TZ; nohup srun --overlap --jobid 174134 -N1 -n1 nice -n 15 /usr/bin/python3 -I - > /tmp/rv1j_a.out 2>&1 <<"PY" &
import sys,json,sqlite3,os,collections
N='/tmp/q_22c714e1_174134'; DBG='/tmp/a15_dbg_174134'
import glob
sys.path.insert(0,N+'/p/s'); sys.path.insert(1,N+'/s/np226'); sys.path.extend(glob.glob(N+'/s/c7d31ddd/venvs/rwtrain_torch211_cu129/lib/python3*/site-packages'))
import student_pilot.r1_persisted as rp
_orig=rp.relocated
def reloc(pin):
    try:
        p=str(_orig(pin))
        if os.path.isfile(p): return p
    except Exception: pass
    p=pin['path']; sha=pin['sha256']
    for c in (p.replace('/tmp/q_22c714e1/',N+'/',1), N+'/p/q/u/'+sha, N+'/u/'+sha, p):
        if os.path.isfile(c): return c
    return p
rp.relocated=reloc
from student_pilot.s1_exclusions import Exclusions
from student_pilot.p3_provenance import pinned, load
c=json.load(open(N+'/p/q/c.json'))
rule=Exclusions(c['dev_scene_exclusions'], c['benchmark_scene_exclusions'])
mix=json.load(open(DBG+'/mixc.json'))['entry']
order=load(pinned(mix['order'])); print('order',len(order),flush=True)
for s,scn in ((0,'2'),(1,'3')):
    src=mix['sources'][s]; A={i for x,i in order if x==s}
    sc0=json.load(open(N+f'/p/q/sc/{scn}/0.json')); kept=set(load(pinned(sc0['indices'])))
    sr=sc0['scene_rebuild']; popn=sr['population_count']
    print('src',s,'admitted',len(A),'db',src['database']['sha256'][:8],'census pop',sr['population']['sha256'][:8],popn,'census kept',len(kept),flush=True)
    myL={}; n=0
    with sqlite3.connect('file:'+str(pinned(src['database']))+'?mode=ro',uri=True) as con:
        for i,t in con.execute('SELECT i,row FROM rows ORDER BY i'):
            n+=1; m=rule.matches(json.loads(t))
            if any(m.values()): myL[i]=(m['dev'],m['benchmark'])
    cL=set(range(popn))-kept; L=set(myL)
    M={i for i in A if i in myL}
    def cnt(S): return (sum(myL[i][0] for i in S), sum(myL[i][1] for i in S), len(S))
    print('src',s,'db rows',n,'myL==censusL',L==cL,'|myL|',len(L),'|cL|',len(cL),'myL-cL',len(L-cL),'cL-myL',len(cL-L))
    print('src',s,'M=L&A (a,b,n)',cnt(M),' L-A (a,b,n)',cnt(L-A),' (cL&A)-M',len((cL&A)-M),' cL-M == cL-A',(cL-M)==(cL-A),flush=True)
    print('src',s,'L-A sample',sorted(L-A)[:5])
PY
sleep 30; cat /tmp/rv1j_a.out
