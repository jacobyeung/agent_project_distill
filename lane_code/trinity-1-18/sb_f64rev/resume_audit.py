"""Verify saved review provenance and enumerate all submitted patch edits, without Git."""
import ast
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'sb_f64'
OUT = ROOT / 'out'
inputs, cached = {}, {}

def read(path):
    path = Path(path)
    if str(path) not in cached:
        cached[str(path)] = path.read_bytes()
        inputs[str(path)] = hashlib.sha256(cached[str(path)]).hexdigest()
    return cached[str(path)]

def obj(path):
    return json.loads(read(path))

read(__file__)
previous = {}
for name in ('static_review', 'behavior_review', 'baseline_regression', 'patched_regression'):
    value = obj(OUT / (name + '.json'))
    changed, missing, outside = [], [], []
    for filename, expected in value['input_sha256'].items():
        path = Path(filename)
        if not (path.is_relative_to(SRC) or path.is_relative_to(ROOT)):
            outside.append(filename)
            continue
        if not path.is_file():
            missing.append(filename)
            continue
        # Stream the archive rather than retaining it in memory.
        if path.suffix == '.tar':
            with path.open('rb') as handle:
                actual = hashlib.file_digest(handle, 'sha256').hexdigest()
            inputs[filename] = actual
        else:
            read(path)
            actual = inputs[filename]
        if actual != expected:
            changed.append(filename)
    previous[name] = dict(changed=changed, missing=missing, outside_scope=outside,
                          inputs_checked=len(value['input_sha256']) - len(outside),
                          tests=value.get('tests'), errors=value.get('errors'), failures=value.get('failures'))

lines = ['# Edited source lines', '', 'Command: `python resume_audit.py`. Old/new intervals are inclusive; an empty interval denotes insertion/deletion.', '']
patches = {}
for relative in ('patches/tree_r1_to_f64.patch', 'read/reader_f64.patch'):
    patch = read(SRC / 'out/kit' / relative).decode()
    changes, current, old, new = [], None, 0, 0
    import re
    for line in patch.splitlines():
        if line.startswith('+++ '):
            current = line[4:].split('\t')[0]
        elif line.startswith('@@'):
            match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
            old, new = map(int, match.groups())
        elif line.startswith('--- '):
            continue
        elif line.startswith('-'):
            changes.append(dict(file=current, side='old', line=old, text=line[1:]))
            old += 1
        elif line.startswith('+'):
            changes.append(dict(file=current, side='new', line=new, text=line[1:]))
            new += 1
        elif line.startswith(' '):
            old += 1
            new += 1
    patches[relative] = changes
    lines += ['## ' + relative, '']
    for file in dict.fromkeys(c['file'] for c in changes):
        for side in ('old', 'new'):
            numbers = [c['line'] for c in changes if c['file'] == file and c['side'] == side]
            ranges = []
            for n in numbers:
                if ranges and n == ranges[-1][-1] + 1:
                    ranges[-1].append(n)
                else:
                    ranges.append([n])
            text = ', '.join(str(r[0]) if len(r) == 1 else f'{r[0]}–{r[-1]}' for r in ranges) or 'none'
            lines.append(f'- `{file}`, {side}: {text}.')
    lines.append('')
lines += ['## Additional module', '', '- `read/f64_read.py`: all lines are new.',
          '- Exact removed/added text is recorded in `resume_review.json`; the independent tree comparison is `INDEPENDENT_TREE_DIFF.patch`.', '']
(OUT / 'PATCH_LINES.md').write_text('\n'.join(lines))

cfg = obj(SRC / 'out/kit/configs/r1_config_f64.json')
needed = {'preparation': str(Path(cfg['preparation_output']) / 'receipt.json'),
          'code': cfg['code']['path'], 'admission': cfg['admission']['path'],
          'depth_init': cfg['depth_init']['path']}
missing = {key: {'path': value, 'status': 'EXISTS' if Path(value).is_file() else 'MISSING'} for key, value in needed.items()}
missing['r2_sampling'] = {'location': 'configs/r1_config_f64.json:r2_sampling', 'status': 'PRESENT' if cfg.get('r2_sampling') else 'MISSING'}
read_cfg = obj(SRC / 'out/kit/read/READ_CONFIG_F64.json')
missing['student_manifest'] = {'location': 'read/READ_CONFIG_F64.json:settings_add.student_manifest', 'value': read_cfg['settings_add']['student_manifest'], 'status': 'MISSING (placeholder)'}

evidence = {}
for path in sorted((SRC / 'out/evidence').glob('*.json')):
    value = obj(path)
    evidence[path.name] = dict(layers=value.get('layers', value.get('parameters', {}).get('lm_layers')),
        input_hashes='input_sha256' in value, records=len(value.get('records', [])),
        ranks_by_stream={s: sorted({r['rank'] for r in value.get('records', []) if r.get('stream') == s and 'rank' in r})
                         for s in ('pose', 'vqa', 'routing', 'pointing')})

spec = importlib.util.spec_from_file_location('review_token_audit', SRC / 'out/kit/scripts/token_audit.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
counterexamples = {}
for case, records in [('empty', []), ('partial', [dict(stream='pose', index=0, tokens=9127, check_row='ok', over_ceiling=False, over_tripwire=False)])]:
    shard = OUT / (case + '_coverage.jsonl')
    shard.write_text(''.join(json.dumps(r) + '\n' for r in records))
    for duplicate in (False, True) if records else (False,):
        output = OUT / (case + ('_duplicate' if duplicate else '') + '_coverage.json')
        module.summarize(SimpleNamespace(shards=[str(shard)] * (2 if duplicate else 1), out=str(output)))
        result = json.loads(output.read_text())
        counterexamples[output.stem] = result
        result['input_sha256'] = {str(shard): hashlib.sha256(shard.read_bytes()).hexdigest(),
            str(SRC / 'out/kit/scripts/token_audit.py'): inputs[str(SRC / 'out/kit/scripts/token_audit.py')],
            str(Path(__file__)): inputs[str(Path(__file__))]}
        output.write_text(json.dumps(result, indent=2) + '\n')

memory = {}
for name in ('mem_n32_8', 'mem_f64_8'):
    value = obj(SRC / 'out/evidence' / (name + '.json'))
    memory[name] = {'layers': value['layers'], 'tokens': [r['tokens'] for r in value['records']],
                    'pose_peak_above_gib': value['records'][0]['peak_above_gib'], 'pose_grad_gib': value['records'][0]['grad_gib']}
for path in [SRC / 'PROMPT.md', SRC / 'STATUS.md', SRC / 'out/kit/F64_REPORT.md',
             SRC / 'work/scripts/f64_dryrun.py', SRC / 'work/scripts/analyze.py']:
    read(path)
mix = {'pose': 16, 'vqa': 32, 'routing': 16, 'pointing': 8}
timings = {}
for layout in ('n32', 'f64'):
    records = obj(SRC / 'out/evidence' / ('fwd_' + layout + '_a43' + ('_local' if layout == 'f64' else '') + '.json'))['records']
    timings[layout] = {s: sum(r['seconds'] for r in records if r['stream'] == s) /
                      sum(r['stream'] == s for r in records) for s in mix}
cpu_ratio = sum(mix[s] * timings['f64'][s] for s in mix) / sum(mix[s] * timings['n32'][s] for s in mix)
enc = obj(SRC / 'out/evidence/encode_f64.json')['records']
numeric = dict(cpu_forward_ratio=cpu_ratio,
               f64_token_range=[min(r['tokens'] for r in enc), max(r['tokens'] for r in enc)],
               conditional_gpu_gib=[57 + 2.7 * (n - 4500) / 1000 for n in (9127, 10215, 16384)],
               conditional_tripwire_tokens=4500 + (76 - 57) * 1000 / 2.7,
               microsteps_per_rank=sum(mix.values()), mix=mix)
value = dict(command='bash run_cpu.sh resume_audit.py', input_sha256=inputs,
    saved_evidence_verification=previous, patch_edited_lines=patches, missing_inputs=missing,
    source_evidence=evidence, token_audit_counterexamples=counterexamples, memory=memory, recomputed_numbers=numeric,
    recipe={k: cfg['recipe'].get(k, 'ABSENT; trainer default applies') for k in ('global_batch', 'world_size', 'max_row_tokens', 'steps')})
(OUT / 'resume_review.json').write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps({k: v for k, v in value.items() if k not in ('input_sha256', 'patch_edited_lines', 'source_evidence')}, indent=2))
(ROOT / 'STATUS.md').write_text('Source and saved-evidence checks are complete. The review records exact patch lines, missing bound inputs, and token-audit counterexamples in out/resume_review.json. The CPU full-depth synthetic first-batch check is in progress; it cannot establish admission of the missing planned-run batches. No GPU or network was used.\n')
