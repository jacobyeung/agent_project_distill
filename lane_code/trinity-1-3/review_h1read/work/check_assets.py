import json,hashlib,tarfile,collections,sys
H='/scratch/jjyeung/orch_n30/cont_ops/work/h1read/'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<24),b''): h.update(b)
    return h.hexdigest()
src=[json.loads(l) for l in open('arc/out/qsets/R0_QUESTIONS_dev_f32.jsonl')]
items=[json.loads(l) for l in open(H+'assets/e52a690b.jsonl')]
idm=json.load(open(H+'evidence/ID_MAP.json'))
reg=json.load(open(H+'kit/launcher/EXTRA.json'))
bad=collections.Counter()
assert len(items)==2169==len(src)
lines=set()
need={}  # source member -> asset ref
for it in items:
    m=idm[it['id']]; lines.add(m['source_line']); s=src[m['source_line']-1]
    if s['qid']!=m['qid'] or s['scene']!=m['scene']: bad['map']+=1
    for a,b in [('question','question'),('options','options'),('answer','answer'),('answer','ground_truth'),('unit','unit'),('question_type','question_type'),('frame_indices','source_frame_indices'),('fps','fps'),('total_num_frames','total_num_frames'),('subtype','subtype')]:
        if s[a]!=it[b] or type(s[a])!=type(it[b]): bad['field_'+b]+=1
    if it['example_id']!=it['id']: bad['exid']+=1
    if len(it['frame_refs'])!=32: bad['nrefs']+=1
    for i,ref in zip(s['frame_indices'],it['frame_refs']):
        k=f"frames/{s['dataset']}/{s['scene']}/{i:06d}.png"
        if need.get(k,ref)!=ref: bad['refclash']+=1
        need[k]=ref
    if s['num_frames']!=32: bad['nf']+=1
# room consistency
rm=collections.defaultdict(set)
for it in items: rm[it['room']].add(idm[it['id']]['scene'])
print('rooms',len(rm),'rooms mapping to >1 scene',sum(len(v)>1 for v in rm.values()))
sc=collections.defaultdict(set)
for it in items: sc[idm[it['id']]['scene']].add(it['room'])
print('scenes',len(sc),'scenes>1 room',sum(len(v)>1 for v in sc.values()))
print('lines covered',len(lines))
# ref -> source unique
inv=collections.defaultdict(set)
for k,v in need.items(): inv[v].add(k)
print('refs',len(inv),'ref with >1 source',sum(len(v)>1 for v in inv.values()), 'reg frames', len(reg['frames']), set(inv)==set(reg['frames']))
# source archive pass
srcsha={}
with tarfile.open('/scratch/jjyeung/n30_mirror/b10_reserve/R0_RESERVE_20261116.tar') as t:
    for m in t:
        n=m.name.removeprefix('./')
        if n in need: srcsha[n]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
print('found src',len(srcsha),'of',len(need))
for k,v in need.items():
    if reg['frames'][v]['sha256']!=srcsha.get(k): bad['framesha']+=1
# asset tar pass
names=[];
with tarfile.open(H+'assets/d81f4a26.tar') as t:
    for m in t:
        names.append(m.name)
        if m.uid or m.gid or m.mtime or m.uname or m.gname or m.mode!=0o644 or not m.isfile(): bad['meta']+=1
        if hashlib.sha256(t.extractfile(m).read()).hexdigest()!=reg['frames'][m.name]['sha256']: bad['assetsha']+=1
print('asset members',len(names),'sorted',names==sorted(names),'unique',len(set(names)),'== reg',set(names)==set(reg['frames']))
for f in ('d81f4a26.tar','e52a690b.jsonl'):
    print(f, sha(H+'assets/'+f)==reg['files'][f]['sha256'])
# deferred
d=json.load(open('arc/out/DEFERRED.json'))
dev=[k for k,v in d['deferred'].items() if v['r0_split']=='R0-dev']
print('deferred dev',dev,[hashlib.sha256(k.encode()).hexdigest()[:24] for k in dev], reg['deferred_room_ids'])
devrooms=open('arc/out/R0_DEV_ROOMS.txt').read().split()
print('dev rooms',len(devrooms), devrooms[:2])
print('BAD',dict(bad))
