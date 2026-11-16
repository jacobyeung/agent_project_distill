import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .io import canonical, new_output, pin, read_json, write_json


VSI_TYPES = ('absolute_count', 'absolute_size_object', 'absolute_distance_object', 'absolute_size_room',
             'relative_count', 'relative_size_object', 'relative_distance_object')
DATA = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917')
VSI = DATA / 'source/vsi_590k.jsonl'
V3 = DATA / 'membership/v3/MANIFEST.json'
VSTI = Path('/home/jjyeung/agent_project/agent/vstibench_full.json')
VSTI_SHA256 = '0a472b0d483a880e8110571b0e8e6a1b193d583100b640d09bf85dee6d85aa5a'


def sample_vsi(path, expected, per_type=1024):
    if type(per_type) is not int or per_type < 1:
        raise ValueError('authority sample size must be positive')
    samples = {name: [] for name in VSI_TYPES}
    hasher, counts = hashlib.sha256(), Counter()
    prefix_bytes, last_line = 0, 0
    with Path(path).open('rb') as handle:
        for number, raw in enumerate(handle, 1):
            hasher.update(raw)
            prefix_bytes += len(raw)
            row = json.loads(raw)
            kind = row['question_type']
            counts[kind] += 1
            if kind in samples and len(samples[kind]) < per_type:
                turns = row['conversations']
                human = [turn['value'] for turn in turns if turn['from'] == 'human']
                answer = [turn['value'] for turn in turns if turn['from'] == 'gpt']
                if len(human) != 1 or len(answer) != 1:
                    raise ValueError(f'unsupported conversation on line {number}')
                samples[kind].append({'line': number, 'question': human[0], 'answer': answer[0]})
            last_line = number
            if all(len(rows) == per_type for rows in samples.values()):
                break
        prefix_sha = hasher.copy().hexdigest()
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            hasher.update(chunk)
    if any(not rows for rows in samples.values()):
        raise ValueError('missing VSI wording families: ' + repr([k for k, v in samples.items() if not v]))
    measured = hasher.hexdigest()
    if measured != expected['sha256'] or Path(path).stat().st_size != expected['bytes']:
        raise ValueError('VSI-590K authority digest or size mismatch')
    return {'authority': {'path': str(Path(path).resolve()), 'sha256': measured, 'bytes': expected['bytes']},
            'sampling': {'per_type': per_type, 'parsed_through_line': last_line, 'parsed_prefix_bytes': prefix_bytes,
                         'parsed_prefix_sha256': prefix_sha, 'encountered_types': dict(counts),
                         'policy': 'one bounded-memory pass; stop parsing once each family has its quota; hash the unread tail without parsing'},
            'samples': samples}


def sample_vsti(path, expected_sha=VSTI_SHA256):
    spec = pin(path)
    if spec['sha256'] != expected_sha:
        raise ValueError('VSTIBench wording authority digest mismatch')
    text = Path(path).read_text()
    rows = json.loads(text)
    lines = [text.count('\n', 0, match.start()) + 1 for match in re.finditer(r'"question"\s*:', text)]
    if len(lines) != len(rows):
        raise ValueError('cannot bind benchmark questions to physical source lines')
    samples = [{'line': line, 'question': row['question'], 'answer': row['ground_truth'], 'id': row['id']}
               for line, row in zip(lines, rows) if row['question_type'] == 'camera_obj_abs_dist']
    if not samples:
        raise ValueError('camera-object wording authority is empty')
    return {'authority': spec, 'samples': samples}


def collect(vsi=VSI, vsti=VSTI, manifest=V3, per_type=1024):
    v3 = read_json(manifest)
    benchmark = v3['benchmark_blocking']['eval_files']['vsibench_full']
    spec = pin(benchmark['path'])
    if spec['sha256'] != benchmark['sha256']:
        raise ValueError('VSIBench family authority digest mismatch')
    rows = read_json(benchmark['path'])
    mc = Counter(row['question_type'] for row in rows if row.get('options'))
    return {'schema': 'gtmeasure-authority-samples-v1', 'vsi': sample_vsi(vsi, v3['source'], per_type),
            'vsti': sample_vsti(vsti), 'vsibench': {'authority': spec, 'mc_question_types': dict(mc)},
            'v3_manifest': pin(manifest)}


def main():
    parser = argparse.ArgumentParser(description='Cache bounded wording samples; never load VSI-590K whole.')
    parser.add_argument('--vsi', type=Path, default=VSI)
    parser.add_argument('--vsti', type=Path, default=VSTI)
    parser.add_argument('--v3-manifest', type=Path, default=V3)
    parser.add_argument('--per-type', type=int, default=1024)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.vsi, args.vsti, args.v3_manifest, args.per_type)
    output = new_output(args.output)
    write_json(output / 'AUTHORITIES.json', result)
    print(canonical({'sampling': result['vsi']['sampling'], 'mc_types': result['vsibench']['mc_question_types']}))
    for kind, rows in result['vsi']['samples'].items():
        print(kind, canonical(rows[:6]))
    print('camera_obj_abs_dist', canonical(result['vsti']['samples'][:1]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
