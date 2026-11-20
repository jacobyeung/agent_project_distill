import json,gzip,hashlib,struct,collections,sys
D=sys.argv[1]
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
rd=json.load(gzip.open(D+'/rd0/rdiff.json.gz')); byP={e['P']['i']:e for e in rd['N']}
ns=json.load(open(D+'/n_sample.json')); ps=json.load(open(D+'/p_sample.json'))
P={r['i']:r for r in ps['rows']}
def flat(x,p=''):
    if isinstance(x,dict):
        out={}
        for k,v in x.items(): out.update(flat(v,p+'/'+k.replace('~','~0').replace('/','~1')))
        return out or {p:{}}
    if isinstance(x,list):
        out={}
        for i,v in enumerate(x): out.update(flat(v,p+'/'+str(i)))
        return out or {p:[]}
    return {p:x}
NINE=('source_qid','candidate_id','question','question_type','answer','gt_answer','ground_record','provenance','tool_output_spans')
PATHS=('/row/s1_source/source/path','/row/s1_source/frame_binding/authority/map/path','/row/s1_source/frame_binding/authority/plan/path','/row/s1_source/frame_binding/authority/fps_authority/path')
c=collections.Counter(); other=collections.Counter(); hashok=0
for r in ns['rows']:
    e=byP.get(r['P_i']); h=hashlib.sha256(packed((r['i'],r['row'],r['target']))).hexdigest()
    hashok+= e is not None and h==e['content_sha256'] and e['i']==r['i']
    p=P.get(r['P_i'])
    if p is None: c['no_P_sample']+=1; continue
    a=flat(dict(i=p['i'],row=json.loads(p['row']),target=json.loads(p['target']) if p['target'] else p['target']))
    b=flat(dict(i=r['i'],row=json.loads(r['row']),target=json.loads(r['target']) if r['target'] else r['target']))
    c['pairs']+=1
    for k in set(a)|set(b):
        if a.get(k,'<m>')==b.get(k,'<m>'): continue
        top=k.split('/')[2] if k.startswith('/row/') else None
        if k=='/i': c['class_i']+=1
        elif top in NINE and k.split('/')[2] in NINE and '/row/'+top not in [] and not (top in json.loads(p['row'])): c['class_copied']+=1
        elif any(k==q for q in PATHS): c['class_paths']+=1
        elif k=='/row/s1_source/frame_binding/fps_source': c['class_fps_source']+=1
        else: other[k]+=1
    pr=json.loads(p['row']); nr=json.loads(r['row'])
    proj=lambda x:(x.get('student_input'),x.get('target'),x.get('routing'),x.get('qid'),x.get('dataset'),x.get('scene'),x.get('category'),x.get('r1_source'),x.get('events'),x.get('form'))
    c['proj_equal']+= proj(pr)==proj(nr); c['sql_target_equal']+= p['target']==r['target']
    c['copies_absent_in_P']+= all(k not in pr for k in NINE if k in nr)
    rt=pr.get('routing') or {}
    c['copies_equal_nested_or_new']+= all((k not in rt) or rt[k]==nr[k] for k in NINE if k in nr)
print('n_sample rows',len(ns['rows']),'hash_and_i_equal_rdiff_N',hashok)
print(dict(c)); print('OTHER',other.most_common(20))
