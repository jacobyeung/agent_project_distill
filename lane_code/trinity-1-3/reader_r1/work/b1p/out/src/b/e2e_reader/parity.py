"""Native restore, frame binding, and official scoring for paired reader runs.

load_native and bind_item are public so another lane can supply perception_factory.
No answers are synthesized from tool responses.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import time

from parity_kit.common import (DENSE, FRAMES, TREE, checked, install, key, pin, policy, read, sha)
from .artifact import Artifact
from .callhook import CallHook, install as install_hook
from .core import E2EGenerator


def _captures(value):
    data = read(value) if isinstance(value, (str, Path)) else value
    captures = data['captures']
    return {c['native']: c for c in captures} if isinstance(captures, list) else captures


def _frame_path(path, root):
    path = Path(path)
    if path.is_absolute():
        path = path.relative_to('/scratch/jjyeung/devs1_frames')
    result = (Path(root) / path).resolve()
    if Path(root).resolve() not in result.parents:
        raise ValueError('frame path escapes frames_root')
    return result


def trainer_row(task, capture, frames_root, verify=True):
    """routed.trainer_row without importing its launcher or changing its path registry."""
    frames = [dict(path=str(_frame_path(f['path'], frames_root)), sha256=f['sha256'])
              for f in capture['frames']]
    if verify:
        for f in frames:
            checked(f['path'], f['sha256'])
    si = dict(frames=frames, frame_indices=capture['anchor_indices'], timestamps=capture['timestamps'],
              fps=capture['fps'], total_num_frames=capture['total_num_frames'],
              question=task['question'], options=task['options'])
    identity = {k: si[k] for k in ('frame_indices', 'fps', 'total_num_frames')}
    identity['frames'] = [f['sha256'] for f in frames]
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'),
                                       allow_nan=False).encode()).hexdigest()
    si['video_identity'] = dict(video_sha256=digest, kind='devS1-pinned-PNG-clip-v1')
    return dict(qid=task['id'], dataset=task['dataset'], scene=task['scene'],
                question_type=task['question_type'], student_input=si)


def bind_item(item, settings, *, verify=True):
    """With verify=False return paths only; this mode never opens an image."""
    captures = _captures(settings.get('frames_json', FRAMES))
    dense = _captures(settings.get('dense_manifest', DENSE))
    c, d = captures[item['native']], dense[item['native']]
    anchors, slots = c['anchor_indices'], d['anchor_slots']
    count = len(d['frames'])
    if count not in (32, 64) or len(anchors) != 32 or len(slots) != len(anchors):
        raise ValueError('expected 32 anchors and 32 or 64 pinned dense frames')
    if settings.get('require_dense64', False) and count != 64:
        raise ValueError('capture has 32 pinned dense frames; require_dense64 is set')
    if any(type(s) is not int or not 0 <= s < count for s in slots):
        raise ValueError('invalid dense anchor slot')
    if ([d['frames'][s]['index'] for s in slots] != anchors
            or [d['frames'][s]['sha256'] for s in slots] != [f['sha256'] for f in c['frames']]
            or [f['index'] for f in c['frames']] != anchors):
        raise ValueError('dense anchors differ from FRAMES.json')
    if item.get('source_frame_indices', anchors) != anchors:
        raise ValueError('task anchors differ from FRAMES.json')
    paths = [_frame_path(f['path'], settings['frames_root']) for f in d['frames']]
    images = []
    if verify:
        from PIL import Image
        for f, p in zip(d['frames'], paths):
            checked(p, f['sha256'])
            with Image.open(p) as im:
                images.append(im.convert('RGB'))
    row = trainer_row(item, c, settings['frames_root'], verify=verify)
    frames = dict(native_frames=images if verify else [str(p) for p in paths],
                  dense_indices=[f['index'] for f in d['frames']], anchor_slots=slots,
                  anchor_indices=anchors)
    return dict(id=key(item), row=row, frames=frames)


def decoded(output):
    """Adapt the reader report to the sealed scorer's text/finish interface."""
    if 'decode' in output:
        output = output['decode'] or dict(text='', finish='item_error')
    calls = output.get('calls', [])
    if isinstance(calls, dict):
        calls = calls['records']
    return {**output, 'text': output.get('text', ''), 'finish': output.get('finish', 'item_error'),
            'calls': calls, 'generated_tokens': output.get('generated_tokens', len(output.get('tokens', [])))}


def score(task, output):
    """The two labels in nomdg.make_record, including native_score's think-close rule."""
    install()
    from evalpath.run import score_item
    dec = decoded(output)
    labels = dict(answer=task['answer'],
                  released_answer=task.get('released_answer_in_options', task.get('released_answer')))
    no_answer = (dec.get('strict_no_answer') or not re.search(r'</think\s*>', dec['text'], re.I)
                 or score_item({**task, 'ground_truth': task['answer']}, dec)['parse_failed'])
    return {k: None if label is None else 0.0 if no_answer else
            score_item({**task, 'ground_truth': label}, dec)['score'] for k, label in labels.items()}


def load_native(export_dir, *, device='cpu', settings, artifact=None):
    """Load the processor and model once, following read_runtime's evaluation ordering."""
    install(settings.get('tree', TREE))
    from student_pilot import carrier_c1_run as trainer
    out = Path(export_dir).resolve()
    restore = read(out / 'RESTORE.json')
    for name, spec in restore['local'].items():
        checked(out / name, spec['sha256'])
    cfg = read(checked(settings['config'], restore['original']['config']['sha256']))
    receipt = read(out / 'receipt.json')
    checked(receipt['model']['path'], receipt['model']['sha256'])
    manifest = read(receipt['model']['path'])
    if artifact is not None:
        export = read(out / 'artifact.json')
        required = [out / 'artifact.json', Path(export['heads']['path']), Path(export['full_weights']['path'])]
        required += [Path(manifest['root']) / n for n in manifest['files']]
        for p in required:
            if str(p.resolve()) not in artifact.allowed:
                raise ValueError('restore input missing from artifact: ' + str(p))
    receipt.update(align=cfg.get('align'), init_artifact=cfg.get('init_artifact'),
                   frame_markers=cfg.get('frame_markers', False), pointing_weights=cfg.get('pointing_weights'),
                   camera={**receipt['camera'], **cfg.get('camera_overrides', {})})
    processor = trainer.processor_for_receipt(manifest, receipt)
    loading = {k: v for k, v in receipt.items() if k != 'init_artifact'}
    model = trainer.load_model(manifest, loading, processor, evaluation=True)
    if cfg.get('depth_init') and 'depth_init' not in receipt:
        # The omitted stage-1 depth init (stage_restore) also froze the private encoder copy; the trained-group
        # contract of the export counts only the tensors that stayed trainable, so freeze it the same way.
        model.auxiliary_heads.depth.model.visual.requires_grad_(False)
        model.depth_stage1 = True
    artifact = trainer.load_artifact(model, pin(out / 'artifact.json'))
    if (artifact['base_identity'] != cfg['base_identity']
            or artifact['config_sha256'] != trainer.identity(cfg)
            or getattr(model, 'trace_program_version', None) != '3.14'):
        raise ValueError('loaded export identity differs')
    model.to(device).eval().requires_grad_(False)
    return model, processor, dict(config=cfg, receipt=receipt, export=artifact, restore=restore)


class ParityGenerator(E2EGenerator):
    """E2EGenerator with its real decoder's explicit cap exposed.

    The parent validates frame layout and owns the model/hook/perception. Its public
    __call__ does not forward max_new_tokens, so this dispatch supplies the native cap.
    """
    def __call__(self, item):
        from .real import generate_real
        start = time.perf_counter()
        batch = self.prompt_batch(self.processor, item['row'])
        batch = {k: v.to(self.device) if hasattr(v, 'to') else v for k, v in batch.items()}
        budget = self.budget_factory()
        result = generate_real(self.model, self.processor, batch, item['frames'], self.hook,
                               self.perception, artifact=self.artifact, budget=budget,
                               max_new_tokens=16384)
        result.update(id=item['id'], seconds=time.perf_counter() - start, frames=self.frames,
                      decode_budget=budget.receipt(len(result['tokens'])))
        return result


def _head(artifact, directory, component):
    from parity_kit.common import LANE, module
    directory = Path(directory).resolve()
    for suffix in ('.json', '.safetensors'):
        if (directory / (component + suffix)).resolve() not in artifact.files(component):
            raise ValueError('head file missing from artifact: ' + component)
    loader = module(LANE / 'heads' / component.removesuffix('_head') / (component + '.py'),
                    '_parity_' + component)
    loaded = loader.load_head(directory)
    return loaded[0] if isinstance(loaded, tuple) else loaded


def make_real(export_dir, artifact_manifest, items, *, perception_factory=None, device='cpu', settings):
    install(settings.get('tree', TREE))
    arm = settings['arm']
    if arm not in ('own_depth', 'scale_head'):
        raise ValueError('unknown arm')
    specs = dict(artifact_manifest)
    artifact = Artifact(specs['root'], specs['name'], specs['sha256'],
                        code_roots=specs.get('code_roots'), env_roots=settings.get('env_roots', ()),
                        write_roots=[os.environ[k] for k in ('TRITON_CACHE_DIR', 'TORCHINDUCTOR_CACHE_DIR', 'XDG_CACHE_HOME',
                                                             'HF_HOME', 'TORCH_HOME') if os.environ.get(k)],
                        required_roles=('checkpoint', 'tokenizer', 'g3t') +
                        (('scale_head',) if arm == 'scale_head' else ())).verify()
    model, processor, info = load_native(export_dir, device=device, settings=settings, artifact=artifact)
    hook = install_hook(model, CallHook(processor.tokenizer, processor._routing_tokens['ids'].values()))
    from evalpath import runtime
    from .real import real_perception
    selection = {key(t): t for t in items}
    if len(selection) != len(items):
        raise ValueError('duplicate selected keys')
    bound_settings = dict(settings, frames_json={'captures': _captures(settings.get('frames_json', FRAMES))},
                          dense_manifest={'captures': _captures(settings.get('dense_manifest', DENSE))})
    cfg = deepcopy(info['config'])
    if cfg.get('tool_mode_flag'):
        raise ValueError('parity requires the unflagged prompt')
    layout = dict(layout=info['export']['frame_layout'], count=32)
    default_perception = None
    if perception_factory is None:
        if settings.get('sam3') and not settings.get('selector_head'):
            raise ValueError('SAM3 ground/gap requires a selector head')
        scale = _head(artifact, settings['scale_head'], 'scale_head') if arm == 'scale_head' else None
        selector = _head(artifact, settings['selector_head'], 'selector_head') if settings.get('selector_head') else None
        sam = None
        if settings.get('sam3'):
            from student_pilot.sam3_tower import Sam3Tower
            sam_settings = dict(settings['sam3'], device=device)
            for name in ('checkpoint_path', 'receipt_path'):
                if Path(sam_settings[name]).resolve() not in artifact.files('sam3'):
                    raise ValueError('SAM file missing from artifact: ' + name)
            sam = Sam3Tower(sam_settings)
        default_perception = real_perception(artifact, device=device, scale_head=scale,
                                             stage1_select_rule=settings.get('stage1_select_rule','null_argmax'),
                                             sam3_tower=sam, selector_head=selector)
    budget_policy = policy()
    generator = ParityGenerator(model, processor, artifact, default_perception, hook,
                               dict(frames=layout), export_layout=layout,
                               prompt_batch=lambda p, r: runtime.prompt_batch(p, r, cfg, 'routed'),
                               budget_factory=lambda: budget_policy.ThinkingBudget(
                                   processor.tokenizer, budget_policy.DECODE_BUDGET,
                                   openers=processor._routing_tokens['ids'].values()), device=device)

    def gen(item):
        if key(item) not in selection or selection[key(item)] != item:
            raise ValueError('item is not in the selected task set')
        bound = bind_item(item, bound_settings)
        if perception_factory is not None:
            generator.perception = perception_factory(artifact=artifact, model=model, processor=processor,
                                                        device=device, item=item)
        result = generator(bound)
        return dict(result, key=key(item), room=item['room'], question_type=item['question_type'],
                    stratum=item.get('stratum'), arm=arm, scores=score(item, result))
    gen.generator, gen.load_info = generator, info
    return gen
