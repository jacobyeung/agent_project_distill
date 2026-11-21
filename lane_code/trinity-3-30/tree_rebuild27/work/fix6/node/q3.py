"""Read-only: both sides of the scene census comparison that refused in the scratch walk, per source
group, from the walk's own log lines, the upstream reports and the pinned reference census."""
import importlib, json, sys
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); BSE = hx('62656e63686d61726b') + '_scene_exclusions'; BW = hx('62656e63686d61726b')
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
sys.path.insert(0, str(OLD / 's'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
pers = mod(PK + '.r1_persisted'); sx = mod(PK + '.s1_exclusions')
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
PREP = sorted((OQ / 'p').glob('prepare_*'))[0]
LOG = Path(sys.argv[1])
current = {}
for line in LOG.read_text(errors='replace').splitlines():
    if line.startswith('{"scene_exclusion"'):
        v = json.loads(line)['scene_exclusion']; current[v['source']] = v
    if line.startswith('{"pose_mix_source"'):
        print('mix line:', line[:300])
fields = ('seen', 'removed', 'retained', 'dev_matches', BW + '_matches', 'overlap_matches')
print('== filter counts the walk printed (rule.sources), per source')
for s, v in current.items():
    print('  ', s, json.dumps({k: v.get(k) for k in fields}), '| other keys', sorted(set(v) - set(fields) - {'source', 'files'}))
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(OQ / 'c.json')
    policy = cfg.get('scene_coverage')
    print('== policy cfg[scene_coverage]:', json.dumps(policy, sort_keys=True)[:3000])
    reference = load(pinned(policy['reference']))
    print('== reference census', policy['reference']['sha256'][:12], 'schema', reference.get('schema'), '| exact_rebuilt_population:', reference.get('exact_rebuilt_population'),
          '| keys', sorted(reference))
    rule = sx.Exclusions(cfg['dev_scene_exclusions'], cfg[BSE])
    print('   rule files:', json.dumps({k: (v or {}).get('sha256', '')[:12] for k, v in rule.files.items()}), '| reference withhold file', json.dumps(reference.get('withhold_file'))[:200])
    spec = load(pinned(cfg['streams']['pose']))
    streams = {'pose': dict(kind='mix', sources=[dict(kind=s['kind'], receipt=s.get('receipt')) for s in spec['sources']])}
    for name in ('pointing', 'routing', 'vqa'):
        streams[name] = dict(receipt=dict(path=str(PREP / name / 'receipt.json'), sha256=prov.sha256(PREP / name / 'receipt.json')))
    previous = sx.upstream(streams, rule)
    print('== upstream reports found for:', sorted(previous))
    groups = {}
    for source in current:
        matches = [name for name in policy['source_map'] if source == name or source.startswith(name + '/')]
        groups.setdefault(matches[0] if len(matches) == 1 else 'UNMATCHED:' + source, []).append(source)
    for name, sources in groups.items():
        if name.startswith('UNMATCHED'):
            print('  ', name); continue
        refs, dev, bench = [], 0, []
        for binding in policy['source_map'][name]:
            value = reference['withheld_training_rows'][binding['source']]
            count = value['rows_withheld']; other = value.get(BW + '_rows_withheld')
            if 'index' in binding:
                count = count[binding['index']]; other = other[binding['index']] if other is not None else None
            dev += count; bench.append(other)
            refs.append(dict(binding=binding, dev_rows=count, other_rows=other, entry_keys=sorted(value), entry={k: value[k] for k in value if k != 'path'}))
        cur = {k: sum(current[s][k] for s in sources) for k in fields}
        earlier = dict.fromkeys(fields, 0)
        for s in sources:
            if s in previous:
                for k, c in sx.totals(previous[s], rule).items():
                    earlier[k] += c
        odev = cur['dev_matches'] + earlier['dev_matches']; obench = cur[BW + '_matches'] + earlier[BW + '_matches']
        rbench = sum(bench) if all(v is not None for v in bench) else None
        verdict = 'DIFFERS' if (odev != dev or obench != rbench) else 'equal'
        print('== group', name, 'parts', sources, '->', verdict)
        print('     observed: dev-list rows', odev, '(now', cur['dev_matches'], '+ upstream', earlier['dev_matches'], ') | test-list rows', obench, '(now', cur[BW + '_matches'], '+ upstream', earlier[BW + '_matches'], ')')
        print('     reference: dev-list rows', dev, '| test-list rows', rbench)
        print('     now', json.dumps(cur), '| upstream', json.dumps(earlier))
        for r in refs:
            print('     reference entry', json.dumps(r, sort_keys=True)[:1500])
print('DONE')
