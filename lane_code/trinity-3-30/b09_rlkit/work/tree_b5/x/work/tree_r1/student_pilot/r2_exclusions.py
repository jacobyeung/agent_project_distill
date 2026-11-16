"""Apply every copied exclusion record, with pinned row-scene coverage."""
import re
from .p3_provenance import load, pinned

ROLES = ('benchmark', 'dev_ids', 'eval_ids', 'frames_gate', 'eval_rooms', 'room_split', 'dev_manifest')
ALIASES = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes', 'scannetpp': 'scannetppv2'}
SEALED = dict(benchmark='3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970',
              dev_ids='951902eea28b6a56e49f1e44761802e05fc4ff25e7ebcb84dfa4bc77fea0a824',
              eval_ids='a5d707acfafeed88a9009cd2fb89f3bfdf53d43fea67b183c589765299e27255',
              frames_gate='eb2957fcaecaf1380aa9b56208902479a21eafcbe1696cc7cd8a41d95a29e352',
              eval_rooms='267efeb1ecf1c1c8329cb4b1809ed05069d9f8d0178a35caba25a9e430a4fd33',
              room_split='246a49f7fefd3c4df4a64eabe4dcce93e0ff8e445644510b510447f0c852fded',
              dev_manifest='e6fe4a7e3c5a9f929d1cb9393915b93020233c0f31d46ded4638cdbd17ccbafb')


def normalize(name):
    corpus, scene = name.split('/', 1)
    return ALIASES.get(corpus, corpus) + '/' + scene


class Exclusions:
    def __init__(self, pins):
        if set(pins) != set(ROLES):
            raise ValueError('All exclusion records are required')
        if {role: pin['sha256'] for role, pin in pins.items()} != SEALED:
            raise ValueError('Exclusion records differ from the sealed build inputs')
        self.pins, self.names, self.qids = pins, {}, {}
        records = {}
        for role, pin in pins.items():
            path = pinned(pin)
            if role in ('dev_ids', 'eval_ids'):
                self.qids[role] = {line.split('\t')[1].strip() for line in path.read_text().splitlines() if line.strip()}
            else:
                records[role] = load(path)
        bench = records['benchmark']
        self.corpora = set(ALIASES.values()) | set(bench.get('other_corpora', {}))
        self.names['benchmark'] = set(bench['scenes'] + bench['physical_groups'])
        self.names['benchmark'].update('/'.join(x) for x in bench['rung1_tokens'])
        self.names['benchmark'].update(c+'/'+s for c, scenes in bench.get('other_corpora', {}).items() for s in scenes)
        rooms = records['eval_rooms']
        self.alias_rooms = {normalize(k): normalize(v) for k, v in rooms['alias_rooms'].items()}
        self.names['eval_rooms'] = set(rooms['evaluation_rooms'])
        self.names['room_split'] = set(s for k, values in records['room_split'].items() if k.endswith('_scenes') for s in values)
        self.names['dev_manifest'] = {s[k] for s in records['dev_manifest']['captures'] for k in ('native', 'scene')}
        self.names = {k: {normalize(x) for x in names} for k, names in self.names.items()}
        self.frames_gate = records['frames_gate']

    def check(self, row, coverage):
        if not isinstance(coverage, dict) or not coverage.get('names') or coverage.get('status') != 'known':
            raise ValueError('Unknown scene overlap: scene_coverage is required')
        names = {normalize(x) for x in coverage['names']}
        if any(name.split('/')[0] not in self.corpora for name in names):
            raise ValueError('Unknown scene corpus overlap')
        key = normalize(row['dataset']+'/'+row['scene'])
        if key not in names:
            raise ValueError('Wrong scene: independent coverage differs')
        for value in (row.get('canonical'), row.get('provenance', {}).get('canonical')):
            if value and normalize(value) not in names:
                raise ValueError('Wrong canonical scene in coverage')
        names.update(self.alias_rooms[n] for n in list(names) if n in self.alias_rooms)
        names.update(re.sub(r'_(\d\d)$', '', n) for n in list(names) if n.startswith('scannet/scene'))
        reasons = [role for role, excluded in self.names.items() if names & excluded]
        ids = {row['qid'], row.get('source_qid'), row.get('provenance', {}).get('source_qid')}
        reasons.extend(role for role, excluded in self.qids.items() if ids & excluded)
        return reasons


def upstream(pins, exclusions):
    result = []
    for pin in pins:
        receipt = load(pinned(pin))
        if receipt.get('exclusions') != exclusions or not isinstance(receipt.get('counts'), dict):
            raise ValueError('Upstream exclusions differ or counts are missing')
        for counts in receipt['counts'].values():
            if (set(counts) != {'seen', 'admitted', 'refused', 'reasons'}
                    or any(type(counts[k]) is not int or counts[k] < 0 for k in ('seen', 'admitted', 'refused'))
                    or counts['seen'] != counts['admitted'] + counts['refused']
                    or not isinstance(counts['reasons'], dict)):
                raise ValueError('Invalid upstream exclusion accounting')
        result.append(dict(pin=pin, receipt=receipt))
    return result
