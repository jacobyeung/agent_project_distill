import csv
import io
import json
import re
from collections import Counter
from pathlib import Path

from .answers import option_letters
from .contracts import (BENCHMARKS, COUNTS, MEMBERSHIP_SHA, RGB, VARIANTS, binding, contained, digest,
                        guard_inputs, jsonl_bytes, load_config, load_json, new_directory,
                        validate_input, write_bytes_once, write_once)
from .frames import cache_selection


VSTI_SHA = '54d93aeecf16921d0c26df732103d7838095dc8931938f0108abef5a819e8294'
VSTI_PROVENANCE_SHA = '5b51d4f5fd052fafa3bfe7e59b81d9dce462bf0b5249344c330b7fd6e7ee40c7'
VSI_LABEL_SHA = 'c23cb4d5e80517ee768829301c2fcd95b9dae43ade30249d8dbaf37de7cc8532'
SCORER_SHA = 'f67703ea8fbca0db13f922e34dc778ead6a546e0b574435e8924c00da6b609c5'
COMPOSITE_SHA = '503a16f193cc4974e4904103eda35138420dfc8c71dac48574d304d52c8194a9'
DSI_REVISION = '7e3be50cda54f98e8ce11fe89696b5b1ed246801'
DSI_COMMIT = 'af90adcd760f2757f8b8dbd869ae9a821f725513'
DSI_SCORER_SHA = 'd1df7b19208892dba6e7b6410342affeb8da02bbe2849c6287b499503fd73c33'
VSI_CATEGORIES = {'object_counting', 'object_abs_distance', 'object_size_estimation', 'room_size_estimation',
                  'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
                  'object_rel_distance', 'route_planning', 'obj_appearance_order'}
VSTI_CATEGORIES = {'camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3',
                   'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf', 'obj_obj_relative_pos_ud',
                   'camera_obj_abs_dist', 'camera_displacement', 'camera_movement_direction'}
NUMERIC = {'object_counting', 'object_abs_distance', 'object_size_estimation', 'room_size_estimation',
           'camera_obj_abs_dist', 'camera_displacement'}


def numeric_qid(value):
    if isinstance(value, bool) or not re.fullmatch(r'0|[1-9][0-9]*', str(value)):
        raise ValueError('VSI/VSTI ids must be original nonnegative integers')
    return str(value)


def question_rows(path):
    rows = load_json(path)
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        raise ValueError('Official VSI/VSTI question authority must be a nonempty JSON list')
    ids = [numeric_qid(row['id']) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate question ids')
    return rows


def membership_rows(path):
    document = load_json(path)
    if isinstance(document, list):
        values = document
    elif isinstance(document, dict):
        keys = [name for name in ('qids_int_sorted', 'qids', 'question_ids', 'members', 'membership', 'questions', 'items', 'rows', 'data')
                if isinstance(document.get(name), list)]
        if keys:
            values = document[keys[0]]
        elif isinstance(document.get('qids_by_category'), dict):
            values = [qid for group in document['qids_by_category'].values() for qid in group]
        else:
            raise ValueError('Membership has no recognized qid list')
    else:
        raise ValueError('Invalid membership document')
    ids, identities = [], {}
    for value in values:
        item = value if isinstance(value, dict) else {}
        qid = numeric_qid(next((item[key] for key in ('qid', 'id', 'question_id') if key in item), None) if item else value)
        ids.append(qid)
        identities[qid] = item
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('Duplicate or empty membership')
    if isinstance(document, dict) and isinstance(document.get('qids_by_category'), dict):
        category_ids = []
        for category, group in document['qids_by_category'].items():
            for value in group:
                qid = numeric_qid(value)
                category_ids.append(qid)
                identities.setdefault(qid, {})['question_type'] = category
        if Counter(ids) != Counter(category_ids):
            raise ValueError('Membership category and qid lists disagree')
    return ids, identities


def resolve_video(media_root, dataset, scene, media_index=None):
    for value in (dataset, scene):
        if not isinstance(value, str) or not value or '/' in value or '\\' in value or '..' in value:
            raise ValueError('Dataset/scene must be safe namespace components')
    key = f'{dataset}:{scene}'
    if media_index is not None:
        if key not in media_index or not isinstance(media_index[key], str):
            raise ValueError(f'Missing dataset-qualified media index entry: {key}')
        return contained(media_root, media_index[key])
    candidates = [contained(media_root, f'{dataset}/{scene}.mp4'), contained(media_root, f'{dataset}_{scene}.mp4')]
    found = [path for path in candidates if path.is_file()]
    if len(found) != 1:
        raise ValueError(f'Expected one dataset-qualified video for {key}; supply an explicit media index if needed')
    return found[0]


def load_vsi(data_root, media_root, membership, project_root, synthetic=False, media_index=None):
    authority = contained(data_root, 'answerable500_gt_canonical.json')
    label_pin = binding(authority, None if synthetic else VSI_LABEL_SHA)
    membership_pin = binding(membership, None if synthetic else MEMBERSHIP_SHA)
    ids, identities = membership_rows(membership)
    source = question_rows(authority)
    by_id = {numeric_qid(row['id']): row for row in source}
    if set(by_id) != set(ids) or not synthetic and len(ids) != 500:
        raise ValueError('VSIBench membership/labels must join exactly, with no missing or extra qids')
    for qid, identity in identities.items():
        for field in ('dataset', 'scene_name', 'question_type'):
            if field in identity and identity[field] != by_id[qid].get(field):
                raise ValueError(f'Membership identity mismatch: {qid} {field}')
    guard = {'source': binding(Path(project_root) / 'agent/scripts/cohort_guard.py'),
             'registry': binding(Path(project_root) / 'agent/evaluation/RETIRED_COHORTS.json')}
    guard_inputs(guard['source'], guard['registry'], [membership])
    rows = [by_id[qid] for qid in ids]
    return _adapt_vsi_rows(rows, media_root, VSI_CATEGORIES, media_index), [label_pin, membership_pin], membership_pin['sha256'], guard


def load_vsti(data_root, media_root, provenance=None, synthetic=False, media_index=None):
    authority = contained(data_root, 'vstibench_repr_450_v2.json')
    provenance = Path(provenance) if provenance else authority.with_suffix(authority.suffix + '.provenance')
    source_pin = binding(authority, None if synthetic else VSTI_SHA)
    provenance_pin = binding(provenance, None if synthetic else VSTI_PROVENANCE_SHA)
    rows = question_rows(authority)
    proof = load_json(provenance)
    if (proof.get('schema') != 'vstibench-repr450-v2-canonical-provenance-v1'
            or proof.get('artifact', {}).get('sha256') != source_pin['sha256']
            or proof['artifact'].get('rows') != len(rows) or not synthetic and len(rows) != 450):
        raise ValueError('Canonical VSTIBench provenance does not bind these questions')
    for row in rows:
        mapping = row.get('answer_mapping')
        if not isinstance(mapping, dict) or set(mapping) != {'letter', 'text'}:
            raise ValueError('Canonical VSTIBench answer mapping is required offline')
        if row['question_type'] in NUMERIC:
            expected = {'letter': None, 'text': str(row['ground_truth'])}
        else:
            letters = option_letters(row.get('options'))
            if row['ground_truth'] not in letters:
                raise ValueError('VSTIBench label is not an option letter')
            option = row['options'][letters.index(row['ground_truth'])]
            expected = {'letter': row['ground_truth'], 'text': option.split('.', 1)[1].strip()}
        if mapping != expected:
            raise ValueError('VSTIBench letter/text mapping differs from the original option')
    return _adapt_vsi_rows(rows, media_root, VSTI_CATEGORIES, media_index), [source_pin, provenance_pin], source_pin['sha256'], None


def _adapt_vsi_rows(rows, media_root, categories, media_index):
    adapted = []
    for row in rows:
        category = row['question_type']
        if category not in categories:
            raise ValueError(f'Unknown benchmark category: {category}')
        options = row.get('options') or []
        if not isinstance(options, list):
            raise ValueError('VSI/VSTI options must be an original list')
        letters = option_letters(options)
        if category not in NUMERIC and (len(letters) < 2 or row['ground_truth'] not in letters):
            raise ValueError('Malformed multiple-choice options or label')
        if category in NUMERIC and options:
            raise ValueError('Numeric question unexpectedly has choice options')
        video = resolve_video(media_root, row['dataset'], row['scene_name'], media_index)
        adapted.append({'qid': numeric_qid(row['id']), 'video_id': f'{row["dataset"]}:{row["scene_name"]}',
                        'question': row['question'], 'options': options, 'video_path': str(video), 'video_sha256': None,
                        'label': {**row, 'id': numeric_qid(row['id']), 'options': options, 'group_id': None, 'variant': None}})
    return adapted


def load_dsi(data_root, manifest_path=None, synthetic=False):
    root = Path(data_root).resolve()
    manifest_path = Path(manifest_path) if manifest_path else root / 'MANIFEST.json'
    binding(manifest_path, None if synthetic else 'e19ae9d1b1b35aacbbe04fbbc07a4337c6e3ba5de000b88bf40a56a13bc791f1')
    manifest = load_json(manifest_path)
    if (manifest.get('schema') != 'dsibench-acquisition-v1' or manifest.get('status') != 'COMPLETE'
            or manifest.get('revision') != DSI_REVISION or manifest.get('official_repo_commit') != DSI_COMMIT):
        raise ValueError('DSI acquisition manifest is incomplete or unpinned')
    files = {entry['path']: entry for entry in manifest['files']}
    if len(files) != len(manifest['files']):
        raise ValueError('Duplicate DSI manifest paths')
    csv_rows, sources = {}, [binding(manifest_path)]
    for variant in VARIANTS:
        name = f'metadatas/{variant}.csv'
        pin = binding(contained(root, name), files[name]['sha256'])
        if files[name].get('status') != 'verified' or files[name]['size_bytes'] != pin['size_bytes']:
            raise ValueError('Unverified DSI CSV')
        sources.append(pin)
        with Path(pin['path']).open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != ['cate', 'relative_path', 'video_type', 'question', 'options', 'GT', 'others']:
                raise ValueError('DSI CSV columns differ from the official format')
            csv_rows[variant] = list(reader)
    lengths = [len(csv_rows[variant]) for variant in VARIANTS]
    if not lengths[0] or len(set(lengths)) != 1 or not synthetic and lengths[0] != 1769:
        raise ValueError('All four DSI variants must have the exact group census')
    adapted, clips = [], set()
    for variant in VARIANTS:
        for ordinal, row in enumerate(csv_rows[variant]):
            standard = csv_rows['std'][ordinal]
            if (row['relative_path'], row['cate']) != (standard['relative_path'], standard['cate']):
                raise ValueError('DSI variants are missing or reordered by original row ordinal')
            if not re.fullmatch(r'[0-5]', row['cate']) or option_letters(row['options']) != ['A', 'B', 'C', 'D'] or row['GT'] not in 'ABCD' or len(row['GT']) != 1:
                raise ValueError('Malformed DSI category/options/label')
            relative = f'videos/{variant}/{row["relative_path"]}'
            video = contained(root, relative)
            if relative not in files or files[relative].get('status') != 'verified':
                raise ValueError(f'Unverified DSI video: {relative}')
            clips.add(row['relative_path'])
            qid = f'dsibench:{variant}:{ordinal}'
            adapted.append({'qid': qid, 'video_id': f'dsibench:{variant}:{row["relative_path"]}',
                            'question': row['question'], 'options': row['options'], 'video_path': str(video),
                            'video_sha256': files[relative]['sha256'],
                            'label': {'id': qid, 'question_type': row['cate'], 'ground_truth': row['GT'],
                                      'question': row['question'], 'options': row['options'], 'group_id': ordinal,
                                      'variant': variant, 'relative_path': row['relative_path']}})
    if not synthetic and len(clips) != 943:
        raise ValueError('DSI referenced-clip census must be exactly 943')
    official = contained(root, 'official_repo/evaluate.py')
    official_pin = binding(official, DSI_SCORER_SHA)
    if files['official_repo/evaluate.py']['sha256'] != official_pin['sha256']:
        raise ValueError('Official DSI scorer differs from acquisition')
    sources.append(official_pin)
    return adapted, sources, binding(manifest_path)['sha256'], None


def prepare(benchmark, config_path, output, artifact_root, data_root, media_root=None, membership=None,
            provenance=None, project_root=None, dataset_manifest=None, media_index=None, synthetic=False):
    if benchmark not in BENCHMARKS:
        raise ValueError('Unsupported benchmark; no full-VSIBench shortcut')
    paper = not synthetic
    output = new_directory(output, artifact_root, paper)
    report = {'schema': 'student-preparation-report-v1', 'status': 'BLOCKED', 'benchmark': benchmark,
              'paper_cell': paper, 'media_failures': [], 'cpu_preflight_required': ['onethinker', 'qwen35']}
    try:
        config = load_config(config_path)
        index = load_json(media_index) if media_index else None
        if benchmark == BENCHMARKS[0]:
            if not all((media_root, membership, project_root)):
                raise ValueError('VSI requires explicit media, membership, and project roots')
            adapted, sources, authority, guard = load_vsi(data_root, media_root, membership, project_root, synthetic, index)
        elif benchmark == BENCHMARKS[1]:
            if not media_root or not project_root:
                raise ValueError('VSTI requires explicit media and project roots')
            adapted, sources, authority, guard = load_vsti(data_root, media_root, provenance, synthetic, index)
        else:
            adapted, sources, authority, guard = load_dsi(data_root, dataset_manifest, synthetic)
        if paper and len(adapted) != COUNTS[benchmark]:
            raise ValueError('Paper cohort membership count changed')
        if media_index:
            sources.append(binding(media_index))
        generation = output / 'generation'
        generation.mkdir()
        media, rows, labels = {}, [], []
        for item in adapted:
            video_id = item['video_id']
            if video_id not in media:
                try:
                    video_pin = binding(item['video_path'], item['video_sha256'])
                    frame_pin = cache_selection(item['video_path'], generation / 'frames', artifact_root, paper)
                    media[video_id] = {'video_path': item['video_path'], 'video_sha256': video_pin['sha256'], 'frame_receipt': frame_pin}
                except (ValueError, OSError, RuntimeError) as error:
                    report['media_failures'].append({'video_id': video_id, 'video_path': item['video_path'], 'error': str(error)})
                    media[video_id] = None
            if media[video_id] is None:
                continue
            options = item['options']
            row = {'qid': item['qid'], 'video_id': video_id,
                   'student_input': {'question': item['question'], 'options': options,
                                     'options_serialization': '\n'.join(options) if isinstance(options, list) else options, **media[video_id]}}
            rows.append(validate_input(row))
            labels.append(item['label'])
        report.update(expected_count=len(adapted), prepared_questions=len(rows), media_count=len(media), source_bindings=sources)
        if report['media_failures']:
            raise ValueError('Required media are missing or invalid; membership was not reduced')
        ids = [row['qid'] for row in rows]
        config_pin = write_bytes_once(generation / 'config.json', Path(config_path).read_bytes(), artifact_root, paper)
        inputs_pin = write_bytes_once(generation / 'inputs.jsonl', jsonl_bytes(rows), artifact_root, paper)
        media_pin = write_once(generation / 'media.json', media, artifact_root, paper)
        membership_pin = write_once(generation / 'membership.json', {'qids': ids}, artifact_root, paper)
        admission_pin = write_once(generation / 'admission_input.json', rows, artifact_root, paper)
        if guard:
            guard_inputs(guard['source'], guard['registry'], [membership_pin['path'], admission_pin['path']])
        public = {'schema': 'student-generation-manifest-v1', 'benchmark': benchmark, 'paper_cell': paper,
                  'ordered_ids': ids, 'expected_count': len(ids), 'config': config_pin, 'inputs': inputs_pin,
                  'media': media_pin, 'preprocessing': RGB, 'cohort_authority_sha256': authority,
                  'membership': membership_pin, 'admission_input': admission_pin, 'guard': guard,
                  'media_roots': [str(Path(data_root if benchmark == BENCHMARKS[2] else media_root).resolve())]}
        generation_pin = write_once(generation / 'manifest.json', public, artifact_root, paper)
        label_pin = write_bytes_once(output / 'scoring/labels.jsonl', jsonl_bytes(labels), artifact_root, paper)
        if benchmark == BENCHMARKS[2]:
            scorer = {'official': binding(Path(data_root) / 'official_repo/evaluate.py', DSI_SCORER_SHA)}
        else:
            scorer = {'implementation': binding(Path(project_root) / 'agent/evaluation/scoring.py', SCORER_SHA),
                      'composite': binding(Path(project_root) / 'agent/evaluation/score_record_core.py', COMPOSITE_SHA)}
        score_manifest = {'schema': 'student-scoring-manifest-v1', 'benchmark': benchmark, 'paper_cell': paper,
                          'generation': generation_pin, 'labels': label_pin, 'source_bindings': sources,
                          'scorer': scorer, 'ordered_ids': ids, 'expected_count': len(ids)}
        scoring_pin = write_once(output / 'scoring/manifest.json', score_manifest, artifact_root, paper)
        report.update(status='PREPARED_CPU_PREFLIGHT_REQUIRED', generation=generation_pin, scoring=scoring_pin,
                      question_membership_exact=True, frame_selection_checked=True, token_coverage='pending_cpu_check')
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        report.update(error=str(error), error_type=type(error).__name__)
        write_once(output / 'preparation_report.json', report, artifact_root, paper)
        raise
    write_once(output / 'preparation_report.json', report, artifact_root, paper)
    return report


def create_fixture_video(path, frames_root, artifact_root, count=40, variable_rate=False, offset=0):
    import av
    import numpy as np
    from fractions import Fraction
    from PIL import Image
    from .contracts import output_path

    path = output_path(path, artifact_root)
    if path.exists():
        raise ValueError('Synthetic video output already exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    colors = []
    for name in ('red.ppm', 'green.ppm', 'blue.ppm'):
        with Image.open(Path(frames_root) / name) as image:
            colors.append(np.asarray(image.resize((64, 32))).copy())
    with av.open(str(path), mode='w', format='mp4') as container:
        stream = container.add_stream('libx264rgb', rate=24)
        stream.width, stream.height, stream.pix_fmt = 64, 32, 'rgb24'
        stream.options = {'crf': '0', 'preset': 'ultrafast'}
        for index in range(count):
            array = colors[(index + offset) % len(colors)].copy()
            array[0, 0] = [index, offset, 255 - index]
            frame = av.VideoFrame.from_ndarray(array, format='rgb24')
            frame.pts = index + index // 7 if variable_rate else index
            frame.time_base = Fraction(1, 24)
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return binding(path)


def materialize_fixtures(fixtures_root, output, artifact_root):
    fixtures, output = Path(fixtures_root), new_directory(output, artifact_root)
    source_names = ['vsibench/answerable500_gt_canonical.json', 'vsibench/MEMBERSHIP_ANSWERABLE_500.json',
                    'vstibench/vstibench_repr_450_v2.json']
    source_names += [f'dsibench/metadatas/{variant}.csv' for variant in VARIANTS]
    source_names += ['dsibench/official_repo/evaluate.py', 'dsibench/official_repo/LICENSE', 'dsibench/official_repo/SOURCE.json']
    for name in source_names:
        write_bytes_once(output / name, contained(fixtures, name).read_bytes(), artifact_root)
    vsti = output / 'vstibench/vstibench_repr_450_v2.json'
    write_once(vsti.with_suffix(vsti.suffix + '.provenance'),
               {'schema': 'vstibench-repr450-v2-canonical-provenance-v1', 'synthetic': True,
                'artifact': {'path': vsti.name, 'rows': len(load_json(vsti)), 'sha256': binding(vsti)['sha256']}}, artifact_root)
    for index, dataset in enumerate(('scannet', 'arkitscenes')):
        create_fixture_video(output / f'videos/{dataset}/fixture_scene.mp4', fixtures / 'frames', artifact_root, offset=index)
    for index, variant in enumerate(VARIANTS):
        create_fixture_video(output / f'dsibench/videos/{variant}/synthetic/clip.mp4', fixtures / 'frames', artifact_root, offset=index)
    root = output / 'dsibench'
    names = [f'metadatas/{variant}.csv' for variant in VARIANTS]
    names += [f'videos/{variant}/synthetic/clip.mp4' for variant in VARIANTS]
    names += ['official_repo/evaluate.py', 'official_repo/LICENSE']
    files = [{'path': name, **{k: v for k, v in binding(root / name).items() if k != 'path'}, 'status': 'verified'} for name in names]
    write_once(root / 'MANIFEST.json', {'schema': 'dsibench-acquisition-v1', 'status': 'COMPLETE',
                                      'revision': DSI_REVISION, 'official_repo_commit': DSI_COMMIT,
                                      'synthetic': True, 'files': files}, artifact_root)
    return output


def cpu_smoke(config_path, output, artifact_root, fixtures_root, project_root, official_python):
    from .frames import cpu_check
    from .generate import generate_run
    from .score import export_bank, score_run

    output = new_directory(output, artifact_root)
    fixture = materialize_fixtures(fixtures_root, output / 'fixtures', artifact_root)
    results = []
    for benchmark, short in zip(BENCHMARKS, ('vsi', 'vsti', 'dsi')):
        data = fixture / {'vsi': 'vsibench', 'vsti': 'vstibench', 'dsi': 'dsibench'}[short]
        prepared = output / ('nonpaper' if short == 'vsi' else f'nonpaper_{short}')
        prepare(benchmark, config_path, prepared, artifact_root, data, fixture / 'videos',
                fixture / 'vsibench/MEMBERSHIP_ANSWERABLE_500.json', project_root=project_root, synthetic=True)
        for model in ('onethinker', 'qwen35'):
            check = output / f'checks/{short}_{model}'
            cpu_check(prepared / 'generation/manifest.json', model, check, artifact_root, synthetic=True)
            run = output / f'runs/{short}_{model}'
            generation = generate_run(prepared / 'generation/manifest.json', model, 'base', run, artifact_root,
                                      check / 'preflight.json', cpu_mock=True)
            scoring = output / f'scores/{short}_{model}'
            score = score_run(run, prepared / 'scoring/manifest.json', scoring, artifact_root, official_python=official_python)
            bank = export_bank(run, scoring / 'scores.json', f'synthetic_{short}_{model}', output / f'banks/{short}_{model}', artifact_root)
            results.append({'benchmark': benchmark, 'model': model, 'completion': generation,
                            'score': binding(scoring / 'scores.json'), 'bank': bank})
    summary = {'schema': 'student-cpu-smoke-v1', 'status': 'CPU_READY_SYNTHETIC', 'paper_cell': False,
               'gpu_smoke': 'UNTESTED', 'native_checkpoint_processors': 'UNTESTED', 'results': results}
    write_once(output / 'cpu_smoke.json', summary, artifact_root)
    return summary
