"""CPU producer/reader proof. RGB is synthetic and always declared as such."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
import torch
from student_pilot import r2_contract as C, r2_frames as F, r2_grammar as G
from student_pilot import carrier_c1_routing as routing
from student_pilot.p3_provenance import digest, file_pin, load, write
from student_pilot.r2_intake import intake, main as intake_main, text_report
from student_pilot.r2_materialize import materialize, main as materialize_main
from student_pilot.r2_dense import build_training

LANE = Path(os.environ.get('R2_FIXTURES', Path(__file__).resolve().parents[3]))
PROOFS = Path(os.environ.get('R2_PROOFS', os.environ['TMPDIR']))
RECORDS = LANE/'work/records'
SOURCES = dict(benchmark='revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json',
               dev_ids='dose_pool/out/POOL_S1/EXCLUDE_DEV_S1.tsv',
               eval_ids='dose_pool/out/POOL_S1/EXCLUDE_EVAL_ROOMS.tsv',
               frames_gate='dose_pool/out/POOL_S1/FRAMES_GATE.json',
               eval_rooms='own_probe/out/EVAL_ROOMS.json', room_split='ofs_e1/out/ROOM_SPLIT.json',
               dev_manifest='devs1_masks/out/MANIFEST.json')


def directory():
    return Path(tempfile.mkdtemp(prefix='r2_', dir=os.environ['TMPDIR']))


def fixture(root, qid='direct', stream='vqa', fps=10):
    store = root/'frames'
    store.mkdir(exist_ok=True)
    pins = []
    for i in range(64):
        path = store/f'{i}.png'
        if not path.exists():
            Image.new('RGB', (32, 32), (i, 80, 130)).save(path)
        pins.append(dict(path=f'/logical/r2/{i}.png', sha256=file_pin(path)['sha256']))
    indices = list(range(0, 64, 2))
    question = 'Is the stove to the left or right of the sofa?'
    target = '<think>\nLocate: the stove is seen in frame 17.\nLocate: the sofa is seen in frame 2.\nRelate: the stove is to the right of the sofa.\n</think>\n\nA'
    row = dict(qid=qid, dataset='d1', scene='fixture_clean', canonical='scannet/fixture_clean',
               question_type='object_rel_direction_easy', trace_contract=C.CONTRACT,
               question=question, options=['A. right', 'B. left'], answer='A', target=target,
               provenance=dict(canonical='scannet/fixture_clean', source_row_sha256='e'*64, frame_indices=indices),
               student_input=dict(frames=pins[::2], frame_indices=indices, timestamps=[i/fps for i in indices],
                                  fps=fps, total_num_frames=64, question=question, options=['A. right', 'B. left'],
                                  dense_source=dict(frames=[dict(pin, source_index=i) for i, pin in enumerate(pins)])))
    if stream == 'routing':
        events = [dict(kind='plan', text='Call: measure camera displacement between frame 1 and frame 25.'),
                  dict(kind='tool_call', token='<move from=1 to=25>', call_id='move'),
                  dict(kind='tool_response', text='dx = -0.21 m, dy = +0.28 m, dz = -0.07 m, distance = 0.35 m', call_id='move'),
                  dict(kind='canonical_text', text='\nStep: the printed distance is 0.35 m.')]
        answer = '<answer>0.35</answer>'
        target, spans = routing.render(events, answer)
        row.update(schema='derivgen-row-v2', form='spec-v3.8-calculator-v2', infrastructure_only=False,
                   events=events, tool_output_spans=spans, answer=answer, gt_answer='0.35', target=target,
                   question_type='camera_displacement')
        row['provenance']['alias'] = 'd1/fixture_clean'
        row['question'] = row['student_input']['question'] = 'How far in meters did the camera move from frame 1 to frame 25?'
    if stream == 'pose':
        row['student_input']['frame_prefix'] = '/logical/r2'
        row['student_input']['frames'] = [{**p, 'path': Path(p['path']).name} for p in pins[::2]]
        row['target_record'] = dict(camera=[[0., 0., 0., 0., 0., 0., 1., 1., 1.]]*32,
            camera_mask=[True]*32, trajectory_scale=1., gravity=[0., -1., 0.], gravity_mask=True,
            point_depth=dict(uv=[[[500., 500.]]]*32, depth=[[2.]]*32, mask=[[True]]*32))
    if stream == 'pointing':
        row['target'] = '<think>\n\n</think>\n\n{"point_2d": [500, 500]}'
        row['pointing'] = dict(frame=1, kind='gt_instance_mask')
    return row


def manifest(root, rows, stream='vqa', family=None, upstream=False):
    root.mkdir(exist_ok=True)
    path = root/'rows.jsonl'
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    pins = {role: file_pin(RECORDS/name) for role, name in SOURCES.items()}
    coverage = dict(exclusions=pins, rows_sha256=file_pin(path)['sha256'], rows={
        r['qid']: dict(status='known', names=[r['dataset']+'/'+r['scene'], r.get('canonical', 'scannet/fixture_clean')])
        for r in rows})
    write(root/'coverage.json', coverage)
    previous = []
    if upstream:
        write(root/'upstream.json', dict(exclusions=pins, counts=dict(example=dict(seen=4, admitted=3, refused=1, reasons={'dev_ids': 1}))))
        previous = [file_pin(root/'upstream.json')]
    result = dict(schema='r2-family-manifest-v1', family=family or stream, stream=stream, count=len(rows),
                  trace_contract=C.CONTRACT, validator_sha256=G.SHARED_SHA256,
                  rows=file_pin(path), row_bindings={r['qid']: digest(r) for r in rows},
                  scene_coverage=file_pin(root/'coverage.json'), exclusions=pins,
                  prefiltered=upstream, upstream_receipts=previous)
    write(root/'MANIFEST.json', result)
    return root/'MANIFEST.json'


class TinyTokenizer:
    """Lossless stand-in for the unavailable pretrained tokenizer."""
    pad_token_id, eos_token_id, eos_token = 0, 1, '<eos>'
    special = {'<eos>': 1, '<|fim_middle|>': 5, '<|video_pad|>': 61}

    def encode(self, text, **kwargs):
        return self(text)['input_ids']

    def __call__(self, text, **kwargs):
        ids, offsets, i = [], [], 0
        while i < len(text):
            token = next((t for t in self.special if text.startswith(t, i)), text[i])
            ids.append(self.special.get(token, ord(token[0])+100))
            offsets.append((i, i+len(token)))
            i += len(token)
        return dict(input_ids=ids, offset_mapping=offsets)

    def decode(self, ids, **kwargs):
        reverse = {v: k for k, v in self.special.items()}
        return ''.join(reverse.get(int(i), chr(int(i)-100) if int(i) >= 100 else '<visual>') for i in ids)

    def convert_tokens_to_ids(self, token):
        return self.special.get(token, self.eos_token_id)


class TinyProcessor:
    """Only the pretrained processor boundary stands in; actual RGB loaders run."""
    video_token_id = 61

    def __init__(self):
        self.tokenizer = TinyTokenizer()
        self.video_processor = SimpleNamespace(merge_size=2, temporal_patch_size=2)

    def apply_chat_template(self, messages, **kwargs):
        prefix = 'Question: '+messages[0]['content'][1]['text']+'\n<think>\n'
        return prefix if len(messages) == 1 else prefix+messages[-1]['content'].removeprefix('<think>\n')+'<eos>\n'

    def __call__(self, text, videos, video_metadata, **kwargs):
        metadata, arrays = video_metadata[0], videos[0]
        ids = self.tokenizer.encode(text[0])
        for i in range(0, len(arrays), 2):
            timestamp = sum(metadata.frames_indices[i:i+2])/(2*metadata.fps)
            ids += self.tokenizer.encode(f'<{timestamp:.1f} seconds>') + [62, 61, 63]
        pixels = arrays[:, ::8, ::8].reshape(len(arrays)//2, 2, 2, 2, 2, 2, 3)
        pixels = pixels.transpose(0, 2, 4, 6, 1, 3, 5).reshape(-1, 24)
        token_ids = torch.tensor([ids])
        return dict(input_ids=token_ids, mm_token_type_ids=torch.where(token_ids == 61, 2, 0), video_grid_thw=torch.tensor([[len(arrays)//2, 2, 2]]),
                    pixel_values_videos=torch.tensor(pixels, dtype=torch.float32)/255)


class GrammarTests(unittest.TestCase):
    def test_all_required_mutations(self):
        bad = ['', 'Relate: The answer is A.', 'Step: So the answer is A.', 'Step: Option A is correct.',
               'Step: think carefully.\nStep: consider the image.', 'Locate: the chair is seen in frame 2 seconds.',
               'Locate: the chair is seen in frames 1, 2, 3.', 'Relate: the chair is absent in frame 2.',
               'Step: estimate 120cm.', 'Step: estimate 3m.', 'Step: estimate 2.5ft.',
               'Step: estimate half a meter.', 'Step: estimate a dozen.', 'Step: estimate a couple of meters.',
               'Step: estimate three meters.', 'Step: estimate 73 meters.', '<move from=1 to=2>',
               '<tool_response>distance 2 m</tool_response>', 'The answer is A.']
        results = []
        for trace in bad:
            with self.subTest(trace=trace), self.assertRaises(ValueError):
                G.validate_direct('<think>\n'+trace+'\n</think>\nA', 'Estimate the object size in meters.', 32)
            results.append(dict(mutation=trace, result='refused'))
        (PROOFS/'MUTATIONS.json').write_text(json.dumps(results, indent=2))

    def test_locate_counts_arithmetic_and_question_constants(self):
        text = '<think>\nLocate: chair a is seen in frame 1.\nLocate: chair b is seen in frame 2.\nStep: list [chair a; chair b]; count = 2.\nStep: compute 2 + 2 = 4.\n</think>\n4'
        self.assertEqual(G.validate_direct(text, 'Count chairs.', 32), '4')
        self.assertEqual(G.arithmetic('2 * 3 - 2 / 2', {2, 3}), 5)
        self.assertEqual(G.validate_direct('<think>\nStep: facing away is a half turn; left and right swap.\n</think>\nA', 'Facing away, which side?', 32), 'A')
        for changed in (text.replace('frame 2', 'frame 33'), text.replace('chair b is', 'chair a is'),
                        text.replace('count = 2', 'count = 3'), text.replace('= 4', '= 5'),
                        text.replace('2 + 2', '2 + 99'), text.replace('2 + 2', '2 / 0')):
            with self.assertRaises(ValueError):
                G.validate_direct(changed, 'Count chairs.', 32)


class DataPathTests(unittest.TestCase):
    def setUp(self):
        self.root = directory()
        self.row = fixture(self.root)
        self.enterContext(patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2': str(self.root/'frames')}), STUDENT_R2_LOCAL_NODE='1'))

    def test_init_warm_start_and_preparation_refusals(self):
        spec = dict(contract=C.CONTRACT, init=INIT, mode='warm_start', run_id='new-run', code_sha256='a'*64, mixture_sha256='b'*64)
        meta = dict(INIT, parent_configuration='a7ad7051-prefix-only')
        self.assertEqual(C.check_init(spec, meta), spec)
        for change in (dict(mode='exact_resume'), dict(run_id='469ddece'), dict(init={}), dict(code_sha256='short')):
            with self.assertRaises(ValueError):
                C.check_init({**spec, **change}, meta)
        for change in (dict(artifact_sha256='0'*64), dict(parent_run='wrong'), dict(parent_configuration='wrong')):
            with self.assertRaises(ValueError):
                C.check_init(spec, {**meta, **change})
        write(self.root/'EXPORT_ARTIFACT.json', meta)
        spec['export_metadata'] = file_pin(self.root/'EXPORT_ARTIFACT.json')
        cfg = dict(r2=spec, init_artifact=dict(artifact=dict(sha256=INIT['artifact_sha256'])))
        write(self.root/'code.json', dict(tree_sha256=spec['code_sha256']))
        write(self.root/'membership.json', dict(contract=C.CONTRACT, rows={}))
        cfg.update(code=file_pin(self.root/'code.json'), r2_membership=file_pin(self.root/'membership.json'))
        spec['mixture_sha256'] = digest({key: cfg.get(key) for key in ('recipe', 'streams', 'route_table')})
        C.preparation(cfg)
        for field in ('code_sha256', 'mixture_sha256'):
            changed = deepcopy(cfg); changed['r2'][field] = 'f'*64
            with self.assertRaises(ValueError):
                C.preparation(changed)
        self.assertIsNone(C.preparation({}))
        with self.assertRaisesRegex(ValueError, 'membership requires'):
            C.preparation({'r2_membership': cfg['r2_membership']})
        from student_pilot import carrier_c1_run as run
        for entry in (C.preparation, run.prepare, run.prepared):
            with self.assertRaisesRegex(ValueError, 'init artifact'):
                entry({**cfg, 'init_artifact': {}})

    def test_intake_mutations_and_upstream_accounting(self):
        path = manifest(self.root/'good', [self.row], upstream=True)
        accepted, report = intake(path)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(report['upstream'][0]['receipt']['counts']['example']['refused'], 1)
        self.assertIn('admitted=1', text_report(report))
        self.assertEqual(intake_main(['--manifest', str(path), '--output', str(self.root/'cli.json')]), 0)
        mutations = [dict(target='A'), dict(scene='wrong'),
                     dict(target=self.row['target'].replace('right of', '73 meters right of')),
                     dict(question_type='camera_displacement'), dict(tool_output_spans=[{}])]
        for i, change in enumerate(mutations):
            row = {**self.row, **change}
            path = manifest(self.root/f'bad{i}', [row])
            if 'scene' in change:
                value = load(path); value['row_bindings'][row['qid']] = digest(self.row); path.write_text(json.dumps(value))
            admitted, refused = intake(path)
            self.assertFalse(admitted)
            self.assertEqual(sum(c['refused'] for c in refused['counts'].values()), 1)
        wrong_unit = deepcopy(self.row)
        wrong_unit['answer_unit'] = 'ft'
        with self.assertRaisesRegex(ValueError, 'Wrong-unit'):
            C.validate(wrong_unit, 'vqa')
        room = {**self.row, 'question_type': 'room_size_estimation', 'provenance': {}}
        admitted, refused = intake(manifest(self.root/'room', [room]))
        self.assertFalse(admitted)
        self.assertIn('lineage_less_room', refused['refusals'][0]['reason'])

    def test_content_clocks_aliases_and_dense_rule(self):
        from student_pilot.dense_eval import nested_indices, attach_dense
        keys = []
        for fps in (30, 10):
            row = fixture(self.root, qid=str(fps), stream='pose' if fps == 30 else 'vqa', fps=fps)
            if fps == 30:
                row['canonical'] = 'd1/fixture_clean'
            built, key = build_training(row)
            keys.append(key)
            dense = built['student_input']['geometry_dense']
            self.assertEqual(dense['frame_indices'], nested_indices(64, list(range(0, 64, 2))))
            self.assertEqual(dense['timestamps'], [i/fps for i in range(64)])
            attach_dense(built, dense, {'dense_frames': 64})
        self.assertEqual(keys[0], keys[1])
        # A second store path holds identical bytes; dense identity ignores path.
        row = deepcopy(self.row)
        row['student_input']['frames'] = [{**p, 'path': p['path'].replace('/logical/r2', '/other/store')} for p in row['student_input']['frames']]
        self.assertEqual(build_training(row)[1], keys[0])

    def test_frame_memo_and_stale_pin(self):
        memo = F.FrameMemo(capacity=2)
        pin = self.row['student_input']['frames'][0]
        self.assertEqual(memo.verify(pin), self.root/'frames/0.png')
        memo.verify(pin)
        self.assertEqual(memo.hashes, 1)
        for p in self.row['student_input']['frames'][1:3]:
            memo.verify(p)
        self.assertEqual(len(memo.values), 2)
        memo.verify(pin)
        self.assertEqual(memo.hashes, 4)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            memo.verify({**pin, 'sha256': '0'*64})
        Image.new('RGB', (32, 32), (99, 98, 97)).save(self.root/'frames/0.png')
        with self.assertRaisesRegex(ValueError, 'Stale'):
            memo.verify(pin)

    def test_marker_full_store_and_route_collision(self):
        path = manifest(self.root/'vqa', [self.row])
        with self.assertRaisesRegex(ValueError, 'Full store forbidden'):
            materialize([path], self.root/'full', full=True)
        report = materialize([path], self.root/'marker', metadata_only=True)
        self.assertEqual(report['status'], 'needs the frame host')
        self.assertFalse((self.root/'marker/receipt.json').exists())
        with patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP='{}'):
            report = materialize([path], self.root/'absent')
            self.assertEqual(report['status'], 'needs the frame host')
        route = {**self.row, 'question_type': 'route_planning'}
        first = manifest(self.root/'sealed', [route], family='sealed')
        second = manifest(self.root/'rendered', [route], family='rendered')
        collision=materialize([first, second], self.root/'collision')
        self.assertIn('Duplicate QID across families: sealed / rendered',collision['intake'][1]['refusals'][0]['reason'])
        self.assertEqual(collision['intake'][1]['counts']['route_planning']['refused'],1)
        report = materialize([first, second], self.root/'filtered', select_types={str(first): list(G.PROGRAM_TYPES)})
        self.assertEqual(report['status'], 'ready')

    def test_real_producers_and_reader_each_family(self):
        from student_pilot.carrier_c1_run import Rows
        paths = []
        for stream in ('vqa', 'routing', 'pose', 'pointing'):
            row = fixture(self.root, qid=stream, stream=stream, fps=30 if stream == 'pose' else 10)
            paths.append(manifest(self.root/stream, [row], stream=stream))
        report = materialize(paths, self.root/'native')
        self.assertEqual(report['status'], 'ready')
        receipt = load(report['receipt']['path'])
        reader = Rows(receipt, TinyProcessor())
        from tests.test_carrier_c1 import fixture as model_fixture
        model, _, _ = model_fixture(training_mode='final')
        model.model.language_model.embed_tokens = torch.nn.Embedding(512, 32)
        model.lm_head = torch.nn.Linear(32, 512, bias=False)
        model.config.text_config.vocab_size = 512
        model.frame_layout = 'duplicate'
        model.auxiliary_heads.depth.config.p3['frame_layout'] = 'duplicate'
        model.recipe = {**model.recipe, 'weights': {**model.recipe['weights'], 'routing': 1.0}}
        model.eval()
        proofs = []
        reader_before = F.MEMO.stats()
        try:
            for stream in ('vqa', 'routing', 'pose', 'pointing'):
                batch, targets, audit = reader.get(stream, 0)
                with torch.no_grad():
                    forward = model(batch, targets, stream=stream)
                self.assertTrue(torch.isfinite(forward['loss']))
                self.assertTrue(torch.isfinite(batch['pixel_values_videos']).all())
                if stream == 'routing':
                    self.assertEqual(audit['tool_spans'], 1)
                    row, _ = reader.row(stream, 0)
                    target, spans, _ = routing.render_full(row['routing']['events'], row['routing']['answer'])
                    ids, keep, _ = routing.suffix_tokens(reader.processor, row, target, spans)
                    start = int(batch['aux_suffix_start'][0])
                    self.assertTrue((batch['labels'][0, start:start+len(ids)][~torch.tensor(keep)] == -100).all())
                proofs.append(dict(family=stream, encoded=True, finite_loss=float(forward['loss']), sequence_tokens=int(batch['input_ids'].shape[1])))
        finally:
            reader.close()
        (PROOFS/'CPU_PATH_PROOF.json').write_text(json.dumps(dict(families=proofs, frame_bytes='synthetic RGB fixture, no real frames',
              stand_ins=['TinyProcessor', 'TinyTokenizer', 'random tiny native Qwen and CarrierC1 in place of pretrained weights'],
              materialize_hashes_before=report['hashes_before'], materialize_hashes_after=report['hashes_after'],
              reader_hashes_before=reader_before, reader_hashes_after=F.MEMO.stats()), indent=2))

    def test_program_refuses_direct_type_and_bad_spans(self):
        row = fixture(self.root, stream='routing')
        G.validate_program(row)
        for change in (dict(question_type='room_size_estimation'), dict(tool_output_spans=[]),
                       dict(target=row['target']+'bad'), dict(events=[])):
            with self.assertRaises(ValueError):
                G.validate_program({**row, **change})
        with self.assertRaisesRegex(ValueError, 'masked routing'):
            C.validate(row, 'vqa')

from tests.r2_init_fixture import INIT
