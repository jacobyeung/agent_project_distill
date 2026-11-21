"""Read-only probe: per-dataset resolution table of the admitted pose rows (bound preparation), by
resolution source; which datasets the lists name; listed-room hits among resolved rows."""
import importlib, json, os, re, sys, time, collections
from pathlib import Path
hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'
KIT = Path(os.environ['Q_KIT']).resolve()
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, file_pin = prov.load, prov.pinned, prov.file_pin
pers = mod(PK + '.r1_persisted')
request = load(NS / 'r.json'); paths = request.pop('_paths')
config = file_pin(Path(sys.argv[1])); LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 0
t0 = time.time()
CAN = re.compile(r'^(scannet|scannetpp|scannetppv2|arkitscenes)/[^/\s]+$')
def strings(value, out):
    if isinstance(value, dict):
        for k, v in value.items(): strings(k, out); strings(v, out)
    elif isinstance(value, list):
        for v in value: strings(v, out)
    elif isinstance(value, str) and CAN.match(value): out.add(value)
with pers.scope(paths):
    cfg = load(pinned(config))
    Rooms = mod(PK + '.r1_rooms').Rooms
    ex = mod(PK + '.s1_exclusions'); rt = mod(PK + '.carrier_c1_routing')
    authority = Rooms(cfg['r1_training']['room_authority'])
    rule = ex.Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    ra = cfg['r1_training']['room_authority']
    for k in sorted(ra):
        p = pinned(ra[k]); print('AUTH', k, p.name, p.stat().st_size, end=' ')
        if p.suffix == '.json':
            v = load(p); print('keys', sorted(v)[:12] if isinstance(v, dict) else type(v).__name__, end='')
        print()
    print('AUTH aliases sample', list(authority.aliases.items())[:3], 'prefixes', collections.Counter(k.split('/')[0] for k in authority.aliases))
    # tier sources of canonical scenes
    tiers = collections.OrderedDict()
    s = set(authority.aliases.values()); tiers['alias_values'] = set(s)
    for k in ('split', 'build'):
        o = set(); strings(load(pinned(ra[k])), o); tiers[k] = o
    tiers['visits'] = {'arkitscenes/' + v for v in authority.visits}
    rooms = authority.r0 | authority.k1
    tiers['rooms'] = {r for r in rooms if CAN.match(r)} | {r + '_%02d' % i for r in rooms if r.startswith('scannet/scene') for i in range(10)}
    tw = cfg['r1_training'].get('direction_twins')
    twin = {}
    if tw:
        av = load(pinned(tw['aliases'])); twin = {k: v['canonical'] for k, v in av['aliases'].items()}
        print('TWIN aliases', len(twin), 'complete', av.get('complete'), 'sample', list(twin.items())[:2], 'prefixes', collections.Counter(k.split('/')[0] for k in twin))
        tiers['twin_values'] = set(twin.values())
    dev = load(pinned(cfg['dev_scene_exclusions'])); o = set(); strings(dev, o); tiers['dev_list'] = o
    ben = load(pinned(cfg['benchmark_scene_exclusions'])); o = set(); strings(ben, o); tiers['bench_list'] = o
    tiers['scannet_namespace'] = {'scannet/scene%04d_%02d' % (a, b) for a in range(807) for b in range(10)}
    rev = {}; tier_of = {}
    for name, cans in tiers.items():
        n = 0
        for c in sorted(cans):
            try: k = rule.key(rt.alias_of(c))
            except Exception: continue
            if k not in rev: rev[k] = c; tier_of[k] = name; n += 1
        print('TIER', name, 'canonicals', len(cans), 'new tokens', n)
    for k, c in twin.items():
        kk = rule.key(k) if '/' in k else k
        if kk not in rev: rev[kk] = c; tier_of[kk] = 'twin_keys'
    listed = rule.names['dev'] | rule.names['benchmark']
    official = rt.load_exclusions(cfg['exclusions'])
    print('LISTS dev', len(rule.names['dev']), 'bench', len(rule.names['benchmark']), 'official', len(official))
    pre = collections.Counter(); vform = collections.Counter()
    for n in listed | {rule.key(x) for x in official if '/' in x and x.split('/')[0].casefold() in rule.aliases}:
        d = n.split('/')[0]; pre[d] += 1; vform[(d, n.split('/', 1)[1][:1] == 'v')] += 1
    print('LISTS dataset prefixes', dict(pre), 'v-form', dict(vform))
    print('ROOMS r0/k1 prefixes', collections.Counter(r.split('/')[0] for r in authority.r0), collections.Counter(r.split('/')[0] for r in authority.k1))
    Rows = mod(PK + '.carrier_c1_run').Rows
    reader = Rows(load(pinned(cfg['preparation'])), None)
    try:
        for stream in ('pose', 'routing', 'pointing', 'vqa'):
            n = reader.count(stream); lim = n if stream == 'pose' and not LIMIT else min(n, LIMIT or 3000)
            tab = collections.defaultdict(collections.Counter); hits = collections.Counter()
            for i in range(lim):
                row = reader.row(stream, i)[0]
                if i == 0: print('ROW0', stream, sorted(row)[:20], row.get('dataset'), row.get('scene'))
                ds = str(row.get('dataset')); t = tab[ds]; t['admitted'] += 1
                st, can, how = authority.status(row)
                if can is None:
                    try: ids = rule.identifiers(row)
                    except Exception: ids = set()
                    hit = [k for k in ids if k in rev]
                    if hit: can = rev[hit[0]]; how = tier_of[hit[0]]
                if can is None: t['unresolved'] += 1; continue
                t['res:' + how] += 1
                try: room = authority.room(can)
                except ValueError: t['room_unresolved'] += 1; continue
                try: ids = rule.identifiers(row)
                except Exception: ids = set()
                names = set(ids) | {rule.key(can), rule.key(room)}
                if names & listed: hits['listed'] += 1
                if room in authority.r0: hits['R0'] += 1
                if room in authority.k1: hits['K1'] += 1
                if official and rt.excluded(official, *(rt.alias_key(x) for x in names)): hits['official'] += 1
            print('TABLE', stream, 'rows', lim, 'of', n, json.dumps({k: dict(v) for k, v in tab.items()}), 'hits', dict(hits), round(time.time() - t0), 's', flush=True)
    finally:
        reader.close()
print('DONE', round(time.time() - t0), 's')
