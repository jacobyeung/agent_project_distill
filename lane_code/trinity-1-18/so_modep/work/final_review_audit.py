"""Check the final package and evidence without applying or modifying source."""
from pathlib import Path
import hashlib, json, re, subprocess

L = Path(__file__).resolve().parents[1]
manifest = json.loads((L/'out/patches/manifest.json').read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for entry in manifest['patches']:
    assert sha(L/'out/patches'/entry['file']) == entry['sha256']
    for file in entry['files']:
        for tree in ('tree', 'delivery_tree'):
            assert sha(L/'work'/tree/file['path']) == file['patched_sha256']
report = (L/'out/REPORT.md').read_text()
assert report.startswith('VERDICT: DONE ')
for doc in ('REPORT.md', 'NOTE_FOR_TREE_REBUILD.md'):
    text = (L/'out'/doc).read_text()
    assert 'Review round 1: finding -> fix -> test' in text
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if not link.startswith('http'):
            assert (L/'out'/link).exists(), (doc, link)
for label in ('off', 'paths', 'sql', 'both'):
    text = (L/'out/tests'/f'review1_native_{label}.log').read_text()
    for line in text.splitlines():
        if line.startswith(('Ran ', 'OK')):
            assert line in report
    result = json.loads((L/'work/tests'/f'review1_native_{label}'/'RESULT.json').read_text())
    assert result['successful'] and result['tests'] == 173 and len(result['skipped']) == 2
mutants = json.loads((L/'out/tests/review1_mutations.json').read_text())
contracts = json.loads((L/'out/tests/review1_contract_mutations.json').read_text())
assert len(mutants) == 6 and len(contracts) == 6
assert all(row['failures'] == 1 and row['errors'] == 0 for row in mutants+contracts)
assert json.loads((L/'out/tests/review1_parity_mutation.json').read_text())['returncode'] == 1
parity = json.loads((L/'out/tests/review1_file_parity.json').read_text())['results']
assert len(parity) == 4 and all(row['files'] == parity[0]['files'] for row in parity)
assert all(all(value['unique_frames'] == 32 for value in row['frame_sources'].values()) for row in parity)
disk_kib = int(subprocess.check_output(['du', '-sk', str(L)], text=True).split()[0])
assert disk_kib*1024 < 3_000_000_000
stamp = subprocess.check_output(['date', '-u'], text=True).strip()
result = dict(time_utc=stamp, base_seal=manifest['base_seal'], patches_verified=2,
              matrix_configurations=4, tests_per_configuration=173, expected_skips_per_configuration=2,
              native_files_per_configuration=39, deliberate_mutants_caught=13,
              lane_disk_kib=disk_kib, production_adoption='OFF pending real-store parity')
(L/'out/tests/review1_final_audit.json').write_text(json.dumps(result, indent=2)+'\n')
with (L/'out/REPORT.md').open('a') as handle:
    handle.write(f'\nFinal package/evidence audit passed {stamp}. Measured lane disk usage: {disk_kib:,} KiB, below 3 GB. [Audit record](tests/review1_final_audit.json).\n')
(L/'work/STATUS.md').write_text(f'''Started 2026-11-19 10:59:49 UTC; deadline 12:29:49 UTC. Host trinity-1-18.
Updated {stamp}.

DONE: All review findings addressed: one MEDIUM, four LOW, no HIGH findings.
Regression task complete: 820 sparse keys / four chunks, full table/view row and event order, order-dependent output, and native inventory bytes. Delivered tests pass; deliberate reversed chunks/rows fail.
Native parity task complete: all 39 files match across four switch combinations. Every source has 32 distinct physical frames. Spies prove zero calls OFF and positive calls ON.
Suite task complete: each of four configurations runs 173 tests, passes 171 and explicitly skips two unavailable integrations. Independent patches run 14 and 20 tests with one expected skip each. Targeted 13 and documentation/helper 4 tests pass.
Mutation task complete: all 13 deliberate variants are caught (six code regressions, one degenerate native fixture, six document/helper contracts).
Package task complete: independent/combined application and manifest hashes verified against base b262e7a7. REPORT.md and NOTE_FOR_TREE_REBUILD.md state the review mapping, exact commands/outputs and adoption rule.
Adoption: both switches OFF on N's first launch. ON from the next only after one production launch establishes parity on real stores. No production switch was enabled here.
Outstanding: production real-store parity/timing, H100 training, socket-enabled Gloo, unstaged external manifest. These require the orchestrator's environment.
Measured lane size {disk_kib:,} KiB, below 3 GB. CPU affinity 0–7, nice 10, bounded threads, CUDA hidden. No Git, SSH, Slurm, deletion or input edits.
''')
print('FINAL_AUDIT '+json.dumps(result, sort_keys=True))
