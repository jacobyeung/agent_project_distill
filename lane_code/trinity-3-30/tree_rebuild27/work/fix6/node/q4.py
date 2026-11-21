"""Read-only: where the scene census and the filter counts part ways, for the first pose source and
for the routing stream. Uses the tree's own row-selection and scene-rule functions."""
import importlib, json, sqlite3, sys
from collections import Counter
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); BW = hx('62656e63686d61726b'); BSE = BW + '_scene_exclusions'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
sys.path.insert(0, str(OLD / 's'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
pers = mod(PK + '.r1_persisted'); sx = mod(PK + '.s1_exclusions'); pm = mod(PK + '.c1_pose_mix')
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
PREP = sorted((OQ / 'p').glob('prepare_*'))[0]
F = ('seen', 'removed', 'retained', 'dev_matches', BW + '_matches', 'overlap_matches')


def show(report, indent, label):
    for source, counts in report.get('sources', {}).items():
        print(' ' * indent + label + ' source ' + source + ': ' + json.dumps({k: counts.get(k) for k in F}))
    for name, nested in report.get('upstream', {}).items():
        show(nested, indent + 3, 'upstream[' + name + ']')


with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(OQ / 'c.json')
    rule = sx.Exclusions(cfg['dev_scene_exclusions'], cfg[BSE])
    rebuild = load(pinned(cfg['r2_scene_rebuild']))
    print('== census record', cfg['r2_scene_rebuild']['path'], 'keys', sorted(rebuild))
    print('   rows_withheld', json.dumps(rebuild.get('rows_withheld')))
    for name, pin in rebuild['receipts'].items():
        r = load(pinned(pin))
        print('   census receipt', name, 'count kept', r.get('count'), '| scene_rebuild', json.dumps({k: (v if not isinstance(v, dict) else v.get('path', v)) for k, v in r.get('scene_rebuild', {}).items()})[:500])
        show(r['source_scene_exclusions'], 6, 'census')
    pool = load(pinned(rebuild['pool_selection']))
    print('   census pool selection keys', sorted(pool)[:30]); show(pool['source_scene_exclusions'], 6, 'census pool')
    print('== routing receipt the job built: its scene report')
    rr = load(PREP / 'routing/receipt.json'); show(rr['source_scene_exclusions'], 3, 'routing')
    print('   routing receipt count', rr['count'], '| removals entries', len(rr.get('removals', [])), '| source', json.dumps(rr.get('source'))[:200])
    print('== first pose source: every row of its store, by the mix row rule and the scene rule')
    spec = load(pinned(cfg['streams']['pose'])); src = spec['sources'][0]; rec = load(pinned(src['receipt']))
    print('   source receipt schema', rec.get('schema'), 'count', rec.get('count'), 'frame_prefix', src.get('frame_prefix'), '| store', rec['database']['sha256'][:12])
    dense = mod(PK + '.carrier_c1_sweep').dense_pose_row
    tally = Counter()
    conn = sqlite3.connect('file:' + str(pinned(rec['database'])) + '?mode=ro&immutable=1', uri=True)
    for index, row, target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
        row, target = json.loads(row), json.loads(target)
        d = bool(dense(row, target)); sel = bool(pm._row_selected(row, target, src['frame_prefix']))
        m = rule.matched(rule.identifiers(row))
        key = ('mix selects' if sel else ('dense, other frame prefix' if d else 'not dense'))
        tally[key + ' | rows'] += 1; tally[key + ' | dev-list rows'] += int(m['dev']); tally[key + ' | test-list rows'] += int(m[BW])
    conn.close()
    for key in sorted(tally):
        print('   %-48s %d' % (key, tally[key]))
print('DONE')
