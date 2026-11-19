"""Exercise the real SAM processor and exact ttower postprocessor on CPU."""
from contextlib import nullcontext
from pathlib import Path
import sys
import unittest
import torch
from PIL import Image

from student_pilot.sam3_tower import Sam3Tower, normalize_phrase
from scripts.sam3_validate import prediction
from scripts.sam3_reference import reference_processor, reference_records

SOURCE = Path('/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src')
WRITER = Path('/scratch/jjyeung/orch_cd/ttower/work/sam3')


class TinyModel(torch.nn.Module):
    """Exact fp32 arithmetic exposes preprocessing, frame, name and state errors."""
    def __init__(self):
        super().__init__()
        from types import SimpleNamespace
        self.weight = torch.nn.Parameter(torch.ones(1))
        self.backbone = SimpleNamespace(forward_image=self.image, forward_text=self.text)
        self.inst_interactive_predictor = None
        self.image_inputs = []

    def image(self, image):
        assert image.dtype == torch.float32
        self.image_inputs.append(image.clone())
        feature = image[:, :1, ::4, ::4]
        return dict(backbone_fpn=[feature], vision_pos_enc=[feature*0], vision_features=feature)

    def text(self, phrases, device):
        return dict(language_features=torch.tensor([sum(map(ord, phrases[0])) % 17], dtype=torch.float32))

    def _get_dummy_prompt(self):
        return None

    def forward_grounding(self, *, backbone_out, **kwargs):
        x = backbone_out['backbone_fpn'][0]; t = backbone_out['language_features'][0]
        shift = x[0, 0, 0, 0]*.25 + t/32
        return dict(pred_logits=(torch.arange(8, dtype=torch.float32)/4 - 1 + shift)[None, :, None],
            presence_logit_dec=shift[None], pred_boxes=torch.tensor([.5, .5, .25, .5]).expand(1, 8, 4),
            pred_masks=(x+torch.arange(8, dtype=torch.float32)[None, :, None, None]/8-.5))


class ReferenceParity(unittest.TestCase):
    def test_launcher_stops_after_stage3_failure_and_continues_after_pass(self):
        import os, subprocess
        root = Path(__file__).resolve().parents[3]
        launcher = (root/'scripts/run_gpu_acceptance.sh').read_text()
        stages = launcher.split('run_stages() {', 1)[1].split('\n}\n', 1)[0]
        # Exercise the launcher's actual six-command function with a CPU stand-in.
        shell = '''set -aeuo pipefail
root=unused
ACCEPTANCE_LANE_ROOT=unused VERIFY_KIT=x PARITY_CROPS=x
GPU_PYTHON=stage
live=(live)
LIVE_INPUTS=x CALL_MODE=scripted GPU_OUTPUT=x SAM_MANIFEST=x SAM3_CHECKPOINT=x
SAM3_SOURCE_ROOT=x T0_WEIGHTS=x T0_BASE=x STUDENT_CONFIG=x STUDENT_ARTIFACT=x
STUDENT_BUNDLE=x ROUTED_ROWS=x ROUTED_GEOMETRY=x
count=0
sha256sum() { echo "fixture-sha $1"; }
stage() {
  count=$((count+1))
  echo "stage=$count"
  if [ "$count" = 3 ]; then return "$STAGE3_STATUS"; fi
}
run_stages() {
''' + stages + '\n}\nexport -f stage sha256sum run_stages\ntimeout 10 bash -euc run_stages\n'
        for status, expected in ((0, 6), (1, 3)):
            result = subprocess.run(['bash', '-c', shell], env=dict(os.environ, STAGE3_STATUS=str(status)),
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, status, result.stderr)
            self.assertEqual(result.stdout.splitlines(), ['stage='+str(i) for i in range(1, expected+1)])

    def test_floor_rejects_corruption_and_coverage_changes(self):
        from dataclasses import replace
        from tests.test_acceptance_parity_rules import fixture
        from scripts.sam3_reference import paired_check, measured_floor_proposal
        old = fixture()
        def row(new):
            return dict(scene='a', frame=0, phrase='chair', **paired_check(prediction(old), new))
        exact = [row(old)]
        self.assertTrue(measured_floor_proposal(exact, exact)['within_measured_floor'])
        for new in (replace(old, masks=old.masks.roll(5, 1)), replace(old, presence=.7),
                    replace(old, all_scores=old.all_scores-.1),
                    replace(old, query_ids=torch.tensor([0, 1, 2, 3, 5]))):
            result = measured_floor_proposal(exact, [row(new)])
            self.assertFalse(result['within_measured_floor'])
            self.assertTrue(result['advisory_only'])
        for changed in ([], [dict(exact[0], frame=1)], exact*2):
            with self.assertRaises(ValueError):
                measured_floor_proposal(exact, changed)

    def test_stage_passes_fresh_r7_despite_archive_failure(self):
        self.stage_gate(fresh_passes=True)

    def test_stage_fails_fresh_r7_and_saves_diagnostics(self):
        self.stage_gate(fresh_passes=False)

    def stage_gate(self, *, fresh_passes):
        from contextlib import ExitStack, redirect_stdout
        from dataclasses import replace
        from types import SimpleNamespace
        from unittest.mock import patch
        import io, json, os, tempfile
        import scripts.sam3_validate as validation
        import scripts.sam3_reference as reference
        from tests.test_acceptance_parity_rules import fixture
        root = Path(tempfile.mkdtemp(prefix='sam_r10_', dir=os.environ['TMPDIR']))
        im = root/'frame.png'; Image.new('RGB', (100, 40)).save(im)
        receipt = root/'receipt.json'; receipt.write_text('{}')
        reference_b1 = fixture()
        fresh = replace(reference_b1, presence=reference_b1.presence-.005 if fresh_passes else .5)
        # The archive gives the opposite verdict to the fresh reference.
        old = replace(reference_b1, presence=.5) if fresh_passes else fresh
        scenes = []
        for i in range(10):
            cache = root/(str(i)+'.json')
            cache.write_text(json.dumps(dict(scene=str(i), phrases=['chair'],
                frames={str(k):dict(phrases={'chair':prediction(old)}) for k in range(32)})))
            scenes.append(dict(scene=str(i), phrases=['chair'], frames=[str(im)]*32,
                               reference=str(cache), reference_sha256=validation.sha256(cache)))
        manifest = root/'manifest.json'
        manifest.write_text(json.dumps(dict(scenes=scenes, receipt_sha256=validation.sha256(receipt), contract={})))
        class Tower:
            device = torch.device('cpu')
            _backend = SimpleNamespace(model=None)
            _autocast = staticmethod(nullcontext)
            def _load(self): pass
            def encode(self, frames):
                return SimpleNamespace(frames=({'features':[torch.zeros(1)]},))
            def detect(self, *a): return [fresh]*32
            def detect_cache_reference(self, *a): return [fresh]*32
        args = SimpleNamespace(start_check=False, enable_sam3_tower=True, command='parity', manifest=manifest,
            receipt=receipt, checkpoint=root/'weights', source_root=root, precision='bf16',
            image_batch_size=1, native_image_batch=False, out=root/'output', max_seconds=60,
            max_write_bytes=10000000, parity_rule='noise-aware', measure_reference_floor=True,
            reference_writer_root=WRITER)
        batches = []
        def records(processor, frames, phrases, *, batch_size, autocast):
            batches.append(batch_size)
            return [dict(chair=prediction(reference_b1)) for _ in frames]
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, CUDA_VISIBLE_DEVICES='cpu-fixture'))
            stack.enter_context(patch.object(validation, 'attach_sam3_tower', return_value=Tower()))
            stack.enter_context(patch.object(validation, 'load_cache', side_effect=lambda p:json.loads(Path(p).read_text())))
            stack.enter_context(patch.object(reference, 'reference_processor',
                return_value=SimpleNamespace(reference_sources={'stub.py':'a'*64})))
            stack.enter_context(patch.object(reference, 'reference_records', side_effect=records))
            stack.enter_context(patch.object(validation, 'runtime_attestation', return_value=dict(
                run_id='cpu-test-run', hardware={'name':'CPU mock'}, libraries={'torch':torch.__version__})))
            for name, value in [('device_count',1), ('synchronize',None), ('reset_peak_memory_stats',None),
                                ('max_memory_allocated',0), ('max_memory_reserved',0), ('get_device_name','CPU mock')]:
                stack.enter_context(patch.object(torch.cuda, name, return_value=value))
            printed = io.StringIO()
            with redirect_stdout(printed), (nullcontext() if fresh_passes else self.assertRaises(SystemExit)):
                validation.run(args)
        self.assertEqual(batches, [1,4]*10)
        result = json.loads((args.out/'REPORT.json').read_text())
        floor = json.loads((args.out/'REFERENCE_FLOOR.json').read_text())
        self.assertEqual(result['ok'], fresh_passes)
        self.assertEqual(result['aggregate']['policy'], 'sam3-noise-aware-r7')
        self.assertEqual(floor['floor']['strict']['failed'], 0)
        self.assertEqual(floor['candidate']['strict']['failed'], 320)
        self.assertEqual(floor['within_measured_floor'], fresh_passes)
        self.assertEqual(floor['archived_reference_vs_tower']['ok'], not fresh_passes)
        self.assertFalse(floor['archived_reference_vs_reference_b1']['ok'])
        self.assertIn('archive_fresh_strict', printed.getvalue())
        self.assertIn('archive_tower_strict', printed.getvalue())
        self.assertEqual(len(list(args.out.glob('*_same_card.json'))), 10)
        scenes = [json.loads((args.out/(str(i)+'.json')).read_text()) for i in range(10)]
        diagnostics = [json.loads((args.out/(str(i)+'_same_card.json')).read_text()) for i in range(10)]
        aggregate = validation.verify_fresh_gate(result, scenes, diagnostics)
        self.assertEqual(aggregate['ok'], fresh_passes)
        self.assertEqual(result['reference_provenance']['frame_sha256']['0'], [validation.sha256(im)]*32)
        self.assertEqual(set(result['reference_seconds']), {'b1','b4','total'})
        # The final acceptance checker cannot quietly consume archived checks.
        from copy import deepcopy
        wrong = deepcopy(scenes)
        wrong[0]['checks'] = wrong[0]['archived_reference_vs_tower_checks']
        with self.assertRaises(AssertionError):
            validation.verify_fresh_gate(result, wrong, diagnostics)
        wrong = deepcopy(diagnostics)
        wrong[0]['runtime_run_id'] = 'another-run'
        with self.assertRaises(AssertionError):
            validation.verify_fresh_gate(result, scenes, wrong)

    def test_exact_fp32_reference_and_tower_real_processor(self):
        sys.path.insert(0, str(SOURCE))
        model = TinyModel().eval()
        processor = reference_processor(model, SOURCE, WRITER, device='cpu', resolution=32)
        frames = [Image.new('RGB', (17+i, 13+i), (i*37, 255-i*21, i*13)) for i in range(7)]
        phrases = ['chair', 'kitchen cabinet', 'lamp']
        reference = reference_records(processor, frames, phrases, batch_size=1, autocast=nullcontext)
        images_single = model.image_inputs[:]
        model.image_inputs.clear()
        batched = reference_records(processor, frames, phrases, batch_size=4, autocast=nullcontext)
        self.assertEqual(reference, batched)
        torch.testing.assert_close(torch.cat(images_single), torch.cat(model.image_inputs), rtol=0, atol=0)
        for native in (False, True):
            tower = Sam3Tower(dict(device='cpu', precision='float32', image_batch_size=4,
                                  native_image_batch=native), backend=processor)
            features = tower.encode(frames)
            for phrase in phrases:
                for i, actual in enumerate(tower.detect_cache_reference(features, phrase)):
                    expected = reference[i][phrase]
                    value = prediction(actual)
                    self.assertEqual(expected['presence'], value['presence'])
                    self.assertEqual(expected['all_instance_scores'], value['all_instance_scores'])
                    for a, b in zip(expected['instances'], value['instances']):
                        self.assertEqual(a, {k:b[k] for k in a})
                    self.assertEqual(len(expected['instances']), len(value['instances']))
        # The prompt map is part of the independent reference contract.
        import importlib.util
        spec = importlib.util.spec_from_file_location('reference_phrase_r10', WRITER/'common.py')
        common = importlib.util.module_from_spec(spec); spec.loader.exec_module(common)
        for name in list(common.SINGULAR)+[' Kitchen_Cabinets ', 'vending machine']:
            self.assertEqual(normalize_phrase(name), common.phrase(name))


if __name__ == '__main__':
    unittest.main()
