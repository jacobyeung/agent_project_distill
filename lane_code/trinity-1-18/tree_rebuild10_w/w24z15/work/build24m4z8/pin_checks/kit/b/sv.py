"""Publish native scene bindings and census the admitted native selection."""
from pathlib import Path
import sys
import hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load

STATUSES = ("benchmark","dev","R0","withheld","K1_heldout","official")


def classifier(cfg):
    from student_pilot.p3_provenance import pinned
    from student_pilot.s1_exclusions import Exclusions,dev_names,benchmark_names
    from student_pilot.r1_rooms import Rooms
    from student_pilot.r2_withheld import Withheld,room
    from student_pilot.carrier_c1_routing import load_exclusions,alias_key,excluded
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
    def classify(row,stream):
        nonlocal vqa_binding
        status,canonical,how=authority.status(row)
        physical=None
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
        if not physical_rooms:raise ValueError('R1_CENSUS_ROOM_UNRESOLVED:'+stream)
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
    payload["s2.json"]=encoded(dict(status="REFUSE" if failure else "\x50ASS",refusal=failure,counts=counts,
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
