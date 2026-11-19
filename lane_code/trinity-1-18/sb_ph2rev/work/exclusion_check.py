"""Independent check of the phrase kit's 209 captures / 1,037 rows against the five pinned exclusion lists."""
import hashlib, json, sys
from pathlib import Path

EX = Path('/scratch/jjyeung/orch_n30/sb_ph2rev/work/extract')
STAGED = EX/'payload/files'
TOKEN = {'scannet': 'd1', 'scannetpp': 'd2', 'arkitscenes': 'd3'}
LISTS = dict(
    R0=('/scratch/jjyeung/orch_n30/b10_reserve/out/R0_ROOMS.txt', 'bdb5d402'),
    dev_S1=('/scratch/jjyeung/orch_n30/sb_rowOI/inputs/dev_s1.json', '969cdb56'),
    BENCH_v2=('/scratch/jjyeung/orch_n30/sb_cntrev/k1/auth/BENCH_SCENE_EXCLUSIONS_v2.json', '3119aa4a'),
    withheld_80=('/scratch/jjyeung/orch_n30/sb_cntrev/k1/auth/WITHHELD_ROOMS_80.json', '634820b4'),
    K1_heldout=('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/build17/inputs/'
                '27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390.json', '4d4736cf'))


def names(kind, raw, text):
    if kind == 'R0':
        return set(text.split())
    if kind == 'dev_S1':
        out = set(raw['rooms']) | set(raw['physical_groups']) | set(raw['natives'])
        for d in (raw['aliases'], raw['canonical']):
            for k, v in d.items():
                out |= {k, *v}
        return out
    if kind == 'BENCH_v2':
        return set(raw['scenes']) | set(raw['physical_groups']) | {'/'.join(t) for t in raw['rung1_tokens']} | {m['group'] for m in raw['members'].values()}
    if kind == 'withheld_80':
        out = set(raw['rooms'])
        for k, v in raw['aliases'].items():
            out |= {k, *v}
        return out
    held = [c for c in raw['teacher_k1']['captures'] if c['k1_split'] != 'train']
    return {c['canonical'] for c in held} | {c['room'] for c in held} | {a for c in held for a in c.get('aliases', [])}


def main():
    pinned = json.loads((STAGED/'scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json').read_text())
    ids = set((STAGED/'scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt').read_text().split())
    caps = [c for c in pinned['captures'] if any(r['id'] in ids for r in c['rows'])]
    rows = {c['canonical']: [r['id'] for r in c['rows'] if r['id'] in ids] for c in caps}
    out = dict(captures=len(caps), rows=sum(map(len, rows.values())), lists={})
    for kind, (path, pin) in LISTS.items():
        data = Path(path).read_bytes(); sha = hashlib.sha256(data).hexdigest()
        raw = None if kind == 'R0' else json.loads(data)
        pin_ok = (raw['teacher_k1']['sha256'][:8] == pin) if kind == 'K1_heldout' else sha.startswith(pin)
        ex = names(kind, raw, data.decode() if kind == 'R0' else None)
        if kind == 'R0':
            r0 = json.loads(Path(LISTS['K1_heldout'][0]).read_text())['r0_scenes']
            ex |= set(r0['rooms']) | set(r0['captures'])
        def forms(c):
            ds, cap = c['canonical'].split('/', 1); rds, rn = c['room'].split('/', 1)
            return {c['canonical'], f'{TOKEN[ds]}/{cap}', c['room'], f'{TOKEN[rds]}/{rn}'}
        hits = sorted(c['canonical'] for c in caps if forms(c) & ex)
        out['lists'][kind] = dict(sha256=sha, pin=pin, pin_ok=pin_ok, names=len(ex), hit_captures=hits, hit_rows=sum(len(rows[h]) for h in hits))
    sys.path.insert(0, str(EX/'sb_mask_phrase'))
    kit_withheld = sorted('scannet/'+c for c in ('scene0201_02', 'scene0478_00', 'scene0478_01', 'scene0614_02', 'scene0692_03'))
    out['kit_hardcoded_withheld_equals_list_hits'] = kit_withheld == out['lists']['withheld_80']['hit_captures']
    out['decision_rows'] = out['rows'] - out['lists']['withheld_80']['hit_rows']
    Path('/scratch/jjyeung/orch_n30/sb_ph2rev/work/EXCLUSION_CHECK.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != 'lists'}),
          {k: (v['pin_ok'], len(v['hit_captures']), v['hit_rows']) for k, v in out['lists'].items()})


if __name__ == '__main__':
    main()
