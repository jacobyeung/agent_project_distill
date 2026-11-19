from pathlib import Path
import json
root=Path('sb_mask_phrase/part2')
p=root/'vendor/PINS.json'; d=json.loads(p.read_text()); h='19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d'
d['sha256']['terminator.sh']=h; d['input_sha256']['sb_mask_phrase/part2/vendor/terminator.sh']=h
p.write_text(json.dumps(d,indent=1)+'\n')
p=root/'launch_gpu.sh'; s=p.read_text().replace('export PYTHONDONTWRITEBYTECODE=1', 'export OPENSSL_CONF="$PWD/../payload/environment/ssl/openssl.cnf" PATH=/usr/bin:/bin\nexport PYTHONDONTWRITEBYTECODE=1'); p.write_text(s)
p=root/'launch_gpu.py'; s=p.read_text().replace("env.update(CUDA_VISIBLE_DEVICES=identity,", "env.update(OPENSSL_CONF=str(kit.parent/'payload/environment/ssl/openssl.cnf'), PATH='/usr/bin:/bin',\n               CUDA_VISIBLE_DEVICES=identity,"); p.write_text(s)
p=root/'gate.py'; s=p.read_text(); s=s.replace('def fixture_dir(root=HERE):', '''def refuse_symlinks(path):
    # Check ancestors first, before stat, resolve or traversal can follow a link.
    for candidate in reversed((path, *path.parents)):
        if candidate.is_symlink():
            raise SystemExit(f'REFUSED: symlink {candidate}')


def fixture_dir(root=HERE):'''); s=s.replace("path = (root / os.environ.get('PART2_FIXTURE_DIR', 'work/part2_fixture')).resolve()", "path = root / os.environ.get('PART2_FIXTURE_DIR', 'work/part2_fixture')\n    refuse_symlinks(path)\n    path = path.resolve()")
s=s.replace("bars = root / 'part2/BARS_PART2.json'", "bars = root / 'part2/BARS_PART2.json'\n    refuse_symlinks(bars)")
s=s.replace('    for folder in targets:\n', "    # Capture scores are aggregate inputs, but symlinked inputs still refuse.\n    inputs = [root / 'work/part2_caps', root / 'out/pool_part2']\n    for folder in dict.fromkeys(targets + inputs):\n        refuse_symlinks(folder)\n")
s=s.replace("        for path in sorted(folder.rglob('*')):\n", "        for path in sorted(folder.rglob('*')):\n            refuse_symlinks(path)\n            if folder not in targets:\n                continue\n")
s=s.replace("path.suffix in ('.json', '.jsonl', '.gz') or path.name.startswith('PER_ITEM')", "any(s.lower() in ('.json', '.jsonl', '.csv', '.tsv', '.gz') for s in path.suffixes) or path.name.upper().startswith('PER_ITEM')")
s=s.replace("('STOP.json', 'KILLED', 'KILLED.json')", "('STOP', 'STOP.json', 'KILLED', 'KILLED.json')"); p.write_text(s)
p=root/'price.py'; s=p.read_text(); s=s.replace('def frozen(path, sha_file):', '''def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(T.clean(value), stream, indent=1, allow_nan=False)


def write_gz(path, value):
    with gzip.open(path, 'xt') as stream:
        json.dump(T.clean(value), stream, separators=(',', ':'), allow_nan=False)


def frozen(path, sha_file):''')
s=s.replace('K.write_gz(', 'write_gz(').replace("        if dest.exists():\n            continue\n", '')
s=s.replace("(FIXTURE/'FIXTURE.json').write_text(json.dumps(", "write_json(FIXTURE/'FIXTURE.json', ").replace("HERE/'kit.py', NEW, BARS2)})), indent=1))", "HERE/'kit.py', NEW, BARS2)})))")
start=s.index('    cat = ', s.index('def aggregate(')); end=s.index('    out_dir.mkdir',start)
body=s[start:end]
# The population helper scopes every fit, comparison and report to its kept captures.
helper='''def population(data, wcf, a0, keep, fc):
    data = [d for d in data if keep(d['capture'])]
    wcf = [r for r in wcf if keep(r['capture'])]
'''+body.replace("    assert len(good_rows) == part1['both_good_rows']\n", '')+'''    cf = {r['row_id']: r['prediction'] for r in wcf}
    result = dict(rows=len(wcf), captures=len(data), both_good_rows=len(good_rows),
                  w_cf_mra=AG.mra(wcf), w_cf_gain=S.contrast(wcf, [a0[r['row_id']] for r in wcf]),
                  bars=bars, best_w=best,
                  w_exact_rows_equal_w_cf=sum(r['prediction'] == cf[r['row_id']] for r in arms['W_exact']),
                  arms={a: {k: v for k, v in r.items() if k != 'stats'} for a, r in reports.items()},
                  new_choices={k: {n: v for n, (v, ev) in c.items() if v != 'raw'} for k, c in new_choice.items()},
                  new_evidence={k: {n: ev for n, (v, ev) in c.items()} for k, c in new_choice.items()})
    return result, arms


'''
s=s[:start]+'''    dec, arms = population(data, wcf, a0, lambda c: c not in AG.WITHHELD, part1['fold_choices'][chosen])
    full, arms_full = population(data, wcf, a0, lambda c: True, part1['fold_choices_1037'][chosen])
    for key, expected in dict(rows=1012, captures=204, both_good_rows=442).items():
        assert dec[key] == part1['population']['decision'][key] == expected, (key, dec[key])
    for key, expected in dict(rows=1037, captures=209, both_good_rows=456).items():
        assert full[key] == part1['population']['all_rows'][key] == expected, (key, full[key])
'''+s[end:]
s=s.replace("chosen = part1['chosen_arm']; fc = part1['fold_choices'][chosen]", "chosen = part1['chosen_arm']")
s=s.replace("open(out_dir/'PER_ITEM_PART2.jsonl', 'w')", "open(out_dir/'PER_ITEM_PART2.jsonl', 'x')")
a=s.index('    cf = ',s.index('def aggregate(')); b=s.index('                    checks=',a)
s=s[:a]+'''    decision = dict(bars_file=dict(path=str(BARS2), sha256=K.sha(BARS2), verified_unchanged=True), new_phrases_sha256=K.sha(NEW),
                    part1_arm=chosen, **dec, **{key+'_1037': value for key, value in full.items()},
                    fold_choices=part1['fold_choices'][chosen], fold_choices_1037=part1['fold_choices_1037'][chosen],
'''+s[b:]
s=s.replace("(out_dir/'DECISION_PART2.json').write_text(json.dumps(T.clean(decision), indent=1, allow_nan=False))", "write_json(out_dir/'DECISION_PART2.json', decision)")
s=s.replace("{k: v['verdict'] for k, v in bars.items()}", "{k: v['verdict'] for k, v in dec['bars'].items()}").replace('best_w=best,\n                          fixture=fixture', "best_w=dec['best_w'],\n                          fixture=fixture")
s=s.replace('def aggregate(fixture=False):', helper+'def aggregate(fixture=False):')
p.write_text(s)
