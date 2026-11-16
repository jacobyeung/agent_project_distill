"""Eligibility-bound (capture, name) data and deterministic decoder frame sampling."""
import hashlib
from pathlib import Path
import random

import numpy as np
from PIL import Image
import torch
from torch.nn import functional as F
from torch.utils.data import Dataset

from .common import read_json, rle_decode, sha256_file, sha256_json
from .eligibility import Gate
from .labels import SCHEMA, MISS_WEIGHT
from .teacher import capture_key
from .vit import frame_size, rgb_tensor


def room_validation(room, fraction=.1):
    return int(hashlib.sha256(('owngrd-room-v1|' + room).encode()).hexdigest()[:16], 16) / 2**64 < fraction


def choose_frames(rows, epoch, item_key, count=4, seed=0):
    rng = random.Random(sha256_json([seed, epoch, item_key]))
    positives = [i for i, r in enumerate(rows) if r.get('pos_inst')]
    chosen = [rng.choice(positives)] if positives else []
    hard = [i for i, r in enumerate(rows) if r['teacher_presence'] > .5 and r['presence'] in (0, None) and i not in chosen]
    rng.shuffle(hard)
    chosen.extend(hard[:max(0, count-len(chosen))])
    rest = [i for i in range(len(rows)) if i not in chosen]
    rng.shuffle(rest)
    chosen.extend(rest[:max(0, count-len(chosen))])
    return sorted(chosen)


def resize_mask(mask, hw):
    return F.interpolate(torch.as_tensor(np.asarray(mask).copy(), dtype=torch.float32)[None, None],
                         hw, mode='nearest')[0, 0]


class GroundingDataset(Dataset):
    def __init__(self, manifest, label_root, teacher_root, split='train', size_hw=(480, 640),
                 validation_fraction=.1, seed=0, decoder_frames=4, verify_frames=True):
        if split not in ('train', 'train_val', 'inspect'):
            raise ValueError('Unknown split')
        self.manifest = read_json(manifest)
        self.gate = Gate(self.manifest['gate_root'])
        receipt = self.gate.admit(self.manifest['captures'])
        if receipt['gate_digest'] != self.manifest['gate_receipt']['gate_digest']:
            raise ValueError('Gate digest differs from the manifest receipt')
        if split == 'train' and any(c['k1_split'] != 'train' for c in self.manifest['captures']):
            raise ValueError('Train manifest contains a heldout capture')
        self.label_root, self.teacher_root = Path(label_root), Path(teacher_root)
        self.size_hw, self.seed, self.decoder_frames = tuple(size_hw), seed, decoder_frames
        self.epoch, self.verify_frames = 0, verify_frames
        self.captures, self.items, pins = [], [], {}
        for c in self.manifest['captures']:
            if split != 'inspect':
                if c['k1_split'] != 'train':
                    continue
                if room_validation(c['room'], validation_fraction) != (split == 'train_val'):
                    continue
            self.gate.admit([c])
            key = capture_key(c['canonical'])
            lp = self.label_root / (key+'.labels.json.gz')
            tp = self.teacher_root / key / 'teacher.json.gz'
            label = read_json(lp)
            done = read_json(tp.parent / 'DONE.json')
            if label['schema'] != SCHEMA or label['canonical'] != c['canonical']:
                raise ValueError('Label schema or capture mismatch')
            thash, ghash = sha256_file(tp), sha256_file(c['gt']['path'])
            if thash != done['teacher_sha256'] or thash != label['teacher_sha256']:
                raise ValueError('Teacher hash mismatch')
            if ghash != c['gt']['sha256'] or ghash != label['gt_sha256']:
                raise ValueError('GT hash mismatch')
            if label['k1_split'] != c['k1_split']:
                raise ValueError('Label split mismatch')
            pins[key] = dict(labels=sha256_file(lp), teacher=thash, gt=ghash)
            ci = len(self.captures)
            self.captures.append(c)
            for n in c['names']:
                if n['name'] not in label['clip_presence'] or label['roles'][n['name']] != n['role']:
                    raise ValueError('Label name or role mismatch')
                self.items.append((ci, n['name']))
        self.pins = pins
        self.label_sha256 = sha256_json(dict(files=pins, manifest=sha256_file(manifest), gate=receipt['gate_digest']))

    def __len__(self):
        return len(self.items)

    def set_epoch(self, epoch):
        self.epoch = int(epoch)

    def __getitem__(self, index):
        return self.get_item(index)

    def get_item(self, index, frame_ids=None):
        ci, name = self.items[index]
        c = self.captures[ci]
        self.gate.admit([c])
        key = capture_key(c['canonical'])
        lp = self.label_root / (key+'.labels.json.gz')
        tp = self.teacher_root / key / 'teacher.json.gz'
        if sha256_file(lp) != self.pins[key]['labels'] or sha256_file(tp) != self.pins[key]['teacher']:
            raise ValueError('Labels or teacher changed during training')
        lab, teacher = read_json(lp), read_json(tp)
        slots = [str(f['slot']) for f in c['frames']]
        if teacher['frame_slots'] != [f['slot'] for f in c['frames']] or teacher['frame_indices'] != [f['index'] for f in c['frames']]:
            raise ValueError('Teacher frame order mismatch')
        if teacher['frame_sha256'] != [f['sha256'] for f in c['frames']] or set(lab['frames']) != set(slots):
            raise ValueError('Teacher frame hashes or label slots mismatch')
        rows = [lab['frames'][s][name] for s in slots]
        chosen = choose_frames(rows, self.epoch, [c['canonical'], name], self.decoder_frames, self.seed)
        if frame_ids is not None:
            chosen = list(frame_ids)
            if len(set(chosen)) != len(chosen) or any(i < 0 or i >= len(rows) for i in chosen):
                raise ValueError('Invalid decoder frame override')
        frames = []
        for f in c['frames']:
            if self.verify_frames and sha256_file(f['path']) != f['sha256']:
                raise ValueError('Frame hash mismatch')
            with Image.open(f['path']) as im:
                frames.append(im.convert('RGB'))
        size = frame_size(frames[0], self.size_hw)
        hw = (size[0]//4, size[1]//4)
        if sha256_file(c['gt']['path']) != self.pins[key]['gt']:
            raise ValueError('GT changed during training')
        decoder = []
        with np.load(c['gt']['path'], allow_pickle=False) as gt:
            if gt['frame_indices'].tolist() != teacher['frame_indices']:
                raise ValueError('GT frame order mismatch')
            for fi in chosen:
                row = rows[fi]
                inst = gt['inst'][fi]
                props = teacher['frames'][slots[fi]]['phrases'][name]['instances']
                targets, hardneg, soft, proposals = [], [], [], []
                for p in row['proposals']:
                    mask = resize_mask(rle_decode(props[p['k']]['mask']), hw)
                    info = dict(mask=mask, instance=p.get('inst'), weight=p.get('weight', 1.),
                                joint=p['joint'], selection_only=p.get('selection_only', False), cls=p['cls'])
                    if p['cls'] == 'POS':
                        targets.append(dict(mask=mask, instance=p['inst'], weight=1., low_resolution=False, cls='POS'))
                    elif p['cls'] == 'HARDNEG':
                        hardneg.append(info)
                    elif p['cls'] == 'DISTILL':
                        soft.append(info)
                    proposals.append(info)
                for instance in row['miss']:
                    targets.append(dict(mask=resize_mask(inst == instance, hw), instance=instance,
                                        weight=MISS_WEIGHT, low_resolution=True, cls='MISS'))
                gt_masks = {i: resize_mask(inst == i, hw) for i in row['gt_visible']}
                decoder.append(dict(targets=targets, hardneg=hardneg, soft=soft, gt_masks=gt_masks,
                                    proposals=proposals, presence=row['presence'], why=row['why'], teacher_presence=row['teacher_presence']))
        target = dict(name=name, role=lab['roles'][name], frames=rows, decoder=decoder,
                      clip_presence=lab['clip_presence'][name],
                      gt_instances=sorted(int(i) for i, label in lab['id_name'].items() if label == name),
                      gt_visible_instances=sorted({i for r in rows for i in r['gt_visible']}))
        return dict(canonical=c['canonical'], name=name, frames=frames, size_hw=size,
                    pixels=rgb_tensor([frames[i] for i in chosen], size), frame_ids=torch.tensor(chosen),
                    target=target, frame_count=len(frames))


def teacher_candidates(target, limit=3):
    """Use triaged instance ids for teacher tracks; unknown ids remain separate proposals."""
    groups = {}
    for f, row in enumerate(target['decoder']):
        for k, p in enumerate(row['proposals']):
            if p['cls'] == 'DISPUTED':
                continue
            key = ('id', p['instance']) if p['instance'] is not None else ('proposal', f, k)
            group = groups.setdefault(key, {})
            if f not in group or p['joint'] > group[f]['joint']:
                group[f] = p
    result = []
    for group in groups.values():
        members = [(f, p['mask']) for f, p in sorted(group.items())]
        scores = [p['joint'] for p in group.values()]
        pres = [target['decoder'][f]['teacher_presence'] for f in group]
        result.append(dict(source='teacher', members=members, weight=min(p['weight'] for p in group.values()),
            native=max(scores) > .5, features=[max(scores), sum(scores)/len(scores),
                len(scores)/max(len(target['decoder']), 1), sum(pres)/len(pres), 0., 1.]))
    return sorted(result, key=lambda c: -c['features'][0])[:limit]
