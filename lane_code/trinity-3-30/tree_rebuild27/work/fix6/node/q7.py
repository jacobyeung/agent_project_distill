"""Read-only probe: can the admitted pose rows be given rooms through the tiered alias map that the
kit classifier already uses for unresolved rows of the third stream, and if so, do any lie in K1 or
R0 rooms. Scene names are read with SQL from the two pose stores; nothing is written."""
import importlib, json, os, sqlite3, sys
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
CONFIG = Path(sys.argv[1]); ORDER = Path(sys.argv[2])
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(pinned(file_pin(CONFIG)))
    Binding = mod(PK + '.r1_direction_twins').Binding
    binding = Binding(cfg); strict = binding.strict
    spec = load(pinned(cfg['streams']['pose']))
    order = json.loads(ORDER.read_text())
    wanted = {}
    for source, index in order:
        wanted.setdefault(source, set()).add(index)
    rows_by_scene = Counter()
    for number, src in enumerate(spec['sources']):
        rec = load(pinned(src['receipt']))
        conn = sqlite3.connect('file:' + str(pinned(rec['database'])) + '?mode=ro&immutable=1', uri=True)
        keep = wanted.get(number, set())
        for index, ds, scene in conn.execute("SELECT i, json_extract(row,'$." + DS + "'), json_extract(row,'$.scene') FROM rows"):
            if index in keep:
                rows_by_scene[(ds, scene)] += 1
        conn.close()
    print('admitted pose rows', sum(rows_by_scene.values()), '| scenes', len(rows_by_scene), '| by set', dict(Counter(ds for (ds, _), n in rows_by_scene.items() for _ in range(n))))
    tally, rooms = Counter(), {k: Counter() for k in ('k1', 'r0')}
    for (ds, scene), n in rows_by_scene.items():
        row = {DS: ds, 'scene': scene}
        status, canonical, how = strict.status(row)
        if status == 'unresolved':
            try:
                canonical, how2 = binding.tiered.canonical(row)
                how = 'tiered:' + str(how2)
            except Exception as error:
                canonical = None; how = 'tiered raises ' + type(error).__name__
        room = None
        if canonical:
            try:
                room = strict.room(canonical)
            except ValueError:
                how = str(how) + ', no room'
        if room is None:
            cls = 'no room'
        elif room in strict.k1:
            cls = 'K1 held-out room'; rooms['k1'][room] += n
        elif room in strict.r0:
            cls = 'R0 room'; rooms['r0'][room] += n
        else:
            cls = 'other room'
        tally[(cls, 'rows')] += n; tally[(cls, 'scenes')] += 1; tally[('how ' + str(how).partition(':')[0] + ' ' + str(ds), 'rows')] += n
    for key in sorted(tally):
        print('   %-44s %-7s %d' % (key[0], key[1], tally[key]))
    for k, c in rooms.items():
        print(k, 'rooms with admitted pose rows (' + str(len(c)) + '):', json.dumps(dict(c.most_common(12))))
print('DONE')
