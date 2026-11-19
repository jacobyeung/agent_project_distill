"""Fixtures for the full fine-tuning evaluator tests: an Orchard generation package with real cached RGB32 frames,
LoRA and full fine-tuning provisional publications built with the trainer's storage.finalize, and a carrier tokenizer."""
import hashlib
import io
import json
import math
import os
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from student_pilot import auxiliary_losses, ddp_config, full_ft, geometry_input, orchard_paths, provisional, storage
from student_pilot.common import binding, load_json
from student_pilot.orchard_eval import contracts
from tests import test_benchmark_eval as benchmark_fixtures
from tests.fullft_toys import tiny_base

LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'
ALL = {'llm': True, 'vision_blocks': True, 'merger': True}
CAMERA = {'weight': 1.0, 'embed_dim': 16, 'num_heads': 2, 'trunk_depth': 1,
          'supervision': {'path': '/fixture/camera_sidecar.jsonl', 'sha256': 'c' * 64}}
FEATURE_DIM = 8
ENCODER = {'name': 'g3t', 'repository': 'fixture', 'revision': 'fixture', 'source_sha256': '0' * 64,
           'input': 'square_pad_518', 'pooling': 'roi_align_valid_region'}


class CarrierTokenizer:
    """The two token ids camera_targets needs: the carrier and the tiny model's video token (61)."""

    def __init__(self, carrier=5):
        self.ids = {'<|fim_middle|>': carrier, '<|video_pad|>': 61}

    def convert_tokens_to_ids(self, token):
        return self.ids.get(token)

    def encode(self, text, add_special_tokens=False):
        return [self.ids[text]] if text in self.ids else [ord(char) for char in text]


def orchard_stack(stack, root):
    """Orchard mode with the test root as the owned project (provisional artifacts and runs stay under it)."""
    stack.enter_context(patch.dict(os.environ, STUDENT_ORCHARD='1', STUDENT_FRAME_ROOT_MAP='',
                                   STUDENT_MODEL_ROOT=str(Path(root) / 'models')))
    stack.enter_context(patch.object(orchard_paths, 'PROJECT', Path(root)))


def png_bytes(array):
    from PIL import Image

    stream = io.BytesIO()
    Image.fromarray(array).save(stream, format='PNG', optimize=False)
    return stream.getvalue()


def generation_manifest(stack, root, rows=2, size=64):
    """A non-paper VSTIBench generation package whose rows share one video with a real 32-frame RGB cache."""
    from student_pilot.orchard_eval.frames import decoder_identity

    root = Path(root)
    folder = root / 'generation'
    video = contracts.write_bytes_once(folder / 'video.bin', b'synthetic media fixture', root)
    contract = {'video_sha256': video['sha256'], 'decoder': decoder_identity(), 'preprocessing': contracts.RGB}
    cache = folder / 'frames' / contracts.digest(contract)
    records = []
    for index in range(32):
        array = ((np.arange(size * size * 3, dtype=np.int64).reshape(size, size, 3) * (index + 3)) % 251).astype(np.uint8)
        pin = contracts.write_bytes_once(cache / f'frame_{index:08d}.png', png_bytes(array), root)
        records.append({'index': index, 'pts_seconds': index / 2, 'width': size, 'height': size, 'png': pin,
                        'rgb_sha256': hashlib.sha256(array.tobytes(order='C')).hexdigest()})
    selection = [{'index': row['index'], 'pts_seconds': row['pts_seconds'], 'png_sha256': row['png']['sha256'],
                  'rgb_sha256': row['rgb_sha256']} for row in records]
    receipt = contracts.write_once(cache / 'selection.json', {
        'schema': 'rgb32-selection-v1', 'cache_contract': contract, 'cache_id': contracts.digest(contract),
        'total_num_frames': 32, 'fps': 2.0, 'fps_rational': {'numerator': 2, 'denominator': 1},
        'frame_indices': list(range(32)), 'frames': records, 'ordered_selection_sha256': contracts.digest(selection)}, root)
    items = [{'qid': f'synthetic-{index}', 'video_id': 'synthetic-video', 'student_input': {
              'question': f'Synthetic question {index}?', 'options': ['A. red', 'B. blue'],
              'options_serialization': 'A. red\nB. blue', 'video_path': video['path'],
              'video_sha256': video['sha256'], 'frame_receipt': receipt}} for index in range(rows)]
    ids = [row['qid'] for row in items]
    source = {key: items[0]['student_input'][key] for key in ('video_path', 'video_sha256', 'frame_receipt')}
    manifest = {'schema': 'student-generation-manifest-v1', 'benchmark': 'vstibench_repr450_v2',
                'paper_cell': False, 'ordered_ids': ids, 'expected_count': rows, 'preprocessing': contracts.RGB,
                'cohort_authority_sha256': 'a' * 64, 'guard': None, 'media_roots': [str(folder)],
                'config': contracts.write_once(folder / 'config.json', contracts.DEFAULT_CONFIG, root),
                'inputs': contracts.write_bytes_once(folder / 'inputs.jsonl', contracts.jsonl_bytes(items), root),
                'media': contracts.write_once(folder / 'media.json', {'synthetic-video': source}, root),
                'membership': contracts.write_once(folder / 'membership.json', {'qids': ids}, root),
                'admission_input': contracts.write_once(folder / 'admission_input.json', items, root),
                **contracts.prompt_provenance(contracts.DEFAULT_CONFIG)}
    path = folder / 'manifest.json'
    contracts.write_once(path, manifest, root)
    attestation = contracts.write_once(root / 'attestation.json', {
        'schema': 'orchard-prepared-media-attestation-v1', 'manifests': {
            str(path): {'manifest': contracts.binding(path), 'media': manifest['media'], 'videos': {video['path']: source}}}}, root)
    stack.enter_context(patch.dict(os.environ, ORCHARD_MEDIA_ATTESTATION=attestation['path'],
                                   ORCHARD_MEDIA_ATTESTATION_SHA256=attestation['sha256']))
    return path, [row['png']['sha256'] for row in records]


SCORER_PROJECT = Path(os.environ.get('STUDENT_EVAL_PROJECT_ROOT', '/home/jjyeung/agent_project'))


def scoring_manifest(root, generation):
    """The scoring package of generation_manifest's cohort: multiple-choice VSTI labels and the pinned scorer sources."""
    from student_pilot.orchard_eval.prepare import COMPOSITE_SHA, SCORER_SHA

    root, generation = Path(root), Path(generation)
    public = load_json(generation)
    items = contracts.load_jsonl(public['inputs']['path'])
    labels = [{'id': item['qid'], 'question_type': 'camera_movement_direction', 'ground_truth': 'AB'[index % 2],
               'question': item['student_input']['question'], 'options': item['student_input']['options'],
               'group_id': None, 'variant': None} for index, item in enumerate(items)]
    folder = root / 'scoring'
    label_pin = contracts.write_bytes_once(folder / 'labels.jsonl', contracts.jsonl_bytes(labels), root)
    scorer = {'implementation': contracts.binding(SCORER_PROJECT / 'agent/evaluation/scoring.py', SCORER_SHA),
              'composite': contracts.binding(SCORER_PROJECT / 'agent/evaluation/score_record_core.py', COMPOSITE_SHA)}
    manifest = {'schema': 'student-scoring-manifest-v1', 'benchmark': public['benchmark'], 'paper_cell': False,
                'generation': contracts.binding(generation), 'labels': label_pin, 'source_bindings': [], 'scorer': scorer,
                'ordered_ids': public['ordered_ids'], 'expected_count': len(public['ordered_ids'])}
    contracts.write_once(folder / 'manifest.json', manifest, root)
    return folder / 'manifest.json'


def write_store(root, rows, cells, seed=5):
    """A sealed geometry feature store: one float16 row [32, *cells, FEATURE_DIM] per ordered frame selection."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    generator = np.random.default_rng(seed)
    lines = []
    for index, frames in enumerate(rows):
        array = generator.standard_normal((32, *cells, FEATURE_DIM)).astype(np.float16)
        np.save(root / f'v{index}.npy', array)
        lines.append(json.dumps({'key': geometry_input.frame_key(frames), 'frames': frames, 'file': f'v{index}.npy',
                                 'sha256': geometry_input.file_sha256(root / f'v{index}.npy'),
                                 'shape': [32, *cells, FEATURE_DIM], 'dtype': 'float16', 'layer': 23, 'encoder': ENCODER}))
    (root / 'manifest.jsonl').write_text('\n'.join(lines) + '\n')
    return {'manifest': str(root / 'manifest.jsonl'), 'manifest_sha256': geometry_input.file_sha256(root / 'manifest.jsonl')}


def geometry_settings(store, injection=geometry_input.INJECTION):
    return {'schema': geometry_input.SCHEMA, 'injection': injection, 'layer': 23, 'feature_dim': FEATURE_DIM,
            'frames_per_token': 2, 'projector': dict(geometry_input.INJECTIONS[injection]), 'encoder': dict(ENCODER),
            'store': dict(store)}


def fixture_frames(video):
    return [hashlib.sha256(f'video{video}:frame{index}'.encode()).hexdigest() for index in range(32)]


class PublicationFixtures:
    """Mixed into a TestCase: provisional DDP publications (LoRA or full fine-tuning) under an Orchard-owned root."""

    def publication_setup(self):
        from tests import test_ddp_pipeline, test_provisional, test_provisional_pipeline

        test_provisional.ProvisionalTests.setUp(self)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        orchard_stack(self.stack, self.root)
        self._ddp = test_ddp_pipeline.DDPProtocolTests
        self._pipeline = test_provisional_pipeline.ProvisionalPipelineTests

    # The trainer fixtures read these through self.
    def document(self, name, value):
        from tests import test_provisional
        return test_provisional.ProvisionalTests.document(self, name, value)

    def candidates(self, count=20):
        from tests import test_provisional
        return test_provisional.ProvisionalTests.candidates(self, count)

    def index(self, entries, name='candidate_index.jsonl'):
        from tests import test_provisional
        return test_provisional.ProvisionalTests.index(self, entries, name)

    def prepare_pool(self, student='onethinker'):
        return self._pipeline.prepare_pool(self, student)

    def ddp_pool(self, student='onethinker', label=LABEL, config=None):
        return self._ddp.ddp_pool(self, student, label, config)

    def finalize(self, run, name):
        publish = orchard_paths.PROJECT / 'runs' / name
        receipt = storage.finalize(run, publish, self.root, provisional_diagnostic=LABEL)
        return publish / receipt['adapter_directory'], publish / 'PUBLISHED.json'

    def lora_publication(self, student='onethinker', name='lora'):
        run = self._ddp.completed_run(self, student)
        return self.finalize(run, name)

    def full_publication(self, student='qwen35', train=ALL, camera=None, geometry=None, carrier=13, name='fullft',
                         seed=5):
        """A completed full fine-tuning (or frozen-VLM) run of the tiny base, published by storage.finalize.

        Full weights are the BF16 export of a seeded FP32 tiny base (several shards); camera adds auxiliary heads with
        random camera tokens and the given carrier id; geometry adds a random projector for the given settings."""
        config = {'parallel': 'fsdp', 'full_ft': {'train': train}}
        if camera is not None:
            config['camera'] = camera
        if geometry is not None:
            config['geometry'] = geometry
        self.ddp_pool(student, config=config)
        protocol, settings = self.protocol, self.protocol['training']
        manifest = load_json(self.training_path)
        count = manifest['counts']['training_rows']
        batch = settings['effective_batch_size']
        steps = math.ceil(count / batch) * settings['epochs']
        tagged = provisional.tag({'student': student, 'PROVISIONAL_DIVISION_SHA': protocol['PROVISIONAL_DIVISION_SHA']}, LABEL)
        store = storage.RunArtifacts(self.root / f'training_{name}', tagged, self.root)
        directory = store.root / provisional.adapter_directory(LABEL)
        directory.mkdir()
        block = settings['full_ft']
        _, report = full_ft.prepare_model(tiny_base(student), block)
        record = {key: report[key] for key in ('schema', 'mode', 'train', 'learning_rates', 'group_parameters',
                                                'trainable_parameters', 'base_parameters')}
        if full_ft.frozen_vlm(block):
            adapter = {'frozen_vlm': True}
        else:
            trained = tiny_base(student, dtype=torch.float32, seed=seed)
            names = [name for name, _ in full_ft.base_parameters(trained)]
            state = {name: parameter.detach() for name, parameter in trained.named_parameters()}
            with patch.object(full_ft, 'EXPORT_SHARD_BYTES', 4096):
                export = full_ft.save_export(full_ft.export_tensors(state, names), directory / full_ft.EXPORT_DIRECTORY,
                                             {'student': student, 'base': protocol['base'], 'base_sha256': protocol['base_sha256']},
                                             {key: record[key] for key in ('mode', 'train', 'group_parameters',
                                                                           'trainable_parameters', 'base_parameters')})
            adapter = {'full_weights': binding(directory / full_ft.EXPORT_DIRECTORY / full_ft.EXPORT_MANIFEST),
                       'full_weights_bytes': export['bytes'], 'full_weights_tensors': export['tensor_count']}
        store.write(f'{directory.name}/provenance.json', {'adapter': adapter, 'protocol_version': ddp_config.VERSION})
        heads_pin = None
        if camera is not None:
            heads = auxiliary_losses.attach(tiny_base(student), None, CarrierTokenizer(carrier), camera)
            torch.manual_seed(seed + 1)
            with torch.no_grad():
                heads.camera.tokens.copy_(torch.randn_like(heads.camera.tokens))
            path = store.root / 'auxiliary_heads.pt'
            torch.save({key: value.detach().cpu() for key, value in heads.state_dict().items()}, path)
            heads_pin = binding(path)
            store.write('auxiliary_heads.json', {'weights': heads_pin, **heads.manifest()})
        geometry_result = None
        if geometry is not None:
            module = geometry_input.GeometryInput(geometry_input.normalize(geometry), 16)
            torch.manual_seed(seed + 2)
            with torch.no_grad():
                for parameter in module.projector.parameters():
                    parameter.copy_(torch.randn_like(parameter) * 0.5)
            (store.root / 'geometry').mkdir()
            geometry_input.save(module, store.root / 'geometry')
            geometry_result = {'weights': binding(store.root / 'geometry' / geometry_input.WEIGHTS_NAME),
                               'manifest': binding(store.root / 'geometry' / geometry_input.MANIFEST_NAME),
                               'parameters': sum(p.numel() for p in module.projector.parameters())}
        for step in range(1, steps + 1):
            store.write(f'steps/{step:04d}.json', {'step': step})
        store.write('throughput.json', {'synthetic': True, 'world_size': settings['world_size']})
        (store.root / 'train.log').write_text(f'{LABEL} synthetic CPU full fine-tuning publication fixture\n')
        result = {'schema': 'completed-provisional-diagnostic-training-v1', 'status': 'TRAINED', 'student': student,
                  'synthetic': True, 'base': protocol['base'], 'base_sha256': protocol['base_sha256'],
                  'base_restart': 'fresh_load_of_original_snapshot_no_smoke_adapter', 'protocol': binding(self.protocol_path),
                  'training_manifest': binding(self.training_path), 'adapter': adapter,
                  'adapter_parameters': record['trainable_parameters'], 'protocol_version': ddp_config.VERSION,
                  'training_sha256': protocol['training_sha256'], 'settings': settings,
                  'run_control': protocol['run_control'], 'run_control_sha256': protocol['run_control_sha256'],
                  'dataset_counts': manifest['counts'], 'frozen_base_unchanged': True, 'completed_epochs': settings['epochs'],
                  'rank_checks': [{'rank': rank, 'frozen_base_unchanged': True} for rank in range(settings['world_size'])],
                  'realized': {'optimizer_steps': steps, 'training_rows': steps * batch, 'source_rows': count * settings['epochs'],
                               'epoch_padding_rows': steps * batch - count * settings['epochs']},
                  'full_ft': record, 'auxiliary_heads': heads_pin,
                  **({'camera': protocol['camera'], 'camera_sha256': protocol['camera_sha256']} if 'camera' in protocol else {}),
                  **({'geometry': geometry_result} if geometry_result is not None else {})}
        ddp_config.validate_training_result(store.record(result), protocol, LABEL)
        store.write('training_result.json', result)
        store.write('run.json', result)
        store.write('input_manifest.json', {'rows': manifest['rows']})
        return self.finalize(store.root, name)


def rewrite_census(publish, change):
    """Apply change(files) to a publication's SHA256 census and rebind its receipt (for refusal tests)."""
    from student_pilot.common import canonical_bytes

    publish = Path(publish)
    census = load_json(publish / 'SHA256_MANIFEST.json')
    change(census['files'])
    (publish / 'SHA256_MANIFEST.json').write_bytes(canonical_bytes(census))
    receipt = load_json(publish / 'PUBLISHED.json')
    receipt.update(sha256_manifest=binding(publish / 'SHA256_MANIFEST.json'), file_count=len(census['files']))
    (publish / 'PUBLISHED.json').write_bytes(canonical_bytes(receipt))


def tiny_batch(student='qwen35'):
    """One native prompt of the tiny base: 16 temporal groups of one merged video token each, BF16 pixels."""
    from tests.test_ddp_models import NativeMultimodalBatchTests

    row = NativeMultimodalBatchTests.fixture(student)[3][0]
    prompt = int((row['labels'] == -100).sum())
    batch = {key: value[:, :prompt] if key in ('input_ids', 'attention_mask', 'mm_token_type_ids') else value
             for key, value in row.items() if key != 'labels'}
    return {key: value.to(torch.bfloat16) if value.is_floating_point() else value for key, value in batch.items()}
