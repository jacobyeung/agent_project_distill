"""Offline SAM 3 image grounding. Only the run subcommand touches CUDA."""
import argparse
import os
import time
from common import *


def make_processor(checkpoint):
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['XDG_CACHE_HOME'] = str(HERE/'cache')
    os.environ['HF_HOME'] = str(HERE/'cache/hf')
    os.environ['TRITON_CACHE_DIR'] = str(HERE/'cache/triton')
    os.environ['TORCH_HOME'] = str(HERE/'cache/torch')
    import torch
    from sam3.model_builder import build_sam3_image_model
    from sam3.model.sam3_image_processor import Sam3Processor
    from sam3.model.box_ops import box_cxcywh_to_xyxy
    from sam3.model.data_misc import interpolate

    class RawProcessor(Sam3Processor):
        @torch.inference_mode()
        def _forward_grounding(self, state):
            outputs = self.model.forward_grounding(
                backbone_out=state['backbone_out'], find_input=self.find_stage,
                geometric_prompt=state['geometric_prompt'], find_target=None)
            scores = outputs['pred_logits'].sigmoid().reshape(-1).float()
            presence = float(outputs['presence_logit_dec'].sigmoid().item())
            boxes = box_cxcywh_to_xyxy(outputs['pred_boxes'].reshape(-1, 4)).float()
            h, w = state['original_height'], state['original_width']
            boxes *= torch.tensor([w, h, w, h], device=boxes.device)
            order = torch.argsort(scores, descending=True, stable=True)
            keep = order[scores[order] >= CONTRACT['instance_floor']][:CONTRACT['max_instances']]
            native_masks = outputs['pred_masks'].reshape(-1, *outputs['pred_masks'].shape[-2:])
            instances = []
            # Upsample one mask at a time to bound native-resolution memory.
            for idx in keep.tolist():
                mask = interpolate(native_masks[idx][None,None].float(), (h,w),
                                   mode='bilinear', align_corners=False).sigmoid()[0,0] > .5
                mask = mask.cpu().numpy()
                instances.append(dict(query=idx, score=float(scores[idx]),
                                      box=boxes[idx].cpu().tolist(), mask=rle_encode(mask)))
            click = deepest(rle_decode(instances[0]['mask'])) if instances else None
            return dict(presence=presence, all_instance_scores=scores.cpu().tolist(),
                        all_boxes=boxes.cpu().tolist(), instances=instances, click=click,
                        joint_score=presence * instances[0]['score'] if instances else -1.)

    if not Path(checkpoint).is_file():
        raise FileNotFoundError(checkpoint)
    model = build_sam3_image_model(checkpoint_path=str(checkpoint), load_from_HF=False,
                                  device='cuda', eval_mode=True, enable_inst_interactivity=False)
    return RawProcessor(model, device='cuda', resolution=CONTRACT['resolution'])


def run(a):
    # Only the designated tuning manifest can be opened before tau is frozen.
    if Path(a.scenes).resolve() != (HERE/'scenes_tune.json').resolve():
        require_frozen()
    manifest = read_json(a.scenes)
    if manifest['contract_sha256'] != fixed_sha():
        raise ValueError('Manifest tower contract differs')
    if manifest['phase'] != 'tune':
        require_frozen()
    elif any(row['scene'] not in tuning_scenes() for row in manifest['scenes']):
        raise ValueError('Tuning manifest includes a held-out scene')
    if not 0 <= a.rank < a.world:
        raise ValueError('Require 0 <= rank < world')
    import torch
    from PIL import Image
    if not os.environ.get('CUDA_VISIBLE_DEVICES') or torch.cuda.device_count() != 1:
        raise RuntimeError('Parent must set CUDA_VISIBLE_DEVICES to exactly one GPU')
    processor = None
    checkpoint_stat = Path(a.checkpoint).stat()
    provenance = dict(path=str(Path(a.checkpoint).resolve()), size=checkpoint_stat.st_size,
                      mtime_ns=checkpoint_stat.st_mtime_ns)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for row in manifest['scenes'][a.rank::a.world]:
        scene, phrases = row['scene'], row['phrases']
        final = cache_path(out, scene)
        if final.exists():
            old = load_cache(out, scene)
            if old['phrases'] != phrases or len(old['frames']) != 32 or old['checkpoint'] != provenance:
                raise RuntimeError(f'Incompatible existing cache; move aside explicitly: {final}')
            print(f'resume: {scene} complete', flush=True)
            continue
        # Fail before loading weights when frames are unavailable.
        paths = [Path(a.frames)/scene.replace('/', '__')/f'{slot}.jpg' for slot in range(32)]
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            raise FileNotFoundError(f'Missing frames: {missing[:3]}')
        if processor is None:
            processor = make_processor(a.checkpoint)
        torch.cuda.reset_peak_memory_stats()
        value = dict(scene=scene, phrases=phrases, contract_sha256=fixed_sha(),
                     checkpoint=provenance, frames={}, phase=manifest['phase'])
        start = time.monotonic()
        for slot, path in enumerate(paths):
            frame_start = time.monotonic()
            with Image.open(path) as source:
                image = source.convert('RGB')
            with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                state = processor.set_image(image)
                predictions = {}
                for text in phrases:
                    processor.reset_all_prompts(state)
                    predictions[text] = processor.set_text_prompt(prompt=text, state=state)
            del state
            torch.cuda.synchronize()
            elapsed = time.monotonic() - frame_start
            value['frames'][str(slot)] = dict(size=list(image.size), phrases=predictions, seconds=elapsed)
            print(canonical(dict(scene=scene, slot=slot, phrases=len(phrases), seconds_per_frame=elapsed,
                                 peak_memory_gb=torch.cuda.max_memory_allocated()/1e9)), flush=True)
        value['seconds'] = time.monotonic() - start
        value['peak_memory_gb'] = torch.cuda.max_memory_allocated()/1e9
        save_cache(final, value)
        print(canonical(dict(scene=scene, complete=True, seconds_per_frame=value['seconds']/32,
                             peak_memory_gb=value['peak_memory_gb'])), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--scenes', type=Path, required=True, help='prepare.py scene/phrase JSON manifest')
    r.add_argument('--rank', type=int, required=True)
    r.add_argument('--world', type=int, required=True)
    r.add_argument('--out', type=Path, default=HERE/'raw/tune')
    r.add_argument('--frames', type=Path, default=WORK/'frames32')
    r.add_argument('--checkpoint', type=Path, default=CHECKPOINT)
    run(p.parse_args())


if __name__ == '__main__':
    main()
