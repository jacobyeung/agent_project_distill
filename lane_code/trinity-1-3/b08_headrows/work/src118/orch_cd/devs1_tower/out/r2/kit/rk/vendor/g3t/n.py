import importlib
from pathlib import Path
from types import SimpleNamespace
import torch
import numpy as np


def source_import(source_dir):
    from u0.models.n0 import N0
    return N0
binding = SimpleNamespace(source_import=source_import)

def selected_layers(aggregator, images):
    import torch
    if aggregator.training or aggregator.depth != 24 or aggregator.aa_block_size != 1 or (list(aggregator.aa_order) != ['frame', 'global']) or (aggregator.patch_start_idx != 5) or (images.ndim != 5) or (images.shape[2] != 3):
        raise ValueError('Unsupported aggregator contract')
    b, s, channels, h, w = images.shape
    normalized = (images - aggregator._resnet_mean) / aggregator._resnet_std
    normalized = normalized.view(b * s, channels, h, w)
    patches = aggregator.patch_embed(normalized)
    if isinstance(patches, dict):
        patches = patches['x_norm_patchtokens']

    def expand(value):
        query = value[:, 0:1].expand(b, 1, *value.shape[2:])
        others = value[:, 1:].expand(b, s - 1, *value.shape[2:])
        return torch.cat([query, others], dim=1).view(b * s, *value.shape[2:])
    tokens = torch.cat([expand(aggregator.camera_token), expand(aggregator.register_token), patches], dim=1)
    del patches, normalized
    pos = None
    if aggregator.rope is not None:
        pos = aggregator.position_getter(b * s, h // aggregator.patch_size, w // aggregator.patch_size, device=images.device)
        pos = pos + 1
        special = torch.zeros(b * s, aggregator.patch_start_idx, 2).to(images.device).to(pos.dtype)
        pos = torch.cat([special, pos], dim=1)
    _, p, c = tokens.shape
    fi = gi = 0
    result = [None] * 24
    for layer in range(24):
        tokens, fi, frame = aggregator._process_frame_attention(tokens, b, s, p, c, fi, pos=pos)
        tokens, gi, global_ = aggregator._process_global_attention(tokens, b, s, p, c, gi, pos=pos)
        if layer in (4, 11, 17, 23):
            result[layer] = torch.cat([frame[0], global_[0]], dim=-1)
        del frame, global_
    return (result, aggregator.patch_start_idx)

def native_sample(values, coords, native_hw, shape, endpoints=True):
    """Map native canvas coordinates through square padding and half-pixel resize."""
    import torch.nn.functional as F
    h, w = map(int, native_hw)
    oh, ow = shape
    if endpoints:
        u = torch.linspace(0, w, ow, device=values.device)
        v = torch.linspace(0, h, oh, device=values.device)
    else:
        u = (torch.arange(ow, device=values.device)+.5)*w/ow
        v = (torch.arange(oh, device=values.device)+.5)*h/oh
    boxes = torch.as_tensor(coords, device=values.device, dtype=torch.float32)
    # Pixel edge coordinates normalized for grid_sample(align_corners=False).
    x = boxes[:, 0, None] + u[None]/w*(boxes[:, 2]-boxes[:, 0])[:, None]
    y = boxes[:, 1, None] + v[None]/h*(boxes[:, 3]-boxes[:, 1])[:, None]
    grid = torch.stack((x[:, None, :].expand(-1,oh,-1), y[:, :, None].expand(-1,-1,ow)), -1)/512-1
    result = F.grid_sample(values.float().permute(0,3,1,2), grid, mode='bilinear', padding_mode='border', align_corners=False)
    return result.permute(0,2,3,1)


def head_outputs(model, blocks, inputs, start, slots, coords, native_hw, chunk):
    """Consume only anchor features; release each dense raster after sampling."""
    result = {k: [] for k in ('depth_grid','depth_conf_grid','depth_lo','depth_conf_lo','points_grid','points_conf_grid')}
    cuda = inputs.device.type == 'cuda'
    for offset in range(0, len(slots), chunk):
        selected = slots[offset:offset+chunk]
        small = [b[:, selected].contiguous() if b is not None else None for b in blocks]
        images = inputs[selected][None]
        box = coords[selected]
        with torch.autocast('cuda', dtype=torch.bfloat16, enabled=cuda):
            depth, conf = model.depth_head(small, images=images, patch_start_idx=start, frames_chunk_size=chunk)
        for key, raster in (('depth',depth[0]),('depth_conf',conf[0,...,None])):
            result[key+'_grid'].append(native_sample(raster,box,native_hw,(51,51))[...,0].cpu().numpy().astype(np.float32))
            result[key+'_lo'].append(native_sample(raster,box,native_hw,(120,160),False)[...,0].cpu().numpy().astype(np.float16))
        del depth, conf, raster
        with torch.autocast('cuda', dtype=torch.bfloat16, enabled=cuda):
            points, conf = model.point_head(small, images=images, patch_start_idx=start, frames_chunk_size=chunk)
        result['points_grid'].append(native_sample(points[0],box,native_hw,(51,51)).cpu().numpy().astype(np.float32))
        result['points_conf_grid'].append(native_sample(conf[0,...,None],box,native_hw,(51,51))[...,0].cpu().numpy().astype(np.float32))
        del points, conf, small, images
    return {k: np.concatenate(v,0) for k,v in result.items()}


class N1:
    def __init__(self, source_dir, weights_dir, device):
        from u0.models.n0 import N0
        self.model = N0.from_pretrained(str(Path(weights_dir).resolve()), local_files_only=True, enable_depth=True, enable_point=True).eval().to(device)
        self.model.local_camera_head.float()
        self.model.global_camera_head.float()
        self.device = torch.device(device)
        self.preprocess = importlib.import_module('u0.utils.load_fn').load_and_preprocess_images_square

    def extract(self, images, slots, native_hw, chunk=8):
        import torch.nn.functional as F
        from p import convert
        cuda = self.device.type == 'cuda'
        if cuda: torch.cuda.reset_peak_memory_stats(self.device)
        frames, coords = [], []
        with torch.inference_mode():
            for image in images:
                square, coordinate = self.preprocess([image],1024)
                frames.append(F.interpolate(square.to(self.device),size=(518,518),mode='bilinear',align_corners=False)[0])
                coords.append(coordinate[0,:4])
            inputs = torch.stack(frames); del frames
            coords = torch.stack(coords).float().cpu().numpy()
            with torch.autocast('cuda', dtype=torch.bfloat16, enabled=cuda):
                blocks, start = selected_layers(self.model.aggregator, inputs[None])
            if start != 5 or blocks[23].shape != (1,len(inputs),1374,2048):
                raise ValueError('Layer shape changed')
            with torch.autocast('cuda', enabled=False):
                camera = blocks[23][:,:,:1,:].float()
                local = self.model.local_camera_head([camera])[-1][0].float().cpu().numpy()
                global_ = self.model.global_camera_head([camera])[-1][0].float().cpu().numpy()
            result = convert(local,global_,coords)
            result.update(head_outputs(self.model,blocks,inputs,start,slots,coords,native_hw,chunk))
            transform = result['world_to_frame0']
            result['points_grid'] = (result['points_grid'] @ transform[:3,:3].T + transform[:3,3]).astype(np.float32)
            result['grid_uv'] = np.linspace(0,1000,51,dtype=np.float32)
        if cuda:
            torch.cuda.synchronize(self.device)
            result['peak_allocated_bytes'] = np.array(torch.cuda.max_memory_allocated(self.device),dtype=np.int64)
            result['peak_reserved_bytes'] = np.array(torch.cuda.max_memory_reserved(self.device),dtype=np.int64)
        else:
            result['peak_allocated_bytes'] = result['peak_reserved_bytes'] = np.array(0,dtype=np.int64)
        return result
