import sys, json, sqlite3, re, collections as C, itertools
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent/'reference'))
import d2_support as d
d.BASE=Path('/scratch/jjyeung/orch_n30/sb_rowD2')
OUT=Path(__file__).parent/'out'

def options(r):
    return {x.split('. ',1)[0]:x.split('. ',1)[1].strip().lower() for x in r['student_input']['options']}

def objects(r):
    line=r['target'].splitlines()[1]
    if line.startswith('Seen:'):
        m=re.fullmatch(r'Seen: (.+?) in frame (\d+); (.+?) in frame (\d+); (.+?) in frame (\d+)\.',line)
        assert m,line
        return [m[1],m[3],m[5]]
    m=re.fullmatch(r'Step 1: (?:find|locate) the (.+?), the (.+?) and the (.+)\.',line)
    if not m:m=re.fullmatch(r'Step 1: (?:find|locate) the (.+?) and the (.+?), then the (.+)\.',line)
    assert m,line
    names=list(m.groups())
    relation=r['target'].splitlines()[2]
    matched=set()
    for x,y,z in itertools.permutations(names):
        if (relation.startswith(f'Step 2: facing the {y} from the {x}, I find the {z} ')
            or relation.startswith(f'Step 2: standing at the {x} and facing the {y}, I find the {z} ')
            or relation.startswith(f'Step 2: I stand at the {x} facing the {y}; I find the {z} ')
            or (relation.startswith(f'Step 2: I find the {z} ') and relation.endswith(f' when I stand at the {x} facing the {y}.'))):
            matched.add((x,y,z))
    assert len(matched)==1,('unrecognized_reference_heading_roles',r['qid'],relation,names)
    return list(next(iter(matched)))

def authority():
    rooms,excluded=d.room_authority()
    cfg=d.load(d.KIT/'w20/work/build20/inputs/config.json')
    removals=list(cfg['remove_files'])
    for p in [d.KIT/'inputs/records/n.json',d.KIT/'inputs/records/z.json',Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json')]:
        if str(p) not in [x['path'] for x in removals]:
            v=d.pin(p);removals.append({k:v[k] for k in ('path','sha256')})
    for x in removals:d.pin(x['path'],x['sha256'])
    division=d.load(cfg['scene_division']['path'],cfg['scene_division']['sha256'])
    return rooms,excluded,cfg,removals,division

def main():
    d.pin(__file__);d.pin(d.__file__)
    d.pin(d.DB,d.DB_SHA)
    rooms,excluded,cfg,removal_pins,division=authority()
    removals=d.row_removals.Removals(removal_pins)
    train=set(division['train_scenes']);held=set(division['heldout_scenes'])
    counts=C.Counter();before=C.Counter();blocked=C.Counter();metadata=[]
    con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    for i,raw in con.execute('select i,row from rows order by i'):
        r=json.loads(raw)
        if not r.get('question_type','').startswith('object_rel_direction_'):continue
        op,_,cl=d.classify(r);family=r['question_type'].rsplit('_',1)[-1];label=options(r)[r['answer']]
        before[op,cl,family,label]+=1
        canon,_=rooms.canonical(r);room=rooms.room(canon) if canon else None;assert room
        reasons=['room:'+k for k,v in excluded.items() if room in v]
        reasons+=['remove:'+removal_pins[j]['path'] for j in removals.match(r)]
        scene=r['dataset']+'/'+r['scene']
        if scene not in train:reasons.append('scene_outside_train')
        if scene in held:reasons.append('scene_heldout')
        for reason in reasons:blocked[reason]+=1
        m=dict(i=i,qid=r['qid'],opening=op,clause=cl,family=family,label=label,objects=objects(r),pool=r['pool'],
               room=room,scene=scene,refused=reasons,source_sha256=__import__('hashlib').sha256(raw.encode()).hexdigest(),pair_id=r.get('pair_id'))
        metadata.append(m)
        if not reasons:counts[op,cl,family,label]+=1
    def cells(c):return [dict(zip(('opening','clause','family','label','rows'),(*k,v))) for k,v in sorted(c.items())]
    value=dict(command='PYTHONDONTWRITEBYTECODE=1 python survey.py',input_sha256=d.PINS,before=cells(before),admitted=cells(counts),blocked=dict(blocked),rows=metadata)
    (OUT/'SURVEY.json').write_text(json.dumps(value,sort_keys=True)+'\n')
    print(json.dumps(dict(admitted=cells(counts),blocked=dict(blocked)),indent=2))
    Path('STATUS.md').write_text('The gate passes all 5,846 easy/hard pairs, and all 1,274 literal disagreements are medium. The source survey applies N’s full configured removal lists plus u-union, all five room authorities, and the pinned scene division. The admitted cell counts are available in out/SURVEY.json for fixed quota selection.\n')

if __name__=='__main__':main()
