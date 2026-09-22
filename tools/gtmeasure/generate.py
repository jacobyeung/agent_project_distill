# Scene-loop and provenance patterns adapt tools/vstigen/generate.py at e2f387e (vstigen-membership-v4-20260922).
import argparse
from collections import Counter
import importlib.metadata
from pathlib import Path

from .assets import load_scene, receipt_candidates, safe_scene
from .authority import DATA, V3, collect
from .blocking import benchmark_blocking, overlap, refuse_blocked
from .conventions import FAMILIES, MEASURES
from .formats import TYPE_FAMILY, harvest
from .io import canonical, digest, new_output, pin, read_json, sha, source_commit, verify_pin, write_json, write_jsonl
from .questions import generate_scene
from .split import ARM_C, load_split


PREPARED = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_membership_v3/out/inputs/prepared_scene_list.json')
JOB_ROOTS = [DATA / 'runtime_control/gt_teacher_r1313/materialization_v2' / name
             for name in ('jobs_scannet_v1', 'jobs_prep_v2', 'jobs_codex')]


def sources(structure='v1'):
    root = Path(__file__).resolve().parents[2]
    names = ['tools/gtmeasure/' + name + '.py' for name in ('__init__', 'io', 'authority', 'formats', 'blocking', 'mesh_membership',
                                                           'conventions', 'geometry', 'assets', 'targets', 'split', 'questions', 'generate', 'mix')]
    names += ['tools/gtmeasure/requirements.txt', 'collector/gt_scene_assets.py', 'student/compact_targets/compact_counted_v1.py']
    if structure == 'v2':
        names.append('collector/frame_alignment.py')
    return {name: sha(root / name) for name in names}


def counts(rows):
    return {'rows': len(rows), 'by_family': dict(Counter(row.get('family', row['category']) for row in rows)),
            'by_source': dict(Counter(row.get('source', 'compact') for row in rows)),
            'by_dataset': dict(Counter(row['dataset'] for row in rows))}


def write_dataset(output, train, heldout, split):
    if len({row['qid'] for row in [*train, *heldout]}) != len(train) + len(heldout):
        raise ValueError('duplicate dataset row identity')
    artifacts = {}
    for name, rows in (('train.jsonl', train), ('heldout.jsonl', heldout)):
        write_jsonl(output / name, rows)
        artifacts[name] = pin(output / name, len(rows))
    write_json(output / 'split.json', split)
    artifacts['split.json'] = pin(output / 'split.json')
    return artifacts


def process_scene(row, conventions, config, commit, job_roots, blocked, split):
    dataset, name = safe_scene(row)
    entry = {'dataset': dataset, 'scene_name': name, 'attempts': [], 'rows': 0, 'status': 'deferred_no_readable_receipt'}
    try:
        refuse_blocked(dataset, name, blocked)
    except ValueError as error:
        entry.update(status='deferred_benchmark_scene_group', reason=str(error))
        return [], entry
    entry['split'] = split.side(dataset, name)
    for path in receipt_candidates(row, job_roots):
        if not path.is_file():
            entry['attempts'].append({'path': str(path), 'reason': 'receipt_missing'})
            continue
        try:
            scene = load_scene(path)
            if safe_scene(scene.receipt) != (dataset, name):
                raise ValueError('receipt differs from prepared scene identity')
            generated, coverage = generate_scene(scene, conventions, seed=config['seed'], density=config['density'],
                                                   config_sha=digest(config), commit=commit, structure=config.get('structure', 'v1'))
            repeated, repeated_coverage = generate_scene(scene, conventions, seed=config['seed'], density=config['density'],
                                                          config_sha=digest(config), commit=commit, structure=config.get('structure', 'v1'))
            if canonical(generated) != canonical(repeated) or coverage != repeated_coverage:
                raise RuntimeError('same-seed generation is not byte-identical')
            entry.update(coverage, status='generated' if generated else 'deferred_no_observable_measurements',
                         receipt=pin(path), assets={key: scene.receipt[key] for key in ('dense', 'calibration', 'instances', 'instance_mesh', 'annotations', 'alignment', 'source_provenance', 'video')},
                         rgb_frames=scene.receipt['frames'], same_seed_repeat_byte_identical=True)
            return generated, entry
        except (OSError, ValueError, KeyError, TypeError) as error:
            entry['attempts'].append({'path': str(path), 'reason': type(error).__name__ + ': ' + str(error)})
            entry['status'] = 'deferred_invalid_assets'
    return [], entry


def load_authority_samples(path, expected_sha, manifest):
    if not expected_sha:
        raise ValueError('cached wording samples require --authorities-sha256')
    verify_pin({'path': str(path), 'sha256': expected_sha})
    samples = read_json(path)
    authorities = manifest['benchmark_blocking']['eval_files']
    expected = {'vsi': manifest['source'], 'vsti': authorities['vstibench_full'], 'vsibench': authorities['vsibench_full']}
    for name, required in expected.items():
        spec = samples[name]['authority']
        if spec['sha256'] != required['sha256'] or Path(spec['path']).resolve() != Path(required['path']).resolve():
            raise ValueError('cached wording samples cite a foreign authority')
        verify_pin(spec)
    return samples


def run(args):
    commit = source_commit()
    structure = getattr(args, 'structure', 'v1')
    if args.density < 1 or args.density > 99999 or args.limit is not None and args.limit < 1:
        raise ValueError('density and optional scene limit must be positive')
    prepared = read_json(args.prepared_scenes)
    keys = [safe_scene(row) for row in prepared]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate prepared scene')
    if args.prepared_scenes.resolve() == PREPARED.resolve() and len(prepared) != 306:
        raise ValueError('prepared training-scene census must remain 306')
    manifest = read_json(args.v3_manifest)
    evaluation, blocked = benchmark_blocking(manifest['benchmark_blocking']['eval_files'])
    split = load_split(args.split)
    samples = load_authority_samples(args.authorities, args.authorities_sha256, manifest) if args.authorities else collect(manifest=args.v3_manifest)
    conventions = harvest(samples, structure=structure)
    conventions['measurements'] = {
        family: {**measure, 'authority_evidence': [
            {'authority': conventions['authorities']['vsti' if kind == 'camera_obj_abs_dist' else 'vsi'],
             'question_type': kind, 'line': conventions['templates'][kind][0]['source_line']}
            for kind, name in TYPE_FAMILY.items() if name == family]}
        for family, measure in MEASURES.items()}
    conventions['sample_cache'] = pin(args.authorities) if args.authorities else None
    config = {'schema': 'gtmeasure-config-v1', 'seed': args.seed, 'density': args.density,
              'conventions_sha256': digest(conventions), 'source_sha256': digest(sources(structure)),
              'dependencies': {name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'shapely')},
              'selection': 'seeded hash order; round-robin across five families; no duplicate student input',
              'visibility': 'all counted category instances appear in selected RGB; metric objects have unique labels; MC pools co-occur in an authenticated frame',
              'output_schema': 'RGB-only student_input; compact_counted_v1 target; privileged geometry only in supervision/provenance'}
    if structure == 'v2':
        config['structure'] = structure
    selected = sorted(prepared, key=safe_scene)
    if args.scene:
        requested = set(args.scene)
        selected = [row for row in selected if '/'.join(safe_scene(row)) in requested]
        if len(selected) != len(requested):
            raise ValueError('requested scene is absent from prepared membership')
    if args.limit:
        selected = selected[:args.limit]
    selected_keys = {safe_scene(row) for row in selected}
    output = new_output(args.output)
    checkpoints = output / 'scene_checkpoints'
    checkpoints.mkdir()
    write_json(output / 'CONFIG.json', {'repo_commit': commit, 'config': config, 'config_sha256': digest(config)})
    write_json(output / 'CONVENTIONS.json', conventions)
    coverage, all_rows = [], []
    for number, row in enumerate(selected, 1):
        generated, entry = process_scene(row, conventions, config, commit, args.job_root or JOB_ROOTS, blocked, split)
        directory = checkpoints / '__'.join(safe_scene(row))
        directory.mkdir()
        write_jsonl(directory / 'rows.jsonl', generated)
        write_json(directory / 'COVERAGE.json', entry)
        entry['checkpoint'] = {'rows': pin(directory / 'rows.jsonl', len(generated)), 'coverage': pin(directory / 'COVERAGE.json')}
        coverage.append(entry)
        all_rows.extend(generated)
        print(f'{number}/{len(selected)} {row["dataset"]}/{row["scene_name"]}: {entry["status"]}; rows={len(generated)}', flush=True)
    coverage.extend({'dataset': row['dataset'], 'scene_name': row['scene_name'], 'status': 'not_requested', 'rows': 0}
                    for row in prepared if safe_scene(row) not in selected_keys)
    coverage.sort(key=safe_scene)
    all_rows.sort(key=lambda row: row['qid'])
    train, heldout = split.partition(all_rows)
    split_record = split.record(train, heldout)
    artifacts = write_dataset(output, train, heldout, split_record)
    census = {'prepared_scenes': len(prepared), 'selected_scenes': len(selected),
              'by_status': dict(Counter(entry['status'] for entry in coverage)), 'scenes': coverage}
    write_json(output / 'COVERAGE.json', census)
    artifacts.update({name: pin(output / name) for name in ('COVERAGE.json', 'CONFIG.json', 'CONVENTIONS.json')})
    overlap_census = overlap([{'dataset': row['dataset'], 'scene_name': row['scene']} for row in all_rows], evaluation)
    if overlap_census['any']:
        raise ValueError('benchmark scene reached emitted rows')
    report = {'schema': 'gtmeasure-manifest-v1', 'source': 'gtmeasure_v1', 'repo_commit': commit,
              'config': config, 'config_sha256': digest(config), 'source_files': sources(structure),
              'inputs': {'prepared_scenes': pin(args.prepared_scenes, len(prepared)), 'v3_manifest': pin(args.v3_manifest),
                         'split': pin(args.split), 'inherited_split': split.inherited_pin,
                         'wording_authorities': conventions['authorities'], 'authority_samples': conventions['sample_cache'],
                         'job_roots': [str(Path(root).resolve()) for root in args.job_root or JOB_ROOTS]},
              'counts': {'all': counts(all_rows), 'train': counts(train), 'heldout': counts(heldout)},
              'coverage': {key: value for key, value in census.items() if key != 'scenes'},
              'benchmark_blocking': {name: {key: value for key, value in info.items() if key != 'keys'} for name, info in evaluation.items()},
              'overlap': overlap_census, 'split_census': split_record['counts'],
              'determinism': {'repeated_scenes': sum(entry.get('same_seed_repeat_byte_identical', False) for entry in coverage),
                              'row_bytes_identical': all(entry.get('same_seed_repeat_byte_identical') is True for entry in coverage if entry['status'] == 'generated')},
              'artifacts': artifacts, 'independent_review': 'pending; this generator does not grant trainer admission'}
    write_json(output / 'MANIFEST.json', report)
    print(canonical({'counts': report['counts'], 'coverage': report['coverage'], 'split': report['split_census']}), flush=True)
    return 0 if all_rows else 2


def main():
    parser = argparse.ArgumentParser(description='Generate deterministic CPU measurement supervision from authenticated training-scene assets.')
    parser.add_argument('--prepared-scenes', type=Path, default=PREPARED)
    parser.add_argument('--v3-manifest', type=Path, default=V3)
    parser.add_argument('--split', type=Path, default=ARM_C)
    parser.add_argument('--authorities', type=Path, help='Reuse a pinned bounded authority sample instead of parsing VSI-590K again.')
    parser.add_argument('--authorities-sha256', help='Required digest of a reused authority-sample cache.')
    parser.add_argument('--job-root', type=Path, action='append', default=[])
    parser.add_argument('--scene', action='append', default=[], help='Exact dataset/scene from prepared membership; may repeat.')
    parser.add_argument('--limit', type=int, help='Process only the first N requested scenes; retain other scenes in the coverage denominator.')
    parser.add_argument('--structure', choices=('v1', 'v2'), default='v1', help='v2 prepends pinned GT intermediate observations; v1 preserves the original rendering.')
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--density', type=int, default=30, help='Total row cap per scene, shared across the five measurement families.')
    parser.add_argument('--output', type=Path, required=True)
    return run(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
