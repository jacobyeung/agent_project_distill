import json, hashlib, hmac, tarfile, collections
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1vsti/'
S='/scratch/jjyeung/orch_n30/rows_r1/out/vsti_rel_dev_r0/'
src=[json.loads(l) for l in open(S+'items.jsonl')]
lay=[json.loads(l) for l in open(S+'R0DEV_VSTI_QUESTIONS.jsonl')]
ast=[json.loads(l) for l in open(K+'assets/b62c14e9.jsonl')]
key=bytes.fromhex(json.load(open(K+'evidence/ID_KEY.json'))['key_hex'])
a7=[json.loads(l) for l in open(K+'assets/e52a690b.jsonl')]
a7map=json.load(open(K+'evidence/ID_MAP.json'))
# a7 room <-> physical room bijection
r2p=collections.defaultdict(set); p2r=collections.defaultdict(set)
for r in a7:
    m=a7map[r['id']]; p=(m['dataset'],m['scene']); r2p[r['room']].add(p); p2r[p].add(r['room'])
    assert all(x.split('/')[0]==r['room'] for x in r['frame_refs']), 'a7 ref prefix'
assert all(len(v)==1 for v in r2p.values()) and all(len(v)==1 for v in p2r.values()), 'a7 room map not bijective'
print('a7 rooms bijective', len(r2p))
assert len(src)==len(lay)==len(ast)==900
# tar member hashes
tf=tarfile.open(K+'assets/d81f4a26.tar'); th={}
for mem in tf:
    if mem.isfile(): th[mem.name]=hashlib.sha256(tf.extractfile(mem).read()).hexdigest()
print('tar members', len(th))
bad=collections.Counter(); keys=set()
for s,l,a in zip(src,lay,ast):
    for k,v in s.items():
        if l.get(k)!=v: bad['layout_'+k]+=1
    ident=hmac.new(key,('r6-item\0'+s['qid']).encode(),hashlib.sha256).hexdigest()[:24]
    if a['id']!=ident: bad['id']+=1
    for f,g in [('question','question'),('options','options'),('answer','answer'),('answer','ground_truth'),('question_type','question_type'),('frame_indices','source_frame_indices'),('fps','fps'),('total_num_frames','total_num_frames')]:
        if s[f]!=a[g]: bad[g]+=1
    if not (s['options'] and s['answer'] in 'ABCD'[:len(s['options'])]): bad['gold_range']+=1
    # option text letter-labelled
    if s['answer'] in a['question']: pass
    if len(a['frame_refs'])!=32: bad['nref']+=1
    for fr,ref in zip(s['frames'],a['frame_refs']):
        if th.get(ref)!=fr['sha256']: bad['frame_sha']+=1
    if [f['tar_member'] for f in s['frames']]!=[f"frames/{s['dataset']}/{s['scene']}/{i:06d}.png" for i in s['frame_indices']]: bad['member_order']+=1
    p=(s['dataset'],s['scene'])
    if p2r.get(p)!={a['room']}: bad['room']+=1
    if a['scene']!=a['room']: bad['scene']+=1
    if any(x.split('/')[0]!=a['room'] for x in a['frame_refs']): bad['ref_room']+=1
    extra=set(a)-{'id','example_id','room','scene','benchmark','question_type','question','options','ground_truth','answer','unit','answer_type','source_frame_indices','frame_refs','fps','total_num_frames','subtype','thinking'}
    if extra: bad['extra_keys']+=1
    keys.add(tuple(sorted(a)))
print('mismatches', dict(bad)); print('key sets', keys)
print('types', collections.Counter(a['question_type'] for a in ast)); print('rooms', len({a['room'] for a in ast}))
print('gold dist', collections.Counter((a['question_type'],a['answer']) for a in ast))
