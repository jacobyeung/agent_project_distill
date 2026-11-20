import json,sys,base64,hashlib
txt=open(sys.argv[1]).read().split('@@@ ')[1:]
F={}
for blk in txt:
    head,body=blk.split('\n',1); name,size,sha=head.split()
    b=base64.b64decode(body.strip().split('\n')[0]); assert hashlib.sha256(b).hexdigest()==sha
    F[name]=b; open('/scratch/jjyeung/orch_n30/n_review1c/evidence/A_'+name,'wb').write(b)
    print(name,size,sha)
P=json.load(open('/scratch/jjyeung/orch_n30/n_review1/evidence/routing_receipt_ca0616db.json'))
PM=json.load(open('/scratch/jjyeung/orch_n30/n_review1b/evidence/P_routing_materialization_0c38bc96.json'))
s=json.loads(F['routing_selection.json'])
print('regenerated_sha256',s['regenerated_sha256'],'rows',s['rows'],'logical_output',s['logical_output'])
pr=s.get('p_regeneration') or {}
print('p_regeneration rows',pr.get('rows'),'equal',pr.get('selected_rows_equal'),'hashes',pr.get('selected_row_hashes'),'src',(pr.get('source_routing') or {}).get('sha256'),(pr.get('source_database') or {}).get('sha256'))
print('row_bytes_sha256',s['row_bytes_sha256'],'== P[0]',s['row_bytes_sha256']==(pr.get('selected_row_hashes') or [None])[0])
print('inputs_pinned keys',list(s['inputs_pinned']))
print('regenerated_receipt',s['regenerated_receipt'])
if 'receipt.json' in F:
    R=json.loads(F['receipt.json']); print('receipt pin match',hashlib.sha256(F['receipt.json']).hexdigest()==s['regenerated_receipt']['sha256'])
    for k in sorted(set(R)|set(P)):
        a,b=R.get(k),P.get(k)
        if a!=b: print('RECEIPT DIFF',k,json.dumps(a)[:300],'| P:',json.dumps(b)[:300])
    print('db',R['database'],'count',R['count'],'types',R['types'])
if 'materialization.json' in F:
    M=json.loads(F['materialization.json']); print('mat sha',hashlib.sha256(F['materialization.json']).hexdigest())
    for k in sorted(set(M)|set(PM)):
        if M.get(k)!=PM.get(k): print('MAT DIFF',k,json.dumps(M.get(k))[:400],'| P:',json.dumps(PM.get(k))[:400])
if 'db_bytes.json' in F: print('db_bytes',F['db_bytes.json'].decode()[:1500])
