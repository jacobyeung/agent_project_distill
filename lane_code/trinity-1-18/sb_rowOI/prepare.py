"""Stage pinned metadata, source rows and conservative GT clip inventories; CPU only."""
import os
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,json,hashlib,sqlite3,re,collections,itertools
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
sys.path[:0]=[str(TREE),str(ROOT/'inputs/b12/code')]
from student_pilot.r1_rooms import Rooms
from gtvis import norm,DENY,ambiguous
PINS={}
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):
    p=Path(p);PINS[str(p)]=sha(p);return p
def load(p):return json.loads(pin(p).read_text())
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=1)+'\n')
def strings(v):
    if isinstance(v,str):yield v
    elif isinstance(v,list):
        for x in v:yield from strings(x)
    elif isinstance(v,dict):
        for k,x in v.items():yield k;yield from strings(x)
def main():
    cfg=load(TREE.parent/'build19/inputs/config.json'); auth=cfg['r1_training']['room_authority']
    for v in auth.values():assert sha(pin(v['path']))==v['sha256']
    rooms=Rooms(auth)
    dev=load(ROOT/'inputs/dev_s1.json');assert PINS[str(ROOT/'inputs/dev_s1.json')].startswith('969cdb56')
    bench=load(cfg['benchmark_scene_exclusions']['path'])
    withheld=load(TREE.parents[1]/'fixtures/work/shared/WITHHELD_ROOMS_80.json')
    def canonical(s):
        s=re.sub(r'^d1/','scannet/',s);s=re.sub(r'^d2/','scannetpp/',s);s=re.sub(r'^d3/','arkitscenes/',s)
        return rooms.aliases.get(s,s)
    excluded=set(withheld['rooms']); raw=set(strings(dev))|set(strings(bench))|set(strings(withheld))
    for s in raw:
        s=canonical(s)
        if '/' in s:
            excluded.add(s)
            try:excluded.add(rooms.room(s))
            except (ValueError,TypeError):pass
    b=ROOT/'inputs/b12'; dv=load(b/'work/d0_vocab.json');bv=load(b/'work/bench_vocab.json')
    vocab={}
    for ds,bn in [('d1','scannet'),('d2','scannetpp'),('d3','arkitscenes')]:
        vocab[ds]={norm(x) for k,v in dv.items() if k.endswith('|'+ds) for x in v}|{norm(x) for k,v in bv.items() if k.endswith('|'+bn) for x in v}
    ts=load(b/'out/PACKET_b12_v4/ARK_PIN_TS_CHECK.json');ts2=load(b/'out/PACKET_b12_v4/ARK_PIN_TS_CHECK_K1.json')
    rasters={p.name:p for p in (b/'work/rasters').glob('*.npz')}
    if not rasters:rasters={p.name:p for p in (b/'work/rasters').rglob('*.npz')}
    db=pin(b/'out/PACKET_b12_v4/rows.sqlite'); con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
    sources=collections.defaultdict(list)
    for (s,) in con.execute('select row from rows'):
        r=json.loads(s)
        if r['question_type']=='object_counting':sources[r['provenance']['canonical']].append(r)
    counts=collections.Counter();facts=[];kept=[]
    for canon,rs in sorted(sources.items()):
        r=rs[0];alias=r['dataset']+'/'+r['scene']; status,_,_=rooms.status(r)
        if status!='ok' or rooms.room(canon) in excluded or canon in excluded or alias in raw:counts['excluded_room']+=1;continue
        if r['dataset']=='d3' and not all(v=='ok' for v in [ts.get(alias,'ok'),ts2.get(alias,'ok')]) or (r['dataset']=='d3' and alias not in ts and alias not in ts2):counts['alignment']+=1;continue
        p=rasters.get(r['provenance']['raster'])
        if p is None:counts['missing_raster']+=1;continue
        assert sha(pin(p))==r['provenance']['raster_sha256']
        with np.load(p) as z:
            fi=z['frame_indices'].tolist()
            if fi!=r['student_input']['frame_indices']:counts['pins_differ']+=1;continue
            inst=z['inst'];labels={int(i):norm(l) for i,l in zip(z['ids'],z['labels'])}
            valid=np.asarray(z['valid'],dtype=bool)&(z['depth']>0).any(axis=(1,2)) if 'valid' in z.files else np.ones(len(fi),dtype=bool)
            # B12 rule: every annotation must be visible, with all pins through
            # its first observation valid. Later pose gaps do not add annotations.
            by=collections.defaultdict(list)
            for i,l in labels.items():by[l].append(i)
            cats={}
            for c,ids in by.items():
                w=c.split()[-1]
                plural=w.endswith('s') and not w.endswith(('ss','us','is','os')) and w not in {'canvas','atlas','lens','gas','bias','news','chassis'}
                if len(ids)>3 or c not in vocab[r['dataset']] or c in DENY or plural or ambiguous(c,set(by)) or re.search(r'\d|frame|\b(?:foot|feet|inch|inches|yard|meter|meters|metre|square|degree|cm|mm|m|ft|in|km|deg)\b',c):continue
                visible=[]
                for i in ids:
                    shares=(inst==i).sum(axis=(1,2))/(inst.shape[1]*inst.shape[2]); f=np.flatnonzero(shares>=.002)
                    if not len(f) or not valid[:int(f[0])+1].all():break
                    visible.append(dict(id=i,first_pin=int(f[0])+1,max_share=float(shares.max())))
                else:cats[c]=visible
        if sum(len(v)==1 for v in cats.values())<2 or not any(len(v)>1 for v in cats.values()):counts['no_pair']+=1;continue
        selected=sorted(rs,key=lambda x:x['qid'])[:6]
        facts.append(dict(canonical=canon,room=rooms.room(canon),raster=str(p),raster_sha256=sha(p),categories=cats,source_qids=[x['qid'] for x in selected]))
        kept.extend(selected);counts['eligible_scenes']+=1
        if counts['eligible_scenes']%100==0:print(dict(counts),flush=True)
    Path('inputs/sources.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in kept))
    # Wordings are read only for rejection, never as generation templates.
    corpus=set();corpus_files=[]
    def questions(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k in ('question','prompt','question_text') and isinstance(x,str):corpus.add(x)
                elif isinstance(x,(dict,list)):questions(x)
        elif isinstance(v,list):
            for x in v:questions(x)
    ps=list((ROOT/'inputs/eval').rglob('*.json*'))+list((TREE/'tests/fixtures/benchmark_eval').rglob('*.json'))+[Path('/scratch/jjyeung/n30_mirror/rows_r1/out/vsti_rel_dev_r0/items.jsonl')]
    for p in sorted(ps):
        if p.stat().st_size>40000000:continue
        try:
            before=len(corpus)
            if p.suffix=='.jsonl':
                for l in p.open():
                    if l.strip():questions(json.loads(l))
            else:questions(json.loads(p.read_text()))
            pin(p);corpus_files.append(str(p))
        except (json.JSONDecodeError,UnicodeDecodeError):continue
    dump('inputs/wordings.json',dict(wordings=sorted(corpus),files=corpus_files,input_sha256=PINS))
    for p in [ROOT/'inputs/procedure_sources.jsonl',Path(__file__),TREE/'student_pilot/r1_rooms.py',TREE.parents[1]/'out/TREE_SEAL.json']:pin(p)
    dump('inputs/inventory.json',dict(scenes=facts,counts=counts,room_authority=auth,excluded_rooms=sorted(excluded),input_sha256=PINS))
    Path('STATUS.md').write_text('Inventory preparation is complete. Ground-truth instance counts, complete raster pins, physical-room exclusions, source rows, and rejection-only wording references are staged locally. The generator will assert the planned paired cells.\n')
    print('DONE',dict(counts),'wordings',len(corpus))
if __name__=='__main__':main()
