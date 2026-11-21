"""Read-only confirmation of a candidate receipt for the third stream with the tree's own code:
the sub-checks prepare() applies to a stream receipt, against the run's reference list, and the row
rule of the stream build under the candidate's list. Reads the job directory; writes nothing."""
import hashlib, importlib, json, sqlite3, sys
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74'); BSE = hx('62656e63686d61726b') + '_scene_exclusions'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
sys.path.insert(0, str(OLD / 's'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
pers = mod(PK + '.r1_persisted')
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
PREP = sorted((OQ / 'p').glob('prepare_*'))[0]
CAND = Path(sys.argv[1]); EXPECT = sys.argv[2] if len(sys.argv) > 2 else None
raw = CAND.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
print('candidate', CAND, 'bytes', len(raw), 'sha256', digest, '| matches the announced sha256:', digest == EXPECT if EXPECT else 'not given')
cand = json.loads(raw)
print('candidate fields:', json.dumps(cand, sort_keys=True))
run = mod(PK + '.carrier_c1_run'); routing = mod(PK + '.carrier_c1_routing')
print('tree functions in use:', run.division_admits.__module__ + '.division_admits', 'from', run.__file__)
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}), pers.scope({digest: str(CAND)}):
    cfg = load(OQ / 'c.json')
    spec = load(pinned(cfg['streams']['pose'])); division = spec['division']
    print('reference list of the run (the mix spec):', json.dumps(division))
    now = load(pinned(cfg['r1_training']['store_parameter']))
    print('fields that differ from the receipt the kit names now:', json.dumps({k: [now.get(k), cand.get(k)] for k in sorted(set(now) | set(cand)) if now.get(k) != cand.get(k)}))

    def predicate(name, receipt):
        schema = routing.ROUTING_SCHEMA if name == 'routing' else 'c1-stream-v1'
        parts = dict(schema_differs=receipt.get('schema') != schema, stream_differs=receipt['stream'] != name,
                     division_not_admitted=not run.division_admits(receipt['division'], division),
                     heldout_overlap_nonzero=receipt.get('heldout_overlap') != 0,
                     wrong_mask_flag=(name == 'pointing' and receipt.get('gt_masks_only') is not True))
        return (name != 'pose' and any(parts.values())), parts
    print('== 1. the kit-level reads of this receipt')
    training = mod(PK + '.r1_training'); rooms = mod(PK + '.r1_rooms')
    pin = {'path': str(CAND), 'sha256': digest}
    try:
        bound = training.store_parameter(pin); print('   store_parameter: pass', json.dumps(bound['database']), bound['count'])
    except Exception as error:
        print('   store_parameter: REFUSE', repr(error))
    print('   added-rows step needs the base store:', 'pass' if cand['database']['sha256'] == rooms.STORE else 'REFUSE')
    print('== 2. lines 536-541 of prepare() with the tree division_admits')
    refuse, parts = predicate('vqa', cand); print('   candidate as written:', 'REFUSE' if refuse else 'pass', json.dumps(parts))
    seen = load(PREP / 'vqa/receipt.json')
    refuse, parts = predicate('vqa', seen); print('   receipt the job built from the present one (control, expect REFUSE):', 'REFUSE' if refuse else 'pass', json.dumps(parts))
    rebuilt = dict(seen, division=cand['division'])
    refuse, parts = predicate('vqa', rebuilt); print('   that receipt with the candidate list pin, as the two builders copy it through:', 'REFUSE' if refuse else 'pass', json.dumps(parts))
    for name in ('pointing', 'routing'):
        refuse, parts = predicate(name, load(PREP / name / 'receipt.json')); print('   ' + name + ' (unchanged):', 'REFUSE' if refuse else 'pass')
    print('== 3. row rule of the stream build under the candidate list (tree scene gate, job filters, the store the build reads)')
    gate = mod(PK + '.scene_division_gate'); Exclusions = mod(PK + '.s1_exclusions').Exclusions; Removals = mod(PK + '.row_removals').Removals
    for label, db in (('store after the added rows', OQ / 'twins/rows.sqlite'),):
        conn = sqlite3.connect('file:' + str(db) + '?mode=ro&immutable=1', uri=True)
        try:
            rows = (json.loads(r) for r, in conn.execute('SELECT row FROM rows ORDER BY i'))
            try:
                counts = gate.check_rows(rows, cand['division'], removals=Removals(cfg.get('remove_files', [])),
                                         scene_filter=Exclusions(cfg['dev_scene_exclusions'], cfg[BSE]), stream='vqa')
                print('   ' + label + ': pass', json.dumps(counts))
            except ValueError as error:
                print('   ' + label + ': REFUSE', str(error)[:400])
        finally:
            conn.close()
    print('   rows the job kept:', seen['count'], '(the build would keep the same rows: the filters do not read the list)')
print('DONE')
