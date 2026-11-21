"""Publish native scene bindings and census the admitted native selection."""
from pathlib import Path
import sys
import hashlib
import json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load

STATUSES = ("benchmark","dev","R0","withheld","K1_heldout","official")
# Which list protects which stream (ORCH RULING 2026-11-21T17:16Z item 6). A status that does not
# protect a stream is counted for it as exposure (recorded, not protected) and never as protected.
PROTECTION = {"benchmark":("pose","vqa","routing","pointing"),"dev":("pose","vqa","routing","pointing"),
              "R0":("pose","vqa","routing","pointing"),"withheld":("pose","vqa","routing","pointing"),
              "official":("pose","vqa","routing","pointing"),"K1_heldout":("vqa","pointing")}
# Streams whose rows name scenes only by division token dN/v<hex> (carrier_c1_routing.alias_of).
TOKEN_STREAMS = ("pose",)
CANONICAL = ("scannet","scannetpp","scannetppv2","arkitscenes")
# ScanNet captures form a closed namespace; its tokens are an exact lookup (RULING 1716Z item 1).
SCANNET_NAMESPACE = tuple('scannet/scene%04d_%02d'%(a,b) for a in range(807) for b in range(10))


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
    def collect(value,found):
        if isinstance(value,dict):
            for k,v in value.items():collect(k,found);collect(v,found)
        elif isinstance(value,list):
            for v in value:collect(v,found)
        elif isinstance(value,str) and value.split('/',1)[0] in CANONICAL and value.count('/')==1 and all(value.split('/')):
            found.add(value)
    def read(pin):
        try:return json.loads(pinned(pin).read_bytes())
        except (ValueError,UnicodeDecodeError):return None
    def invert(canonicals):
        table={}
        for canonical in sorted(canonicals):
            try:token=rule.key(alias_of(canonical))
            except (KeyError,ValueError):continue
            # scannetpp/x and scannetppv2/x are one scene with one token; any other clash is a conflict.
            if table.setdefault(token,canonical)!=canonical and alias_key(table[token] or '')!=alias_key(canonical):table[token]=None
        return table
    # Tier 1: every canonical scene the pinned room authority, the direction-twin alias list, the scene
    # lists and the protected room sets name. Tier 2: the whole ScanNet capture namespace. Never prepare's matches.
    found=set()
    pins=dict(cfg["r1_training"]["room_authority"])
    if cfg["r1_training"].get("direction_twins"):pins["twin_aliases"]=cfg["r1_training"]["direction_twins"]["aliases"]
    for key in sorted(pins):collect(read(pins[key]),found)
    collect(list(authority.aliases.values()),found)
    collect(['arkitscenes/'+v for v in authority.visits],found)
    for name in ("dev_scene_exclusions","benchmark_scene_exclusions","exclusions"):
        if cfg.get(name):collect(read(cfg[name]),found)
    collect(sorted(authority.r0|authority.k1|draw.aliases),found)
    named_tokens=invert(found)
    namespace=invert(SCANNET_NAMESPACE)
    if len(namespace)!=len(SCANNET_NAMESPACE) or None in namespace.values():raise ValueError('R1_CENSUS_NAMESPACE_TOKEN_COLLISION')
    if any(named_tokens.get(k) not in (None,v) and alias_key(named_tokens[k])!=alias_key(v) for k,v in namespace.items() if k in named_tokens):
        raise ValueError('R1_CENSUS_NAMESPACE_TOKEN_COLLISION')
    def resolve_token(key):
        for how,table in (('aliases_token',named_tokens),('namespace_token',namespace)):
            if key in table:
                if table[key] is None:raise ValueError('R1_CENSUS_TOKEN_CONFLICT')
                return table[key],how
        return None,None
    def keys(name):
        result={rule.key(name)}
        # Native canonical and physical-room functions provide cross-capture keys; a listed division
        # token resolves to its capture, so its whole physical room is listed (RULING 1716Z item 2).
        ds,scene=name.split("/",1)
        canonical,_=authority.canonical(dict(dataset=ds,scene=scene))
        if not canonical:
            try:canonical,_=resolve_token(rule.key(name))
            except ValueError:canonical=None
        if canonical:
            result.add(rule.key(canonical))
            try:result.add(rule.key(authority.room(canonical)))
            except ValueError:pass
        return result
    lists={"benchmark":set().union(*(keys(n) for n in benchmark_names(cfg["benchmark_scene_exclusions"]))),
           "dev":set().union(*(keys(n) for n in dev_names(cfg["dev_scene_exclusions"])))}
    official_rooms=set(official)
    for n in official:
        if '/' in n:
            try:official_rooms.update(alias_key(k) for k in keys(n))
            except Exception:pass
    vqa_binding=None
    def family(value):
        # Routing rows carry their source family as a record; the receipt keeps its name only.
        return value.get('name') if isinstance(value,dict) else value
    def token_canonical(row):
        try:ids=rule.identifiers(row)
        except ValueError:return None,'unresolved'
        found={}
        for k in ids:
            canonical,how=resolve_token(k)
            if canonical:found[canonical]=how
        if len({alias_key(c) for c in found})>1:raise ValueError('R1_CENSUS_TOKEN_CONFLICT')
        return next(iter(found.items())) if found else (None,'unresolved')
    def classify(row,stream,detail=None):
        nonlocal vqa_binding
        status,canonical,how=authority.status(row)
        how='authority_'+how
        physical=None
        if stream in TOKEN_STREAMS and not canonical:
            canonical,how=token_canonical(row)
        if stream=='vqa' and status=='unresolved' and cfg.get('r1_training',{}).get('direction_twins'):
            from student_pilot.r1_direction_twins import Binding
            if vqa_binding is None:vqa_binding=Binding(cfg)
            physical=vqa_binding.room(row)
            canonical,_=vqa_binding.tiered.canonical(row)
            how='twin_binding'
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
        if not physical_rooms:raise ValueError('R1_CENSUS_ROOM_UNRESOLVED:'+stream)
        flags=dict(benchmark=bool(names & lists['benchmark']),dev=bool(names & lists['dev']),
                   R0=bool(physical_rooms & authority.r0),withheld=draw.touches(dict(row,dataset=row.get('dataset',''),scene=row.get('scene','')),dict(names=sorted(names))),
                   K1_heldout=bool(physical_rooms & authority.k1),official=excluded(official_rooms,*(alias_key(n) for n in names)))
        exposure=sorted(k for k,v in flags.items() if v and stream not in PROTECTION[k])
        for k in exposure:flags[k]=False
        if detail is not None:detail.update(how=how,exposure=exposure,dataset=str(row.get('dataset')),
                                            category=str(row.get('category')),s1_source=str(family(row.get('s1_source'))))
        return flags
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
