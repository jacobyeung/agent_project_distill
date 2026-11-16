"""Scene-eligibility gate for every manifest the head's teacher pass, labels or training reads.

A capture may enter only when (1) the K1 pool inventory (kit_k1a CAPTURES.json) marks it eligible and (2) no
exclusion authority names its scene, its room or any of its anonymized scene tokens. Authorities (pinned by
sha256 in AUTHORITIES): benchmark exclusions v2, the dev-S1 withhold list and the 152 dev-S1 mask captures, the
80 withheld rooms, the own-room gate (evaluation, qualification, tuning, clean and frames32 rooms) and the dev
ROOM_SPLIT (every scene list and overlapping room). Rooms: ScanNet scene without _NN, ScanNet++ scene, ARKit venue.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import sha256_file, sha256_json

AUTHORITIES = {
    'BENCH_SCENE_EXCLUSIONS_v2.json': '3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970',
    'CAPTURES.json': 'dde9aae955f4e8d25419b0b6237a514ab0b392add25dd0dd29a02a424a7c0c53',
    'DEVS1_MANIFEST.json': 'e6fe4a7e3c5a9f929d1cb9393915b93020233c0f31d46ded4638cdbd17ccbafb',
    'EVAL_ROOMS.json': '267efeb1ecf1c1c8329cb4b1809ed05069d9f8d0178a35caba25a9e430a4fd33',
    'ROOM_SPLIT.json': '246a49f7fefd3c4df4a64eabe4dcce93e0ff8e445644510b510447f0c852fded',
    'WITHHELD_ROOMS_80.json': '634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed',
    'dev_scene_exclusions_d0.json': 'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5',
}
PREFIX = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes', 'scannetppv2': 'scannetpp',
          'scannet': 'scannet', 'scannetpp': 'scannetpp', 'arkitscenes': 'arkitscenes'}


def canon(key: str) -> str:
    ds, rest = key.split('/', 1)
    if ds not in PREFIX:
        raise ValueError(f'Unknown dataset prefix in {key!r}')
    return f'{PREFIX[ds]}/{rest}'


def scan_room(scene: str) -> str | None:
    """Room of a ScanNet scene id; other datasets need an explicit room."""
    ds, s = scene.split('/', 1)
    if ds == 'scannet' and len(s) == 12 and s[9] == '_':
        return f'scannet/{s[:9]}'
    if ds == 'scannetpp':
        return scene
    return None


class Gate:
    def __init__(self, root):
        root = Path(root)
        self.pins = {}
        for name, expected in AUTHORITIES.items():
            got = sha256_file(root / name)
            if got != expected:
                raise ValueError(f'Authority {name} changed: {got} != {expected}')
            self.pins[name] = got
        load = lambda n: json.loads((root / n).read_text())
        bench, caps, devm = load('BENCH_SCENE_EXCLUSIONS_v2.json'), load('CAPTURES.json'), load('DEVS1_MANIFEST.json')
        evalr, split = load('EVAL_ROOMS.json'), load('ROOM_SPLIT.json')
        withheld, devx = load('WITHHELD_ROOMS_80.json'), load('dev_scene_exclusions_d0.json')
        rooms, scenes, tokens = {}, {}, {}

        def add(store, key, why):
            store.setdefault(key, set()).add(why)

        for s in bench['scenes']:
            add(scenes, canon(s), 'benchmark_v2')
            add(rooms, canon(bench['members'][s]['group']), 'benchmark_v2')
        for g in bench['physical_groups']:
            add(rooms, canon(g), 'benchmark_v2')
        for ds, tok in bench['rung1_tokens']:
            add(tokens, tok, 'benchmark_v2')
        # dev_scene_exclusions_d0 = D0's withhold list: the dev-S1 rooms plus the 80 withheld rooms.
        for g in devx['physical_groups']:
            add(rooms, canon(g), 'd0_withhold')
        for native, alist in devx['aliases'].items():
            for c in devx['canonical'][native]:
                add(scenes, canon(c), 'd0_withhold')
            for a in alist:
                if a.split('/', 1)[1].startswith('v'):
                    add(tokens, a.split('/', 1)[1], 'd0_withhold')
        for c in devm['captures']:
            add(scenes, canon(c['scene']), 'dev_s1_capture')
            r = scan_room(canon(c['scene']))
            if r:
                add(rooms, r, 'dev_s1_capture')
        for r in withheld['rooms']:
            add(rooms, canon(r), 'withheld_80')
        for r, alist in withheld['aliases'].items():
            for a in alist:
                rest = a.split('/', 1)[1]
                if rest.startswith('v'):
                    add(tokens, rest, 'withheld_80')
                else:
                    add(scenes, canon(a), 'withheld_80')
        for key in ('evaluation_rooms', 'qualification_rooms'):
            for r in evalr[key]:
                add(rooms, canon(r), key)
        for key in ('clean_scenes', 'tuning_scenes', 'frames32_scenes'):
            for s in evalr[key]:
                add(scenes, canon(s), key)
                r = scan_room(canon(s))
                if r:
                    add(rooms, r, key)
        for key in ('tuning_scenes', 'legacy_read_scenes', 'room_disjoint_scenes', 'overlapping_read_scenes'):
            for s in split[key]:
                add(scenes, canon(s), 'dev_room_split')
                add(rooms, scan_room(canon(s)), 'dev_room_split')
        for r in split['overlapping_rooms']:
            add(rooms, canon(r), 'dev_room_split')
        self.rooms, self.scenes, self.tokens = rooms, scenes, tokens
        self.pool = {c['canonical']: c for c in caps['captures']}
        self.digest = sha256_json({'pins': self.pins, 'rooms': {k: sorted(v) for k, v in rooms.items()},
                                   'scenes': {k: sorted(v) for k, v in scenes.items()},
                                   'tokens': {k: sorted(v) for k, v in tokens.items()}})

    def reasons(self, canonical: str, room: str | None = None, aliases=()) -> list[str]:
        """Every reason this capture must stay out; an empty list admits it."""
        canonical = canon(canonical)
        why = set()
        entry = self.pool.get(canonical)
        if entry is None:
            why.add('not_in_pool_inventory')
        else:
            if not entry['eligible']:
                why.update('pool:' + r for r in entry['reasons'])
            if room is not None and canon(room) != canon(entry['room']):
                why.add('room_disagrees_with_inventory')
            room = entry['room']
            aliases = list(aliases) + list(entry.get('aliases', []))
        rooms = {canon(room)} if room else set()
        derived = scan_room(canonical)
        if derived:
            rooms.add(derived)
        if not rooms:
            why.add('room_unknown')
        why.update(self.scenes.get(canonical, ()))
        for r in rooms:
            why.update(self.rooms.get(r, ()))
        for a in aliases:
            why.update(self.tokens.get(a, ()))
        return sorted(why)

    def admit(self, captures):
        """Refuse a manifest that holds any excluded capture; return the gate receipt."""
        bad = {}
        for c in captures:
            r = self.reasons(c['canonical'], c.get('room'), c.get('aliases', ()))
            if r:
                bad[c['canonical']] = r
        if bad:
            raise ValueError(f'Eligibility gate refuses {len(bad)} captures: ' + json.dumps(dict(list(bad.items())[:5])))
        return {'gate_digest': self.digest, 'authorities': self.pins, 'captures': len(captures),
                'manifest_sha256': sha256_json(sorted(c['canonical'] for c in captures))}
