"""Expand the fixed pilot; admit new hashes only from the frame-parity gate."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def membership(m):
    return [(c['canonical'], c['room'], c['k1_split']) for c in m['captures']]


def build(template, missing, parity=None):
    m = copy.deepcopy(template)
    need = {r['canonical']: r['new_indices'] for r in missing}
    total_new = sum(map(len, need.values()))
    if parity is not None:
        if (parity.get('pass_') is not True or parity.get('n_failures') != 0
                or parity.get('pinned_checked') != sum(len(c['dense_frames']) for c in m['captures'])
                or parity.get('new_frames') != total_new
                or set(parity['new']) != set(need)):
            raise ValueError('Incomplete or failed frame parity')
    unresolved = []
    for c in m['captures']:
        frames = {f['index']: f for f in c['dense_frames']}
        additions = need.get(c['canonical'], [])
        supplied = {} if parity is None else {f['index']: f['sha256'] for f in parity['new'].get(c['canonical'], [])}
        if parity is not None and set(supplied) != set(additions):
            raise ValueError('New index set differs')
        for index in additions:
            if index in frames:
                raise ValueError('New index overlaps existing pin')
            h = supplied.get(index)
            if parity is not None and not re.fullmatch('[0-9a-f]{64}', h or ''):
                raise ValueError('Invalid new frame hash')
            frames[index] = dict(index=index, sha256=h, path=None)
            if h is None:
                unresolved.append(dict(canonical=c['canonical'], index=index))
        c['dense_frames'] = [frames[i] for i in sorted(frames)]
        if len(c['dense_frames']) != 64:
            raise ValueError('Require exactly 64 dense frames')
        for f in c['dense_frames']:
            h = f['sha256']
            f['path'] = f'/scratch/jjyeung/k1_frames/{h[:2]}/{h}.png' if h else f"/scratch/jjyeung/k1_frames/UNRESOLVED/{c['canonical'].replace('/', '_')}_{f['index']}.png"
        c['anchor_slots'] = [[f['index'] for f in c['dense_frames']].index(i) for i in c['anchor_indices']]
        si = c['model_row']['student_input']
        si['frames'] = [{k: c['dense_frames'][i][k] for k in ('path', 'sha256')} for i in c['anchor_slots']]
    s = m['gpu']
    s['tower_weights']['path'] = '/scratch/jjyeung/k1/g3t/model.safetensors'
    s['tower_config']['path'] = '/scratch/jjyeung/k1/g3t/config.json'
    s['sam_checkpoint']['path'] = '/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt'
    s['sam_source'] = '/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src'
    s['sam_receipt']['path'] = str(KIT / 'native_kit/vendor_sam/vendor/SAM3_RECEIPT.json')
    m['inventory']['path'] = str(KIT / 'out/CAPTURES.json')
    m['unresolved_dense_sources'] = unresolved
    m['production_ready'] = False
    m['frame_staging_authorized'] = False
    m['k1a_frame_parity'] = None if parity is None else dict(sha256=digest(parity), pinned_checked=parity['pinned_checked'], new_frames=total_new)
    return m


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template', required=True)
    p.add_argument('--missing', required=True)
    p.add_argument('--parity')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    load = lambda name: json.loads(Path(name).read_text())
    m = build(load(a.template), load(a.missing), load(a.parity) if a.parity else None)
    Path(a.out).write_text(json.dumps(m, indent=2) + '\n')


if __name__ == '__main__':
    main()
