"""Paired out-of-room selector refits, evaluated through the serving socket."""
import collections
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import selrefit as B
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
INPUTS = ROOT / 'inputs'
SEED = 20261116
BOOT_SEED = 20261119


def pin_code():
    B.pin_code()
    B.read(ROOT / 'selrefit2.py')


def copy_input(source, dest, expected=None):
    data = B.read(source)
    if expected is not None:
        assert hashlib.sha256(data).hexdigest() == expected, str(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    B.read(dest)
    return dest


def prepare():
    d = B.js(ROOT / 'prior/out/TRAIN_DATA.json')
    copy_input(B.SEL / 'train_selector.py', INPUTS / 'code/train_selector.py')
    copy_input(B.SEL / 'selector_head.py', INPUTS / 'code/selector_head.py')
    copy_input(B.SEL / 'common.py', INPUTS / 'code/common.py')
    copy_input(B.SEL / 'work/run_iso/selector_head.json', INPUTS / 'recipe.json')
    copy_input(B.SOURCE / 'train_labels.json', INPUTS / 'train_labels.json')
    copy_input(B.ROWSETS / 'K1_TRAIN_1037.txt', INPUTS / 'K1_TRAIN_1037.txt')
    copy_input(B.ROWSETS / 'K1_CAPTURES_TRAIN_239.txt', INPUTS / 'K1_CAPTURES_TRAIN_239.txt')
    allowed = set(B.read(INPUTS / 'K1_CAPTURES_TRAIN_239.txt').decode().splitlines())
    assert {c['canonical'] for c in d['captures']} == allowed
    assert all(c['k1_split'] == 'train' for c in d['captures'])
    rooms = sorted({c['room'] for c in d['captures']})
    random.Random(SEED).shuffle(rooms)
    assert d['folds'] == {room: i % 5 for i, room in enumerate(rooms)}
    assert B.CFG == dict(epochs=15, hidden=32, lr=.003, name_mode='none', wd=.001, n_hash=4096)
    rows = {'S': [], 'V': []}
    missing, common, coverage = [], [], []
    prior_rows = collections.defaultdict(list)
    for row in d['rows']:
        prior_rows[row['capture']].append(row)
    for c in d['captures']:
        cap = c['canonical']; name = cap.replace('/', '__') + '.json.gz'
        source_v = B.R.TABLES / name
        target_v = copy_input(source_v, INPUTS / 'tables/V' / name, d['input_sha256'][str(source_v)])
        v = B.table(target_v)
        assert v['capture'] == cap and v['room'] == c['room'] and v['split'] == 'train'
        vrows = B.joined(v)
        assert vrows == prior_rows[cap]
        source_s = B.SEL / 'data/caps_iso' / name
        present = source_s.exists()
        coverage.append(dict(capture=cap, room=c['room'], fold=d['folds'][c['room']], s4_g1_available=present))
        if not present:
            missing.append(dict(capture=cap, status='MISSING', expected=str(source_s)))
            continue
        common.append(cap)
        target_s = copy_input(source_s, INPUTS / 'tables/S' / name, d['input_sha256'][str(source_s)])
        s = B.table(target_s)
        assert s['capture'] == cap
        s['room'] = c['room']
        rows['S'].extend(B.joined(s)); rows['V'].extend(vrows)
    assert len(missing) == 24 and len(common) == 215
    for arm in rows:
        assert all(len(r['x']) == 58 and r['capture'] in common for r in rows[arm])
    pin_code()
    B.write(OUT / 'TRAIN_DATA.json', dict(captures=d['captures'], folds=d['folds'], seed=SEED,
        common_captures=common, missing_s4_g1=missing, coverage=coverage, rows=rows,
        prior_input_sha256=d['input_sha256'], config=B.CFG,
        training_policy='Both arms fit only captures with both tables; secondary evaluation adds the missing-table captures without changing coefficients.'))
    B.status(f'Preparation complete: {len(common)} shared training captures and {len(missing)} missing S4/G1 tables. Both arms use the copied physical-room folds. Inputs, exact missing paths, and hashes are recorded in out/TRAIN_DATA.json; fitting is next.')
    print('PREPARED', json.dumps(dict(captures=len(d['captures']), common=len(common), missing=len(missing), rows={a: len(r) for a,r in rows.items()})), flush=True)


def train():
    d = B.js(OUT / 'TRAIN_DATA.json')
    gs = {arm: B.T.groups(rows, {}) for arm, rows in d['rows'].items()}
    summaries = []
    for k in range(5):
        train_caps = sorted(c for c in d['common_captures'] if d['folds'][next(x['room'] for x in d['captures'] if x['canonical']==c)] != k)
        val_rooms = {c['room'] for c in d['captures'] if d['folds'][c['room']] == k}
        for arm in ['S', 'V']:
            tr = [g for g in gs[arm] if d['folds'][g['room']] != k]
            te = [g for g in gs[arm] if d['folds'][g['room']] == k]
            train_rooms = {g['room'] for g in tr}
            assert train_rooms.isdisjoint(val_rooms)
            assert {r['capture'] for g in tr for r in g['rows']} <= set(train_caps)
            stem = f'{arm}_fold_{k}'
            started = time.monotonic()
            h = B.T.fit(tr, B.CFG, seed=SEED)
            pin_code()
            sha = B.save_head(h, stem, dict(arm=arm, fold=k, training_objects=len(tr), validation_objects=len(te),
                training_captures=train_caps, training_rooms=sorted(train_rooms), validation_rooms=sorted(val_rooms),
                room_overlap=0, training_candidates=sum(len(g['rows']) for g in tr),
                objective='candidate BCE plus null BCE, normalized by candidate+null count per batch', batch_size=16))
            summaries.append(dict(arm=arm, fold=k, weights_sha256=sha, training_objects=len(tr), validation_objects=len(te), seconds=time.monotonic()-started))
            B.status(f'Fitting complete for {len(summaries)}/10 models. Arm {arm}, fold {k} has {len(tr)} training objects; its validation rooms are disjoint. Both arms use the fixed recipe and shared capture set. No held-out data has been read.')
            print('FIT', json.dumps(summaries[-1]), flush=True)
    B.write(OUT / 'FIT.json', dict(folds=summaries, config=B.CFG, seed=SEED, batch_size=16, room_leakage=False, config_search=False))


def score():
    d = B.js(OUT / 'TRAIN_DATA.json')
    B.js(OUT / 'FIT.json')
    ids = set(B.read(INPUTS / 'K1_TRAIN_1037.txt').decode().splitlines())
    labels = {r['id']: r for r in B.js(INPUTS / 'train_labels.json')['rows']}
    heads = {(arm,k): B.custom_head(f'{arm}_fold_{k}') for k in range(5) for arm in ['S','V']}
    pin_code()
    common_pins = dict(B.PINS)
    dest = OUT / 'cv_captures'; dest.mkdir(exist_ok=True)
    seen = set()
    for i,c in enumerate(d['captures']):
        B.PINS.clear(); B.PINS.update(common_pins)
        k = d['folds'][c['room']]
        p = dest / (c['canonical'].replace('/', '__') + '.json')
        if p.exists():
            rec = B.js(p)
            assert rec['code_sha256'] == common_pins[str(ROOT/'selrefit2.py')]
            assert rec['input_sha256'][str(OUT/'FIT.json')] == common_pins[str(OUT/'FIT.json')]
        else:
            started = time.monotonic()
            tab = B.table(INPUTS / 'tables/V' / (c['canonical'].replace('/', '__') + '.json.gz'))
            arms = list(B.evaluate_capture(c, tab, {a:heads[a,k] for a in ['S','V']}, labels, ids))
            assert [r['row_id'] for r in arms[0]['items']] == [r['row_id'] for r in arms[1]['items']]
            assert all(r['mra'] == 0 for a in arms for r in a['items'] if r['prediction'] is None)
            pin_code()
            rec = dict(capture=c['canonical'], room=c['room'], fold=k, in_primary=c['canonical'] in d['common_captures'],
                arms=arms, code_sha256=common_pins[str(ROOT/'selrefit2.py')], seconds=time.monotonic()-started)
            B.write(p,rec)
        seen.update(r['row_id'] for r in rec['arms'][0]['items'])
        B.status(f'Serving-socket scoring has completed {i+1}/{len(d["captures"])} training captures with both out-of-fold models. Printed distances, zero-scored refusals, choice correctness, and exact feature checks are saved per capture. No held-out data has been read.')
        print('SCORE', i+1, len(d['captures']), c['canonical'], rec['seconds'], flush=True)
    assert seen == ids
    B.write(OUT / 'SCORE_COMPLETE.json', dict(captures=len(d['captures']), row_ids=sorted(seen), heldout_read=False))


def metrics(records):
    result = dict(captures=len(records), rooms=len({r['room'] for r in records}))
    for arm in ['S','V']:
        data = [a for r in records for a in r['arms'] if a['arm']==arm]
        rows = [r for a in data for r in a['items']]
        choices = [r for a in data for r in a['choices']]
        result[arm] = dict(distance_rows=len(rows), gap_mra=float(np.mean([r['mra'] for r in rows])),
            refused=sum(r['prediction'] is None for r in rows), objects=len(choices),
            choice_accuracy=float(np.mean([r['correct'] for r in choices])))
    result['paired_gap_mra_gain'] = result['V']['gap_mra'] - result['S']['gap_mra']
    result['paired_choice_accuracy_gain'] = result['V']['choice_accuracy'] - result['S']['choice_accuracy']
    result['paired_refusal_rate_gain'] = (result['V']['refused']-result['S']['refused']) / result['S']['distance_rows']
    return result


def bootstrap(records):
    rooms = sorted({r['room'] for r in records})
    values = []
    for room in rooms:
        recs = [r for r in records if r['room']==room]
        m = metrics(recs)
        values.append([m['S']['distance_rows'], m['S']['objects']] +
            [m[a][field] * (m[a]['distance_rows'] if field=='gap_mra' else m[a]['objects'] if field=='choice_accuracy' else 1)
             for field in ['gap_mra','choice_accuracy','refused'] for a in ['S','V']])
    values = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOT_SEED)
    draws = np.empty((10000,9))
    # One room draw supplies both arms, including every capture and row in that room.
    for start in range(0,10000,100):
        indices = rng.integers(0,len(rooms),size=(100,len(rooms)))
        totals = values[indices].sum(axis=1)
        for j,denom in enumerate([0,1,0]):
            s = totals[:,2+2*j] / totals[:,denom]
            v = totals[:,3+2*j] / totals[:,denom]
            draws[start:start+100,3*j:3*j+3] = np.column_stack([s,v,v-s])
    names = [f'{metric}_{arm}' for metric in ['gap_mra','choice_accuracy','refusal_rate'] for arm in ['S','V','V_minus_S']]
    return dict(unit='physical room', weighting='pooled rows for gap MRA and refusals; pooled objects for choice accuracy',
        draws=10000, seed=BOOT_SEED, rooms=len(rooms), paired=True,
        ci95={name:np.quantile(draws[:,i],[.025,.975]).tolist() for i,name in enumerate(names)},
        bootstrap_sample_sha256=hashlib.sha256(draws.tobytes()).hexdigest())


def finalize():
    d = B.js(OUT/'TRAIN_DATA.json'); fit = B.js(OUT/'FIT.json')
    B.js(OUT/'SCORE_COMPLETE.json')
    records = [B.js(OUT/'cv_captures'/(c['canonical'].replace('/','__')+'.json')) for c in d['captures']]
    pin_code()
    results = {}
    for name,recs in [('primary',[r for r in records if r['in_primary']]), ('all_training',records),
                      ('missing_s4_g1_only',[r for r in records if not r['in_primary']])]:
        folds = [dict(fold=k,**metrics([r for r in recs if r['fold']==k])) for k in range(5)]
        gains = [f['paired_gap_mra_gain'] for f in folds]
        results[name] = dict(pooled=metrics(recs), folds=folds, mean_paired_gap_mra_gain=float(np.mean(gains)),
            fold_sample_sd=float(np.std(gains,ddof=1)), spread_2sd=2*float(np.std(gains,ddof=1)), bootstrap=bootstrap(recs))
    primary = results['primary']
    wins = primary['mean_paired_gap_mra_gain'] > primary['spread_2sd']
    B.write(OUT/'SELREFIT2.json',dict(status='COMPLETE', decision_rule=B.read(OUT/'DECISION.md').decode().splitlines()[0],
        serving_labels_win=wins, decision_scope='primary; equally weighted fold gains; sample SD',
        results=results, missing_s4_g1=d['missing_s4_g1'], missing_capture_count=len(d['missing_s4_g1']),
        config=fit['config'], seed=SEED, bootstrap_seed=BOOT_SEED, fit=fit['folds'], folds=d['folds'],
        training_policy=d['training_policy'], heldout_read=False, candidate_identity_mapping_used=False,
        socket='own-depth median_ratio scale; serving gravity; null-argmax; printed two-decimal distance; refusals score zero',
        interpretation='Arm S and arm V use their respective native candidate tables, features, and labels; this compares training geometry/label pipelines, not a fixed-candidate label-only intervention.',
        commands=['bash run.sh selrefit2.py prepare','bash run.sh selrefit2.py train','bash run.sh selrefit2.py score','bash run.sh selrefit2.py finalize']))
    if wins:
        (OUT/'READ_REQUEST.md').write_text('Request a paired routed distance read at an approved boundary, with arms S and V.\n\nKeep the capture/row manifest, prompts, router, model, seeds, cached proposals, own-depth median_ratio scale, serving gravity, null-argmax rule, distance implementation, corrected labels, and refusal scoring identical. Change only selector coefficients, including their fitted normalization buffers. Fit both final heads with the frozen recipe on the same 215 eligible K1 training captures before the boundary read; archive the heads and input hashes before opening evaluation data. Evaluate both arms on identical routed distance rows and report paired printed-distance gap MRA, refusals, and physical-room bootstrap intervals. This request does not perform a held-out read.\n')
    lines = [
        '# Fair out-of-fold selector comparison',
        f'Decision: {"SERVING LABELS WIN" if wins else "NO WIN"}. Mean fold gain V − S = {primary["mean_paired_gap_mra_gain"]:.6f}; 2 × sample fold SD = {primary["spread_2sd"]:.6f}.',
        'Frozen rule: "serving labels win if V - S mean paired gap-MRA gain on K1 train exceeds 2 x fold SD of the paired gain".',
        'Scope: K1 training captures only; five unchanged physical-room folds, seed 20261116. No held-out data or results were read.',
        'Primary: 215 captures; 24 missing S4/G1 tables are excluded from both fitting arms and primary scoring. Exact missing paths appear in SELREFIT2.json.',
        'Secondary: the same fold models score all 239 training captures, including the 24 missing-table captures; neither arm trains on those 24.',
        'S uses native S4/G1 tables; V uses native serving-geometry tables. Their candidate pools and features can differ; this tests the full training-table intervention.',
        'Both arms: 58-feature DeepSets, hidden 32, no name embedding, candidate/null BCE, AdamW lr .003 and wd .001, 15 epochs, batch 16; no search.',
        'Both arms score through own-depth median_ratio scale, serving gravity, null-argmax, and the printed two-decimal socket distance against corrected labels; refusals score zero.',
        '',
        '| Scope | Rows | S gap MRA | V gap MRA | V − S | S/V refusals | S/V choice accuracy |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for name in results:
        m=results[name]['pooled'];s=m['S'];v=m['V']
        lines.append(f'| {name} | {s["distance_rows"]} | {s["gap_mra"]:.6f} | {v["gap_mra"]:.6f} | {m["paired_gap_mra_gain"]:+.6f} | {s["refused"]}/{v["refused"]} | {s["choice_accuracy"]:.6f}/{v["choice_accuracy"]:.6f} |')
    lines += ['', '| Primary fold | Rows | S gap MRA | V gap MRA | V − S | S/V refusals | S/V choice accuracy |', '|---|---:|---:|---:|---:|---:|---:|']
    for f in primary['folds']:
        s=f['S'];v=f['V']
        lines.append(f'| {f["fold"]} | {s["distance_rows"]} | {s["gap_mra"]:.6f} | {v["gap_mra"]:.6f} | {f["paired_gap_mra_gain"]:+.6f} | {s["refused"]}/{v["refused"]} | {s["choice_accuracy"]:.6f}/{v["choice_accuracy"]:.6f} |')
    lines += ['', 'Physical-room bootstrap: 10,000 paired draws, seed 20261119; pooled row/object weighting and percentile 95% intervals.']
    for name in ['primary','all_training']:
        b=results[name]['bootstrap']; ci=b['ci95']
        lines.append(f'{name}: gap-MRA gain CI [{ci["gap_mra_V_minus_S"][0]:+.6f}, {ci["gap_mra_V_minus_S"][1]:+.6f}]; choice gain CI [{ci["choice_accuracy_V_minus_S"][0]:+.6f}, {ci["choice_accuracy_V_minus_S"][1]:+.6f}]; {b["rooms"]} rooms.')
    lines += [
        'Commands: `bash run.sh selrefit2.py prepare` produced counts/folds; `bash run.sh selrefit2.py train` fitted both arms;',
        '`bash run.sh selrefit2.py score` produced per-capture distances/choices; `bash run.sh selrefit2.py finalize` produced every reported aggregate, bootstrap interval, and decision.',
        'All secondary fold metrics, coefficients, input SHA-256 hashes, and per-row paired predictions accompany the JSON and archive.',
        'Validation: `bash run.sh verify2.py` checks room separation, fold normalization, paired coverage, printed distances, refusal scoring, and all output input hashes.',
        'Archive: `bash run.sh package.py` produces out/sb_selrefit2.tar and out/sb_selrefit2.tar.sha256.',
        'Boundary read: '+('requested in out/READ_REQUEST.md; no read was performed.' if wins else 'not requested because the frozen rule did not pass.'),
    ]
    assert len(lines)<=40
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    B.status(f'Analysis complete: {"serving labels win" if wins else "no win"}; mean fold gain {primary["mean_paired_gap_mra_gain"]:.6f}, 2 x fold SD {primary["spread_2sd"]:.6f}. Primary and all-training metrics and room bootstrap intervals are saved. Validation and packaging are next; no held-out data has been read.')
    print('DECISION',wins, primary['mean_paired_gap_mra_gain'], primary['spread_2sd'],flush=True)


if __name__=='__main__':
    {'prepare':prepare,'train':train,'score':score,'finalize':finalize}[sys.argv[1]]()
