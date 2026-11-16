import numpy as np
import torch
from e import encode_cameras, encode_gravity
from u0.utils.pose_enc import pose_encoding_to_extri_intri


def lift(extri):
    bottom = torch.tensor([0., 0., 0., 1.], dtype=extri.dtype, device=extri.device)
    return torch.cat((extri, bottom.expand(*extri.shape[:-2], 1, 4)), dim=-2)


def convert(local, global_, coords):
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
