"""Write the compact evidence index after all local checks finish."""
from pathlib import Path
import hashlib
import json

E=Path(__file__).resolve().parent
K=E.parent.parent
comparison=json.loads((E/'comparison_summary.json').read_text())
inventory=json.loads((E/'inventory_summary.json').read_text())
proof=json.loads((E/'proof_result.json').read_text())
records=json.loads((E/'package_comparison.json').read_text())
mapping=json.loads((E/'mapping.json').read_text())
assert proof['passed']
assert not inventory['new_or_unclassified']
assert json.loads((E/'build1.json').read_text())==json.loads((E/'build2.json').read_text())
tests=(E/'tests.log').read_text()
assert '79 passed' in tests and 'failed' not in tests.lower()
sha=comparison['package_sha256']
rows={r['old']:r for r in records}
lines=['# F1 evidence','',
    f'Package SHA256: `{sha}`; 125 files, {comparison["bytes"]:,} bytes. Two deterministic builds matched.',
    'Baseline: `6e025a8898e112fd5282af03d8d0e82ce947a2ce2b714736de2745ee293f6572`, verified after one throttled read of the requested archive; reconstructed under `build/f1/baseline/`.',
    'Diff: 112 files retain names and bytes; five input files retain bytes under opaque names; eight files contain path-string edits or package-list exclusions; two unused cell files are omitted.',
    'The complete [hash table and unified diffs](DIFF.md), [machine-readable comparison](build/f1/package_comparison.json), and [zero-context diff](build/f1/path_strings.diff) cover every package member. The comparator asserts the exact replacements and exclusions.',
    'The two cell files remain untouched in the local source directory and are excluded from both package.tar and the launcher payload.',
    'The prepared batch payload was decoded independently: all five [input hashes](build/f1/payload_input_hashes.json) equal the baseline, and all seven F1 pathnames are absent.',
    '', '| Job-root suffix | Unchanged input SHA256 |','|---|---|']
for before,after in mapping['rename'].items():
    lines.append(f'| `p/{after}` | `{rows[before]["sha256"]}` |')
lines += ['',
    'All 65 reader files appear in the [raw before/after hash table](build/f1/reader_hashes.tsv). All 36 evaluator files are byte-identical; 62 reader files are byte-identical. The three remaining reader files differ only by the path strings shown in DIFF.md.',
    '', '| Reader file | Baseline SHA256 | Current SHA256 |','|---|---|---|']
for name in ('reader/chain.py','reader/official_adapter.py','reader/official_score.py'):
    r=rows[name];lines.append(f'| `{name}` | `{r["old_sha256"]}` | `{r["sha256"]}` |')
lines += ['',
    'The scorer CLI default changes only its cohort pathname. The scorer functions, adapter decisions, reader logic, input bytes and SHA pin constants are unchanged.',
    'The proof argv paths containing `legs1` and `rv_merge_fix` remain: changing them requires reader/chain.py and proof/phase_b.py, beyond the permitted launcher-only rename. They also occur in the unchanged VSI kit f42aa1a4.',
    '',
    'Local proof: **PASS**, from a fresh extraction into `build/f1/extracted/`, with an absent work directory that the harness creates empty.',
    'Command (from work/): `PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/kit_revsi/build/f1" OPENBLAS_NUM_THREADS=1 timeout --signal=INT 240 kit_revsi/.venv312/bin/python -B kit_revsi/build/f1/audit_run.py > kit_revsi/build/f1/proof04.log 2>&1`.',
    f'The proof exercised 261 generated clips, {proof["items"]} task items and {proof["phase_b_items"]} dev items; see [result](build/f1/proof_result.json) and [log](build/f1/proof04.log). The recorder wraps local command boundaries without editing packaged code.',
    'Local limitation: an independent [asyncio thread probe](build/f1/asyncio_probe.log) timed out; the proof wrapper bounds selector waits to 0.1 s in the parent and child processes. This external harness adjustment changes no packaged bytes. Initial recorder-error/stalled diagnostic runs are retained; only proof04 is a PASS.',
    'Tests: **79 passed**, two metric divide warnings; command: `PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/kit_revsi/build/f1" kit_revsi/.venv312/bin/python -B -m pytest -q -p no:cacheprovider kit_revsi/tests` ([log](build/f1/tests.log)). All 76 packaged Python files compiled.',
    '',
    f'The complete [job-root path list](build/f1/job_paths.tsv) contains {inventory["paths"]} entries (files, directories and symlinks), enumerated from `{proof["job_root"]}`.',
    f'The complete [recorded local argv](build/f1/local_argv.jsonl) contains {inventory["local_commands"]} command records; the [Orchard argv listing](build/f1/orchard_argv.jsonl) preserves the recorded argument order and labels projected paths and unexecuted namespace/submission/transport construction.',
    'The local proof substitutes runtimes, model assets, media, GPU checks, parity and publication. Its path list is exhaustive for this local job root; real Orchard archive interiors and unexecuted transfer/error branches were not observed.',
    'The [case-insensitive hit table](build/f1/path_hits.tsv) reports every matching string, source/index, term, classification and reason. Local audit/venv prefixes are labeled NEW LOCAL ONLY; they are not Orchard paths.',
    'Search terms: `split, revsi, vsi, vsibench, distill, qgen, scannet, arkit, qwen, legs1, rv_merge, official, bench`. Counts and zero-hit terms appear in the [search summary](build/f1/inventory_summary.json).',
    'Every remaining Orchard-name hit is pre-existing: alias paths or kit filenames shared with f42aa1a4. No new matching payload path was found.',
    'No SSH, submission, Git, network, real media read, real engine or Orchard execution was performed.',
    '']
assert len(lines)<=60,len(lines)
(K/'F1_EVIDENCE.md').write_text('\n'.join(lines))
(K/'REPORT.md').write_text(
    'F1 gives the five payload inputs opaque names and omits the two unused cell files; input bytes, pins and execution/scoring logic are unchanged. Lane argv paths remain because their rename requires reader/proof edits.\n'
    f'Local proof PASS with an external selector-wait workaround; 79 tests passed; 76 Python files compiled; two deterministic builds matched SHA256 {sha}. See F1_EVIDENCE.md and DIFF.md; no Orchard run or submission occurred.\n')
print(json.dumps(dict(evidence_lines=len(lines),sha256=sha)))
