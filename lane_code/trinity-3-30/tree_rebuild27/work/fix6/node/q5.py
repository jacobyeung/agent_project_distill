"""Read-only: what the room authority answers for the first rows of each pose source, and whether
P's own preparation carried an exact census."""
import importlib, json, os, sqlite3, sys
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); DS = hx('64617461736574')
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT']).resolve()
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
pers = mod(PK + '.r1_persisted')
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(OQ / 'c.json')
    Rooms = mod(PK + '.r1_rooms').Rooms
    authority = Rooms(cfg['r1_training']['room_authority'])
    spec = load(pinned(cfg['streams']['pose']))
    for number, src in enumerate(spec['sources']):
        rec = load(pinned(src['receipt']))
        conn = sqlite3.connect('file:' + str(pinned(rec['database'])) + '?mode=ro&immutable=1', uri=True)
        print('== pose source', number, rec.get('schema'))
        for index, raw in conn.execute('SELECT i,row FROM rows ORDER BY i LIMIT 3'):
            row = json.loads(raw)
            try:
                answer = authority.status(row)
            except Exception as error:
                answer = 'raises ' + repr(error)
            print('   row', index, 'keys', sorted(row)[:25])
            print('      set', row.get(DS), 'scene', row.get('scene'), '| canonical', row.get('canonical'), '| routing', json.dumps(row.get('routing'))[:200],
                  '| provenance', json.dumps(row.get('provenance'))[:300])
            print('      authority.status ->', str(answer)[:300])
        conn.close()
    try:
        from sv import classifier
        classify = classifier(cfg)
        rec = load(pinned(spec['sources'][0]['receipt']))
        conn = sqlite3.connect('file:' + str(pinned(rec['database'])) + '?mode=ro&immutable=1', uri=True)
        (raw,) = conn.execute('SELECT row FROM rows ORDER BY i LIMIT 1').fetchone(); conn.close()
        try:
            print('== kit classifier on that first pose row ->', classify(json.loads(raw), 'pose'))
        except Exception as error:
            print('== kit classifier on that first pose row raises', repr(error))
    except Exception as error:
        print('classifier build failed', repr(error))
    print('== P preparation: was the census exact there?')
    try:
        pprep = load(pinned(cfg['r1_training']['p_run']['preparation']))
        cov = (pprep.get('scene_filter_report') or {}).get('coverage') or {}
        pol = cov.get('policy') or {}
        print('   P coverage status', cov.get('status'), '| policy keys', sorted(pol), '| comparison', cov.get('comparison'))
        if pol.get('reference'):
            ref = load(pinned(pol['reference']))
            print('   P reference schema', ref.get('schema'), '| exact_rebuilt_population:', ref.get('exact_rebuilt_population'), '| keys', sorted(ref))
            for name, rec in (cov.get('sources') or {}).items():
                print('   P group', name, 'observed', rec.get('observed_dev_matches'), rec.get('observed_' + hx('62656e63686d61726b') + '_matches'), 'reference', rec.get('reference_dev_rows'), rec.get('reference_' + hx('62656e63686d61726b') + '_rows'))
    except Exception as error:
        print('   P side read failed', repr(error))
print('DONE')
