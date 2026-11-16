"""Pinned rkit native aggregation, sampling and pose conversion operations."""
from pathlib import Path
import numpy as np
import torch
from .camera_targets import encode_cameras, encode_gravity

def selected_layers(aggregator, images, layers=(4, 11, 17, 23)):
    import torch
    if aggregator.training or aggregator.depth != 24 or aggregator.aa_block_size != 1 or (list(aggregator.aa_order) != ['frame', 'global']) or (aggregator.patch_start_idx != 5) or (images.ndim != 5) or (images.shape[2] != 3):
        raise ValueError('Unsupported aggregator contract')
    if any(type(i) is not int or not 0 <= i < 24 for i in layers):
        raise ValueError('Invalid selected aggregator layer')
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
        if layer in layers:
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


def lift(extri):
    bottom = torch.tensor([0., 0., 0., 1.], dtype=extri.dtype, device=extri.device)
    return torch.cat((extri, bottom.expand(*extri.shape[:-2], 1, 4)), dim=-2)


def convert(local, global_, coords):
    from .c1r_ref import source_import
    source_import(Path(__file__).parent / "g3t_vendor")
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    local, global_, coords = np.asarray(local), np.asarray(global_), np.asarray(coords)
    if (local.ndim != 2 or local.shape[1] != 6 or len(local) not in (32, 64, 96)
            or global_.shape != (len(local), 5) or coords.shape != (len(local), 4)
            or not all(np.isfinite(v).all() for v in (local, global_, coords))
            or (np.linalg.norm(local[:, :4], axis=1) < 1e-6).any()
            or (np.linalg.norm(global_[:, 3:], axis=1) < 1e-6).any()
            or (local[:, 4:] <= 0).any() or (local[:, 4:] >= np.pi).any()
            or (coords[:, :2] < 0).any() or (coords[:, 2:] > 1024).any()
            or (coords[:, 2:] <= coords[:, :2]).any()):
        raise ValueError('Invalid camera arrays')
    with torch.inference_mode():
        g2c, intr = pose_encoding_to_extri_intri(torch.as_tensor(local)[None].float(),
            (518, 518), pose_encoding_type='noT_quaR_FoV')
        w2g, _ = pose_encoding_to_extri_intri(torch.as_tensor(global_)[None].float(),
            (518, 518), pose_encoding_type='absT_quaRy_noFoV', build_intrinsics=False)
        w2c = (lift(g2c) @ lift(w2g))[0].double().numpy()
        intr = intr[0].double().numpy()
    c2w = np.linalg.inv(w2c)
    box = coords.astype(np.float64) * (518. / 1024.)
    intr[:, 0, 2] -= box[:, 0]
    intr[:, 1, 2] -= box[:, 1]
    hw = np.stack((box[:, 3] - box[:, 1], box[:, 2] - box[:, 0]), axis=-1)
    raw, mask, step = encode_cameras(c2w, intr, hw, all_frames=True)
    up, ok = encode_gravity(c2w, world_up=(0., -1., 0.))
    if not mask.all() or not ok or not np.isfinite(raw).all():
        raise ValueError('Camera conversion failed')
    return dict(raw_pose=raw, gravity_up=up.astype(np.float32), trajectory_step=np.array(step),
                local_pose_enc=local.astype(np.float32), global_pose_enc=global_.astype(np.float32),
                coords_1024=coords.astype(np.float32), world_to_frame0=w2c[0].astype(np.float32))
