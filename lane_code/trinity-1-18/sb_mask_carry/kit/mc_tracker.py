"""SAM 3 tracker from the pinned video checkpoint: one seed mask on its frame, carried forward and backward.

Runs in the SAM 3 interpreter. The model is the one SAM 3's video predictor wraps (build_sam3_video_model);
the predictor class itself calls .cuda() unconditionally, so the CPU dry run builds the same model directly.
"""
import contextlib
import importlib.util
import io
import json
import sys
import time
from pathlib import Path
import numpy as np
import torch
from torch.overrides import TorchFunctionMode
import mc_common as C

SOURCE_GLOBS = ('sam3/*.py', 'sam3/model/*.py', 'sam3/model/utils/*.py', 'sam3/sam/*.py', 'sam3/perflib/*.py')


def verify_sources():
    receipt = json.loads(C.read(C.RECEIPT))
    if receipt['checkpoint_sha256'] != C.CHECKPOINT_SHA256:
        raise ValueError('receipt pins another checkpoint')
    for name, expected in receipt['source_files'].items():
        got = C.sha256_file(C.SAM3_ROOT/name)
        C.PINS[str(C.SAM3_ROOT/name)] = got
        if got != expected:
            raise ValueError('SAM 3 source differs from receipt: '+name)
    for pattern in SOURCE_GLOBS:
        for p in sorted(C.SAM3_ROOT.glob(pattern)):
            C.PINS[str(p)] = C.sha256_file(p)
    return receipt


def verify_checkpoint():
    got = C.sha256_file(C.CHECKPOINT)
    C.PINS[str(C.CHECKPOINT)] = got
    if got != C.CHECKPOINT_SHA256:
        raise ValueError(f'checkpoint sha256 {got} != pinned {C.CHECKPOINT_SHA256}')
    return got


def import_sam3():
    root = str(C.SAM3_ROOT)
    if 'sam3' in sys.modules and not str(Path(sys.modules['sam3'].__file__).resolve()).startswith(root):
        raise ValueError('another sam3 package was imported first')
    if sys.path[0] != root:
        sys.path.insert(0, root)
    import sam3
    if not str(Path(sam3.__file__).resolve()).startswith(root+'/'):
        raise ValueError('sam3 resolved outside the pinned /scratch source: '+sam3.__file__)
    return sam3


def nonlocal_modules():
    """Loaded module files outside /scratch; the GPU pass refuses any (no /home or /data* reads)."""
    bad = []
    for m in list(sys.modules.values()):
        p = getattr(m, '__file__', None)
        if p and not str(Path(p).resolve()).startswith('/scratch/'):
            bad.append(p)
    return sorted(set(bad))


class CpuRedirect(TorchFunctionMode):
    """Maps the source's literal CUDA devices (device='cuda', .cuda(), .to('cuda')) to the CPU."""

    def __torch_function__(self, func, types, args=(), kwargs=None):
        kwargs = dict(kwargs or {})
        if func is torch.Tensor.cuda or func is torch.Tensor.pin_memory:
            return args[0]
        if str(kwargs.get('device', '')).startswith('cuda'):
            kwargs['device'] = 'cpu'
        if kwargs.get('pin_memory'):
            kwargs['pin_memory'] = False
        if func is torch.Tensor.to and args[1:] and str(args[1]).startswith('cuda'):
            args = (args[0], 'cpu') + tuple(args[2:])
        return func(*args, **kwargs)


def cpu_shims():
    """CPU only, source untouched: redirect literal CUDA devices and replace the MLP's unconditional bf16 cast."""
    import sam3.model.vitdet as V
    CpuRedirect().__enter__()
    spec = importlib.util.spec_from_file_location('mc_sam3_tower', C.TOWER)
    tower = importlib.util.module_from_spec(spec)
    sys.modules['mc_sam3_tower'] = tower
    C.read(C.TOWER)
    spec.loader.exec_module(tower)
    V.addmm_act = tower._addmm_act_float32
    return ['TorchFunctionMode CpuRedirect: device cuda -> cpu, Tensor.cuda and Tensor.pin_memory -> identity, Tensor.to(cuda) -> cpu',
            'sam3.model.vitdet.addmm_act -> sam3_tower._addmm_act_float32 (fp32 MLP)']


class Sam3Carry:
    """Embeds a capture's frames once, then tracks one seed mask at a time (batch size 1, no detector)."""

    def __init__(self, device):
        self.device = torch.device(device)
        if self.device.type == 'cpu' and torch.cuda.is_available():
            raise RuntimeError('CPU run sees a CUDA device; set CUDA_VISIBLE_DEVICES to empty')
        started = time.monotonic()
        self.receipt = verify_sources()
        verify_checkpoint()
        import_sam3()
        self.shims = cpu_shims() if self.device.type == 'cpu' else []
        from sam3.model_builder import build_sam3_video_model
        from sam3.model.io_utils import load_resource_as_video_frames
        self._load_frames = load_resource_as_video_frames
        self.model = build_sam3_video_model(checkpoint_path=str(C.CHECKPOINT), load_from_HF=False,
                                            device=str(self.device), strict_state_dict_loading=True)
        self.model.eval().requires_grad_(False)
        self.tracker = self.model.tracker
        self.load_seconds = time.monotonic()-started
        self.outside = nonlocal_modules()

    def frames(self, paths, shas):
        from PIL import Image
        images = []
        for p, s in zip(paths, shas):
            data = Path(p).read_bytes()
            got = __import__('hashlib').sha256(data).hexdigest()
            if got != s:
                raise ValueError(f'frame sha256 mismatch {p}')
            images.append(Image.open(io.BytesIO(data)).convert('RGB'))
        return images

    @torch.inference_mode()
    def embed(self, images):
        """Tracker features per frame, built as Sam3VideoBase does for its tracker (sam2 neck, conv_s0/s1)."""
        m = self.model
        batch, h, w = self._load_frames(images, image_size=m.image_size, offload_video_to_cpu=True,
                                        img_mean=m.image_mean, img_std=m.image_std)
        dec = self.tracker.sam_mask_decoder
        cache, pos = {}, None
        autocast = torch.autocast('cuda', dtype=torch.bfloat16) if self.device.type == 'cuda' else contextlib.nullcontext()
        for t in range(len(batch)):
            img = batch[t].to(self.device).float().unsqueeze(0)
            with autocast:
                out = m.detector.backbone.forward_image(img)['sam2_backbone_out']
                fpn = out['backbone_fpn']
                fpn = [dec.conv_s0(fpn[0]), dec.conv_s1(fpn[1]), fpn[2]]
            if pos is None:
                pos = out['vision_pos_enc']
            elif t == 1 and not all(torch.equal(a, b) for a, b in zip(pos, out['vision_pos_enc'])):
                raise ValueError('vision_pos_enc differs across frames; cannot share it')
            cache[t] = (img, {'tracker_backbone_out': dict(vision_features=fpn[-1], vision_pos_enc=pos, backbone_fpn=fpn)})
        return cache, (h, w)

    @torch.inference_mode()
    def track(self, cache, seed_t, seed_mask):
        """Seed on frame seed_t; forward then backward over every frame. Returns {t: (mask bool HxW, object score logit)}."""
        tr = self.tracker
        n = len(cache)
        state = tr.init_state(cached_features=cache, video_height=C.CANVAS[0], video_width=C.CANVAS[1], num_frames=n,
                              offload_state_to_cpu=self.device.type == 'cpu')
        tr.add_new_mask(state, frame_idx=int(seed_t), obj_id=1, mask=torch.from_numpy(np.asarray(seed_mask, bool)))
        tr.propagate_in_video_preflight(state, run_mem_encoder=True)
        result = {}
        for reverse in (False, True):
            for t, _, _, video_res, scores in tr.propagate_in_video(state, start_frame_idx=int(seed_t), max_frame_num_to_track=n,
                                                                     reverse=reverse, tqdm_disable=True):
                result[int(t)] = ((video_res[0, 0] > 0).cpu().numpy(), float(scores.reshape(-1)[0].float().cpu()))
        if sorted(result) != list(range(n)):
            raise RuntimeError(f'tracker covered frames {sorted(result)} of {n}')
        return result
