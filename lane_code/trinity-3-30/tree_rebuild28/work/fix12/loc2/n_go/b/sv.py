"""Publish native scene bindings and census the admitted native selection."""
from pathlib import Path
import sys
import hashlib
import json
import re
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load

STATUSES = ("benchmark","dev","R0","withheld","K1_heldout","official")
# Streams whose rows name scenes only by division token (carrier_c1_routing.alias_of).
TOKEN_STREAMS = ("pose",)
CANONICAL = ("scannet","scannetpp","scannetppv2","arkitscenes")


def classifier(cfg):
    from student_pilot.p3_provenance import pinned
    from student_pilot.s1_exclusions import Exclusions,dev_names,benchmark_names
    from student_pilot.r1_rooms import Rooms
    from student_pilot.r2_withheld import Withheld,room
    from student_pilot.carrier_c1_routing import load_exclusions,alias_key,excluded,alias_of
    authority=Rooms(cfg["r1_training"]["room_authority"])
    rule=Exclusions(cfg["dev_scene_exclusions"],cfg["benchmark_scene_exclusions"])
    draw=Withheld()
    official=load_exclusions(cfg["exclusions"])
    def keys(name):
        result={rule.key(name)}
        # Native canonical and physical-room functions provide cross-capture keys.
        ds,scene=name.split("/",1)
        canonical,_=authority.canonical(dict(dataset=ds,scene=scene))
        if canonical:
            result.add(rule.key(canonical))
            try:result.add(rule.key(authority.room(canonical)))
            except ValueError:pass
        return result
    lists={"benchmark":set().union(*(keys(n) for n in benchmark_names(cfg["benchmark_scene_exclusions"]))),
           "dev":set().union(*(keys(n) for n in dev_names(cfg["dev_scene_exclusions"])))}
    vqa_binding=None
    tokens=None
    def token_map():
        # Pose rows name a scene only by its division token dN/v<hex> = alias_of(canonical). Invert
        # alias_of over every canonical scene the pinned room authority (and the direction-twin
        # alias list), the scene lists and the protected room sets name; never read prepare's matches.
        nonlocal tokens
        if tokens is not None:return tokens
        found=set()
        def collect(value):
            if isinstance(value,dict):
                for k,v in value.items():collect(k);collect(v)
            elif isinstance(value,list):
                for v in value:collect(v)
            elif isinstance(value,str) and value.split('/',1)[0] in CANONICAL and value.count('/')==1 and all(value.split('/')):
                found.add(value)
        pins=dict(cfg["r1_training"]["room_authority"])
        twins=cfg["r1_training"].get("direction_twins")
        if twins:pins["twin_aliases"]=twins["aliases"]
        def read(pin):
            try:return json.loads(pinned(pin).read_bytes())
            except (ValueError,UnicodeDecodeError):return None
        for key in sorted(pins):collect(read(pins[key]))
        collect(list(authority.aliases.values()))
        collect(['arkitscenes/'+v for v in authority.visits])
        for name in ("dev_scene_exclusions","benchmark_scene_exclusions","exclusions"):
            if cfg.get(name):collect(read(cfg[name]))
        rooms=authority.r0|authority.k1|draw.aliases
        collect(sorted(rooms))
        collect([r+'_%02d'%i for r in sorted(rooms) if r.startswith('scannet/scene') and re.fullmatch(r'scannet/scene\d+',r) for i in range(100)])
        tokens={}
        for canonical in sorted(found):
            try:token=rule.key(alias_of(canonical))
            except (KeyError,ValueError):continue
            # scannetpp/x and scannetppv2/x are one scene with one token; any other clash is a conflict.
            if tokens.setdefault(token,canonical)!=canonical and alias_key(tokens[token] or '')!=alias_key(canonical):tokens[token]=None
        return tokens
    def token_canonical(row):
        try:ids=rule.identifiers(row)
        except ValueError:return None,'unresolved'
        found={token_map().get(k) for k in ids if k in token_map()}
        if None in found:raise ValueError('R1_CENSUS_TOKEN_CONFLICT')
        if len(found)>1:raise ValueError('R1_CENSUS_TOKEN_CONFLICT')
        return (found.pop(),'division_token') if found else (None,'unresolved')
    named=None
    def listed_dataset(row):
        # A dataset any list or protected room set names; its rows need a scene-level verdict.
        nonlocal named
        if named is None:
            named=set()
            for value in (*lists['benchmark'],*lists['dev'],*official,*authority.r0,*authority.k1,*draw.aliases):
                if isinstance(value,str) and '/' in value:
                    head=value.split('/',1)[0]
                    try:named.add(rule.dataset(head))
                    except Exception:named.add(head.casefold())
        try:ds=rule.dataset(row.get('dataset'))
        except Exception:return True
        return ds in named
    def classify(row,stream,detail=None):
        nonlocal vqa_binding
        status,canonical,how=authority.status(row)
        physical=None;level='scene'
        if stream in TOKEN_STREAMS and not canonical:
            canonical,how=token_canonical(row)
        if stream=='vqa' and status=='unresolved' and cfg.get('r1_training',{}).get('direction_twins'):
            from student_pilot.r1_direction_twins import Binding
            if vqa_binding is None:vqa_binding=Binding(cfg)
            physical=vqa_binding.room(row)
            canonical,_=vqa_binding.tiered.canonical(row)
        candidates=[canonical] if canonical else []
        if stream=='pointing':
            other=(row.get('provenance') or {}).get('canonical_scene')
            if other and other not in candidates:candidates.append(other)
        names=set();physical_rooms=set()
        if physical:physical_rooms.add(physical)
        for candidate in candidates:
            names.update(keys(candidate))
            try:physical_rooms.add(authority.room(candidate))
            except ValueError:raise ValueError('R1_CENSUS_ROOM_UNRESOLVED:'+stream) from None
        try:names.update(rule.identifiers(row))
        except ValueError:
            if not candidates:raise
        names.update(rule.key(room_name) for room_name in physical_rooms)
        if not physical_rooms:
            # Dataset-level verdict only for a dataset no list and no protected room set names.
            if stream in TOKEN_STREAMS and not candidates and not listed_dataset(row):level='dataset'
            else:raise ValueError('R1_CENSUS_ROOM_UNRESOLVED:'+stream)
        if detail is not None:detail.update(level=level,how=how,dataset=str(row.get('dataset')))
        return dict(benchmark=bool(names & lists['benchmark']),dev=bool(names & lists['dev']),
                    R0=bool(physical_rooms & authority.r0),withheld=draw.touches(dict(row,dataset=row.get('dataset',''),scene=row.get('scene','')),dict(names=sorted(names))),
                    K1_heldout=bool(physical_rooms & authority.k1),official=excluded(official,*(alias_key(n) for n in names)))
    return classify


def publish(kit,root,cfg,job):
    from rv import location,put,encoded
    from student_pilot.p3_provenance import pinned,file_pin
    from student_pilot.carrier_c1_run import Rows
    from student_pilot.row_removals import row_keys
    from student_pilot.r2_withheld import SHA256
    live,_=location(Path(kit),Path(root),job)
    classify=classifier(cfg)
    rp=pinned(cfg["r2_scene_rebuild"]);cp=pinned(cfg["scene_coverage"]["reference"])
    payload={"s0.json":rp.read_bytes(),"s1.json":cp.read_bytes()}
    counts={s:dict.fromkeys((*STATUSES,"admitted"),0) for s in ("pose","vqa","routing","pointing")}
    hits={s:[] for s in counts}
    failure=None
    reader=Rows(load(pinned(cfg["preparation"])),None)
    try:
        for stream in counts:
            for index in range(reader.count(stream)):
                row,_=reader.row(stream,index)
                flags=classify(row,stream)
                counts[stream]["admitted"]+=1
                for name,hit in flags.items():counts[stream][name]+=int(hit)
                if any(flags.values()):
                    hits[stream].append(dict(row_keys=sorted(row_keys(row)),statuses=[n for n,v in flags.items() if v]))
                    failure="R1_SCENE_PROTECTED_ADMITTED_ROWS"
    finally:reader.close()
    payload["s3.json"]=encoded(hits)
    payload["s2.json"]=encoded(dict(status="REFUSE" if failure else "PASS",refusal=failure,counts=counts,
        receipt=dict(file="s0.json",sha256=file_pin(rp)["sha256"]),
        coverage=dict(file="s1.json",sha256=file_pin(cp)["sha256"]),
        row_keys=dict(file="s3.json",sha256=hashlib.sha256(payload["s3.json"]).hexdigest()),
        files=dict(dev=cfg["dev_scene_exclusions"],benchmark=cfg["benchmark_scene_exclusions"],official=cfg["exclusions"]),
        authority=cfg["r1_training"]["room_authority"],withheld_sha256=SHA256,
        counts_scope="Whole native prepared Rows selection after removals; protected statuses overlap; refusal precedes review."))
    if sum(map(len,payload.values()))>=1_000_000:raise ValueError("R1_SCENE_EVIDENCE_TOO_LARGE")
    for name,raw in payload.items():put(live/name,raw)
    if failure:raise ValueError(failure)
    return counts
