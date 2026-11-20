from common import *
for name in ('q','n','n_go','qd'):
 k=kit(name);s=(k/'b/sv.py').read_text()
 start=s.index('    def classify(row,stream):');end=s.index('    return classify',start)
 s=s[:start]+'''    vqa_binding=None
    def classify(row,stream):
        nonlocal vqa_binding
        canonical,how=authority.canonical(row)
        physical=None
        if stream=='vqa' and not canonical and cfg.get('r1_training',{}).get('direction_twins'):
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
            except ValueError:pass
        try:names.update(rule.identifiers(row))
        except ValueError:
            if not candidates:raise
        names.update(rule.key(room_name) for room_name in physical_rooms)
        if not candidates:raise ValueError('R1_SCENE_STATUS_UNRESOLVED:'+stream)
        return dict(benchmark=bool(names & lists['benchmark']),dev=bool(names & lists['dev']),
                    R0=bool(physical_rooms & authority.r0),withheld=any(room(n) in draw.aliases for n in names),
                    K1_heldout=bool(physical_rooms & authority.k1),official=excluded(official,*(alias_key(n) for n in names)))
'''+s[end:]
 replace(k/'b/sv.py',s)
 for p in ('BUILD.json','SHA256SUMS.txt'):replace(k/p,(k/p).read_bytes())
 print(name,reseal(k))
