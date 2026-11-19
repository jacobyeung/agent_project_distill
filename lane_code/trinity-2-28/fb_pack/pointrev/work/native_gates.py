"""Run the tree's own reader and pointing gates over the new store; probe encoder-side token tags/weights."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

TREE = Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
OLD = Path('/scratch/jjyeung/orch_n30/fb_pack/in/pointing/rows_c09bb5ca.sqlite')
NEW = Path('/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite')
OUT = Path('/scratch/jjyeung/orch_n30/fb_pack/pointrev/work/native_gates.json')
sys.path.insert(0, str(TREE))
import torch
torch.set_num_threads(4)
from student_pilot import carrier_c1_run as run, carrier_c1_data as data, r2_contract as contract
from student_pilot import r1_training, row_text_audit
from student_pilot.r0_exclusion import reserve


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# Qwen-style pre-tokenization: single digits, words with a leading space, punctuation runs, newlines.
TOK = re.compile(r'<think>|</think>|<\|im_end\|>|\n+| ?[A-Za-z]+|\d| ?[^\sA-Za-z\d]+| ')


def probe(target):
    # Supervised suffix as the trainer builds it when the generation prompt ends with "<think>\n".
    suffix = target[len('<think>\n'):] + '<|im_end|>'
    pieces = TOK.findall(suffix)
    assert ''.join(pieces) == suffix, suffix
    vocab = {p: i for i, p in enumerate(dict.fromkeys(pieces))}
    inv = {i: p for p, i in vocab.items()}
    labels = torch.tensor([[vocab[p] for p in pieces]])
    tags = data.segment_tags(labels, 'pointing', lambda i: inv[i]).reshape(-1).tolist()
    w = data.pointing_token_weights(labels, lambda i: inv[i], decision=5.0, row_mean=2.0).reshape(-1).tolist()
    seg = Counter(data.STREAM_SEGMENTS[t] for t in tags)
    decision = [pieces[k] for k, v in enumerate(w) if v == max(w)]
    close = pieces.index('</think>')
    think_share = sum(w[:close]) / sum(w)
    return dict(pieces=len(pieces), segments=dict(seg), decision_piece=decision,
                decision_weight=round(max(w), 3), think_weight_share=round(think_share, 3),
                coord_pieces_in_think=[pieces[k] for k in range(close) if data.STREAM_SEGMENTS[tags[k]] == 'pointing_coord'])


def main():
    reader = run.Rows({'streams': {'pointing': {'database': {'path': str(NEW), 'sha256': sha(NEW)}, 'count': 25020}}}, None)
    old = sqlite3.connect(f'file:{OLD}?mode=ro', uri=True)
    stats, fails, probes = Counter(), [], {}
    assert reader.count('pointing') == 25020
    for (i, raw_old, _) in old.execute('SELECT i,row,target FROM rows ORDER BY i'):
        try:
            row, record = reader.row('pointing', i)
            assert record == {}
            contract.validate(row, 'pointing', require_frames=False)
            contract.perception(row, 'pointing', record)
            r1_training.row_check(row, 'pointing')
            row_text_audit.check(row, 'pointing')
            reserve().check(row, 'pointing')
            assert data.single_image_row(row, 'pointing') is False
            assert data.single_image_row(row, 'pointing', training_mode='final', geometry_online={'x': 1}) is False
            stats['pass'] += 1
        except Exception as e:  # noqa: BLE001
            fails.append((i, repr(e)[:200]))
        kind = row['pointing']['kind']
        if kind not in probes or i in (13990, 20416):
            o = json.loads(raw_old)
            probes[f'{i}:{kind}'] = dict(old=probe(o['target']), new=probe(row['target']), new_target=row['target'])
    # Aggregate tag effect over every row (logging segments).
    seg_old, seg_new = Counter(), Counter()
    for (i, raw_old, _) in old.execute('SELECT i,row,target FROM rows ORDER BY i'):
        o = json.loads(raw_old)
        n, _ = reader.row('pointing', i)
        for tgt, acc in ((o['target'], seg_old), (n['target'], seg_new)):
            suffix = tgt[len('<think>\n'):] + '<|im_end|>'
            pieces = TOK.findall(suffix)
            has_digit = any(p.strip().isdigit() for p in pieces)
            acc[(o['pointing']['kind'], 'rows_tagged_null' if not has_digit else 'rows_tagged_coord_format')] += 1
    res = dict(rows=25020, native_pass=stats['pass'], failures=fails[:50], n_failures=len(fails), probes=probes,
               segment_rows_old={f'{a}/{b}': v for (a, b), v in seg_old.items()},
               segment_rows_new={f'{a}/{b}': v for (a, b), v in seg_new.items()})
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != 'probes'}))
    for k, v in probes.items():
        print(k, json.dumps({'old': v['old'], 'new': v['new']}))


if __name__ == '__main__':
    main()
