from pathlib import Path
L=Path(__file__).resolve().parents[2]
helper='''def protected_rooms(cfg):
    from student_pilot.r1_rooms import Rooms
    from student_pilot.s1_exclusions import dev_names, benchmark_names, Exclusions
    from student_pilot.p3_provenance import pinned
    authority=Rooms(cfg['r1_training']['room_authority'])
    rule=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
    def keys(name):
        ds,scene=name.split('/',1)
        ds={'d1':'scannet','d2':'scannetpp','d3':'arkitscenes'}.get(ds,ds)
        canonical,_=authority.canonical({'canonical':ds+'/'+scene})
        found={rule.key(name),rule.key(canonical)}
        try:found.add(rule.key(authority.room(canonical)))
        except ValueError:pass
        return found
    lists={};payloads={}
    for label,field,reader,name in (
        ('bench_v2','benchmark_scene_exclusions',benchmark_names,'e6.json'),
        ('dev_s1','dev_scene_exclusions',dev_names,'e7.json')):
        pin=cfg[field];raw=pinned(pin).read_bytes()
        lists[label]=dict(names=set().union(*(keys(n) for n in reader(pin))),sha256=pin['sha256'],file=name)
        payloads[name]=raw
    def matches(row):
        canonical,_=authority.canonical(row)
        if not canonical:raise ValueError('R1_PROTECTED_ROOM_UNRESOLVED')
        values=keys(canonical)
        return {label:bool(values & item['names']) for label,item in lists.items()}
    return lists,payloads,matches


'''
for name in ('n','n_go'):
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/n');p=k/'b/rv.py';s=p.read_text()
 s=s.replace('def evidence(cfg, rooms, live):',helper+'def evidence(cfg, rooms, live):')
 s=s.replace('    payloads = {}\n    counts = {}','    protected, payloads, room_matches = protected_rooms(cfg)\n    counts = {}')
 s=s.replace('            empty = 0','            empty = 0\n            room_counts = dict.fromkeys(protected,0)')
 s=s.replace('                row, _ = reader.row(stream, offset)','                row, _ = reader.row(stream, offset)\n                for label,hit in room_matches(row).items():room_counts[label] += int(hit)')
 s=s.replace('counts[stream] = dict(rows=total, answer_only=empty)','counts[stream] = dict(rows=total, answer_only=empty, protected_rooms=room_counts)')
 s=s.replace('question_types=dict(sorted(types.items())), answer_only=empty,','question_types=dict(sorted(types.items())), answer_only=empty,\n                protected_rooms={label:dict(rows=room_counts[label],sha256=v["sha256"],file=v["file"]) for label,v in protected.items()},\n                canonical_room_reader="student_pilot.r1_rooms.Rooms.canonical and Rooms.room; native exclusion-list readers",')
 s=s.replace('    if any(v["answer_only"] for v in counts.values()):','    if any(any(v["protected_rooms"].values()) for v in counts.values()):\n        raise ValueError("R1_PROTECTED_ROOM_ROWS")\n    if any(counts[stream]["answer_only"] for stream in ("vqa","routing")):')
 p.write_text(s)
print('whole-store protected-room counts and scoped answer-only policy installed')
