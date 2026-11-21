"""Read-only: what the admitted routing rows are that the kit census flags as lying in K1 held-out
rooms. Uses the tree's Rows reader on the bound scratch preparation and the kit's classifier."""
import importlib, json, os, sys
from collections import Counter
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); DS = hx('64617461736574')
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT']).resolve()
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's')); sys.path.insert(0, str(KIT / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, file_pin = prov.load, prov.pinned, prov.file_pin
pers = mod(PK + '.r1_persisted')
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
CONFIG = Path(sys.argv[1])
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(pinned(file_pin(CONFIG)))
    run = mod(PK + '.carrier_c1_run'); Rooms = mod(PK + '.r1_rooms').Rooms
    from sv import classifier
    classify = classifier(cfg); authority = Rooms(cfg['r1_training']['room_authority'])
    print('authority K1 rooms:', len(authority.k1), '| R0 rooms:', len(authority.r0))
    reader = run.Rows(load(pinned(cfg['preparation'])), None)
    total = reader.count('routing')
    by = {k: Counter() for k in ('type', 'set', 'source', 'room', 'how', 'form')}
    hits, examples = 0, []
    try:
        for i in range(total):
            row, _ = reader.row('routing', i)
            flags = classify(row, 'routing')
            if not flags['K1_heldout']:
                continue
            hits += 1
            status, canonical, how = authority.status(row)
            room = authority.room(canonical) if canonical else None
            routing = row.get('routing') or {}
            provenance = row.get('provenance') if isinstance(row.get('provenance'), dict) else {}
            source = str(row.get('source') or provenance.get('source') or provenance.get(hx('73747265616d')) or routing.get('source') or 'not recorded')
            by['type'][str(routing.get('question_type', row.get('question_type')))] += 1
            by['set'][str(row.get(DS))] += 1; by['source'][source[:60]] += 1; by['room'][str(room)] += 1; by['how'][str(how)] += 1
            by['form'][str(routing.get('form'))] += 1
            if len(examples) < 3:
                examples.append(dict(i=i, qid=row.get('qid'), scene=str(row.get(DS)) + '/' + str(row.get('scene')), canonical=canonical, room=room,
                                     type=routing.get('question_type'), keys=sorted(row)[:20], routing_keys=sorted(routing)[:20], provenance_keys=sorted(provenance)[:20]))
    finally:
        reader.close()
    print('admitted routing rows', total, '| flagged K1_heldout', hits)
    for k, c in by.items():
        print('by', k, '(' + str(len(c)) + '):', json.dumps(dict(c.most_common(14))))
    for e in examples:
        print('example', json.dumps(e, default=str)[:700])
print('DONE')
