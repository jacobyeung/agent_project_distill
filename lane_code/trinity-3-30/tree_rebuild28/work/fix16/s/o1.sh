export TZ=UTC; date -u +%TZ
squeue -j 174198 -h -o '%T|%M|%N|%L'
timeout 240 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC
X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/174198; Q=/tmp/q_22c714e1_174198
echo "== node $(hostname -s) $(date -u +%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) nproc $(nproc)"; free -g | sed -n 2p; df -h /tmp | tail -1
echo "== O"; ls -la --time-style=+%H:%M:%S $O | cut -c1-150
echo "== HOLD"; cut -c1-700 $O/HOLD.txt
echo "== tb"; tail -c 2400 $O/tb.txt
echo "== Q"; ls -la --time-style=+%H:%M:%S $Q | cut -c1-150; echo "== Q/p"; ls -la --time-style=+%H:%M:%S $Q/p | cut -c1-150; echo "== Q/p/q"; ls -la --time-style=+%H:%M:%S $Q/p/q | cut -c1-150 | head -50
echo "== sel"; ls -la --time-style=+%H:%M:%S $Q/p/q/selection $Q/p/q/selection/pool 2>&1 | cut -c1-150
echo "== sha tree files"; (cd $Q/p/s && sha256sum launch_r1/entry.py launch_r1/production_proof.py student_pilot/s1_routing.py student_pilot/p3_provenance.py student_pilot/s1_pool_relocate.py student_pilot/orchard_paths.py student_pilot/s1_admission.py)
echo "== entry 277-288"; sed -n 277,288p $Q/p/s/launch_r1/entry.py
echo "== 174134 O"; ls -la --time-style=+%H:%M:%S $X/o/174134 2>&1 | cut -c1-150 | head -40
echo "== q.log head/tail"; head -c 600 $Q/q.log; echo; echo ...; tail -c 900 $Q/q.log; echo
echo "== q0"; head -c 700 $O/q0.json; echo
/usr/bin/python3 -B -I - <<'PY'
import json,hashlib,os,sys,sqlite3,base64,time
X='/project/community/jjyeung/okh7/x_22c714e1'; Q='/tmp/q_22c714e1_174198'
NJ='/tmp/jjyeung/q_22c714e1'; NS='/tmp/q_22c714e1'
def enc(v): return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def dg(v): return hashlib.sha256(enc(v).encode()).hexdigest()
def load(p):
    v=json.load(open(p))
    if isinstance(v,dict) and v.get('encoding')=='base64-json': v=json.loads(base64.b64decode(v['payload']))
    return v
def leaves(v,pre=''):
    if isinstance(v,dict):
        for k in sorted(v): yield from leaves(v[k],pre+'/'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): yield from leaves(x,pre+'/'+str(i))
    else: yield pre,v
def respell(v,a,b):
    if isinstance(v,dict): return {respell(k,a,b):respell(x,a,b) for k,x in v.items()}
    if isinstance(v,list): return [respell(x,a,b) for x in v]
    if isinstance(v,str): return v.replace(a,b)
    return v
def cnt(v,s): return sum(1 for _,x in leaves(v) if isinstance(x,str) and s in x)
def here(p): return Q+p[len(NJ):] if p.startswith(NJ+'/') else Q+p[len(NS):] if p.startswith(NS+'/') else p
def sh(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    return h.hexdigest()
print('== PY')
plan=load(Q+'/p/plan.json'); rq=plan['request']
print('request keys',sorted(rq))
for k in ('job_tmp','frame_roots','routing_selection','config','routing_base','staging','room_audit'): print(' ',k,json.dumps(rq.get(k))[:300])
print('plan NJ strings',cnt(plan,NJ),'NS strings',cnt(plan,NS+'/'))
sp=here(rq['routing_selection']['path']); sel=load(sp)
print('reviewed selection file',sp,'sha256',sh(sp),'keys',sorted(sel))
for k in ('regenerated_sha256','rows','row_id_digest','row_bytes_sha256','regenerated_receipt','logical_output'): print(' ',k,json.dumps(sel.get(k)))
ip=sel.get('inputs_pinned',{})
print('  inputs_pinned keys',sorted(ip)); 
for k in ('config_sha256','routing_base','division','base_model','routing_database'): print('   ',k,json.dumps(ip.get(k))[:260])
print('  inputs_pinned.s1_routing',json.dumps(ip.get('s1_routing'))[:700])
print('  reviewed selection NS strings',cnt(sel,NS+'/'),'NJ strings',cnt(sel,NJ))
O=X+'/o/174198'
for name in ('a0r.json','a0m.json'):
    p=O+'/'+name
    if not os.path.exists(p): print(name,'absent'); continue
    v=load(p); print('==',name,'bytes',os.path.getsize(p),'sha256',sh(p),'digest',dg(v),'keys',sorted(v)[:40])
    print('   NJ strings',cnt(v,NJ),'NS strings',cnt(v,NS+'/'))
    if name=='a0r.json':
        new=v
        print('   digest(new)==expected',dg(v)==sel['regenerated_sha256'],'digest(respell NJ->NS)',dg(respell(v,NJ,NS)),'== expected',dg(respell(v,NJ,NS))==sel['regenerated_sha256'])
        print('   database',json.dumps(v.get('database')),'materialization',json.dumps(v.get('materialization')))
        print('   count',v.get('count'),'scenes',v.get('scenes'))
    old=X+'/o/174134/'+name
    if os.path.exists(old):
        o=load(old); print('   174134',name,'sha256',sh(old),'digest',dg(o),'NJ',cnt(o,NJ),'NS',cnt(o,NS+'/'))
        if name=='a0r.json': print('   digest(174134)==expected',dg(o)==sel['regenerated_sha256'],'database',json.dumps(o.get('database')),'materialization',json.dumps(o.get('materialization')))
        a=dict(leaves(o)); b=dict(leaves(v)); br=dict(leaves(respell(v,NJ,NS)))
        d1=[k for k in sorted(set(a)|set(b)) if a.get(k,'<absent>')!=b.get(k,'<absent>')]
        d2=[k for k in sorted(set(a)|set(br)) if a.get(k,'<absent>')!=br.get(k,'<absent>')]
        print('   leaves old',len(a),'new',len(b),'differing',len(d1),'differing after respell NJ->NS',len(d2))
        for k in d1[:6]: print('    D1',k,'|',str(a.get(k,'<absent>'))[:110],'|',str(b.get(k,'<absent>'))[:120])
        for k in d2[:25]: print('    D2',k,'|',str(a.get(k,'<absent>'))[:110],'|',str(br.get(k,'<absent>'))[:120])
    else: print('   no 174134 copy at',old)
# rows of the refused job's regenerated selection, read-only and immutable
db=Q+'/p/q/selection/rows.sqlite'
if os.path.exists(db):
    t=time.time(); n=0; ids=hashlib.sha256(); full=hashlib.sha256(); full2=hashlib.sha256(); nj=0; first=None
    c=sqlite3.connect('file:'+db+'?mode=ro&immutable=1',uri=True)
    for i,row,target in c.execute('SELECT i,row,target FROM rows ORDER BY i'):
        v=json.loads(row)
        ids.update((json.dumps([i,v.get('qid',v.get('id'))],separators=(',',':'))+'\n').encode())
        full.update((json.dumps([i,row,target],separators=(',',':'))+'\n').encode())
        r2=row.replace(NJ,NS); k=row.count(NJ); nj+=k
        full2.update((json.dumps([i,r2,target],separators=(',',':'))+'\n').encode()); n+=1
        if first is None and k: first=(i,[(p,x) for p,x in leaves(v) if isinstance(x,str) and NJ in x])
    c.close()
    print('== rows.sqlite of 174198 sha256',sh(db),'rows',n,'seconds',round(time.time()-t,1))
    print('   row_id_digest',ids.hexdigest(),'== reviewed',ids.hexdigest()==sel.get('row_id_digest'))
    print('   row_bytes_sha256',full.hexdigest(),'== reviewed',full.hexdigest()==sel.get('row_bytes_sha256'))
    print('   row_bytes_sha256 after respell NJ->NS',full2.hexdigest(),'== reviewed',full2.hexdigest()==sel.get('row_bytes_sha256'))
    print('   NJ occurrences in rows',nj,'first row with NJ',first[0] if first else None)
    if first:
        for p,x in first[1][:8]: print('     ',p,'|',x[:150])
PY
EOS
date -u +%TZ
