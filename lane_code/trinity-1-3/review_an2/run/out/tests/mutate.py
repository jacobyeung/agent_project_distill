import hashlib, json, subprocess, sys
from pathlib import Path
AN = Path(__file__).resolve().parents[2]; SRC = (AN/'out/native_vs_direct.py').read_text()
PY = '/scratch/jjyeung/envs/p1cpu/bin/python3.12'
M = {
 'M01_pairing_shift_direct': ("native_score(arms['scripted'][k]), direct[k]['score']) for k in selected]",
                              "native_score(arms['scripted'][k]), direct[selected[(selected.index(k)+1)%len(selected)]]['score']) for k in selected]"),
 'M02_denominator_drop_no_answer': ("selected = group if selection == 'all_items' else",
                                    "selected = [k for k in group if not arms['unflagged'][k]['no_answer']] if selection == 'all_items' else"),
 'M03_sensitivity_keeps_direct_refused': ("direct_mean = pct([direct[k]['score'] for k in selected])",
                                          "direct_mean = pct([direct[k]['score'] for k in group])"),
 'M04_primary_drops_refused': ("selected = group if selection == 'all_items' else",
                               "selected = [k for k in group if task_rows[k]['native'] not in refused] if selection == 'all_items' else"),
 'M05_resample_items_not_rooms': ("rows = [(task_rows[k]['room'],", "rows = [(k,"),
 'M06_resample_captures_not_rooms': ("rows = [(task_rows[k]['room'],", "rows = [(task_rows[k]['native'],"),
 'M07_percentile_90': ("[quantile(values[j], .025), quantile(values[j], .975)]", "[quantile(values[j], .05), quantile(values[j], .95)]"),
 'M08_unpaired_bootstrap': ("        for j in (0, 1):\n            values[j].append(100 * sum(c[j + 1] for c in chosen) / denominator)",
                            "        other = rnd.choices(clusters, k=len(clusters))\n        for j in (0, 1):\n            values[j].append(100 * (sum(c[j + 1] for c in chosen) + sum(c[j+1] for c in other)) / (denominator + sum(c[0] for c in other)))"),
 'M09_bootstrap_room_weighted': ("values[j].append(100 * sum(c[j + 1] for c in chosen) / denominator)",
                                 "values[j].append(100 * sum(c[j + 1] / c[0] for c in chosen) / len(chosen))"),
 'M10_refusal_direct_zeroed': ("rows = [(task_rows[k]['room'], native_score(arms['unflagged'][k]),\n                     native_score(arms['scripted'][k]), direct[k]['score']) for k in selected]",
                               "rows = [(task_rows[k]['room'], native_score(arms['unflagged'][k]),\n                     native_score(arms['scripted'][k]), 0 if task_rows[k]['native'] in refused else direct[k]['score']) for k in selected]"),
 'M11_callrate_all_items': ("decoded = [r for r in rs if not r.get('geometry_refusal')]", "decoded = rs"),
 'M12_label_answer_for_primary': ("return 'released_answer' if row['stratum'] == 'primary' else 'answer'", "return 'answer'"),
 'M13_drop_capped': ("selected = group if selection == 'all_items' else",
                     "selected = [k for k in group if not arms['unflagged'][k]['capped']] if selection == 'all_items' else"),
}
out = {}
for name, (a, b) in M.items():
    # Both primary and capped selection rows carry the room coordinate.
    expected_occurrences = 2 if name.startswith(('M05_', 'M06_')) else 1
    assert SRC.count(a) == expected_occurrences, (name, SRC.count(a))
    d = AN/'work/mutations'/name/'out'
    source = SRC.replace(a, b)
    if (d/'tests/RESULTS.json').is_file():
        assert (d/'native_vs_direct.py').read_text() == source
        r = json.loads((d/'tests/RESULTS.json').read_text())
        returncode = 0 if r['successful'] else 1
    else:
        d.mkdir(parents=True)
        (d/'native_vs_direct.py').write_text(source)
        (d/'tests').mkdir()
        for path in (AN/'out/tests').glob('*.py'):
            (d/'tests'/path.name).write_bytes(path.read_bytes())
        p = subprocess.run([PY,'-I','-s','-B',str(d/'tests/run_tests.py'),'--all'], capture_output=True, text=True, timeout=600)
        (d/'tests/run.log').write_text(p.stdout+p.stderr)
        r = json.loads((d/'tests/RESULTS.json').read_text())
        returncode = p.returncode
    killed = [f['test'].split()[0] for f in r['failures']+r['errors']]
    out[name] = dict(killed=bool(killed), failing_tests=killed, results_path=str(d/'tests/RESULTS.json'),
                     returncode=returncode, source_sha256=hashlib.sha256(SRC.encode()).hexdigest())
    print(name, 'KILLED' if killed else 'SURVIVED', killed, flush=True)
    (AN/'out/tests/MUTATION_RESULTS.json').write_text(json.dumps(out, indent=2)+'\n')
