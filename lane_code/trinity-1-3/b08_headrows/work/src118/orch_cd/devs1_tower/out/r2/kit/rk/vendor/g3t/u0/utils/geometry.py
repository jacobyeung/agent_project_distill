import torch
import numpy as np
from u0.dependency.distortion import apply_distortion, iterative_undistortion, single_undistortion

def unproject_depth_map_to_point_map(depth_map: np.ndarray, extrinsics_cam: np.ndarray, intrinsics_cam: np.ndarray) -> np.ndarray:
    if isinstance(depth_map, torch.Tensor):
        depth_map = depth_map.cpu().numpy()
    if isinstance(extrinsics_cam, torch.Tensor):
        extrinsics_cam = extrinsics_cam.cpu().numpy()
    if isinstance(intrinsics_cam, torch.Tensor):
        intrinsics_cam = intrinsics_cam.cpu().numpy()
    world_points_list = []
    for frame_idx in range(depth_map.shape[0]):
        cur_world_points, _, _ = depth_to_world_coords_points(depth_map[frame_idx].squeeze(-1), extrinsics_cam[frame_idx], intrinsics_cam[frame_idx])
        world_points_list.append(cur_world_points)
    world_points_array = np.stack(world_points_list, axis=0)
    return world_points_array

def depth_to_world_coords_points(depth_map: np.ndarray, extrinsic: np.ndarray, intrinsic: np.ndarray, eps=1e-08) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if depth_map is None:
        return (None, None, None)
    point_mask = depth_map > eps
    cam_coords_points = depth_to_cam_coords_points(depth_map, intrinsic)
    cam_to_world_extrinsic = closed_form_inverse_se3(extrinsic[None])[0]
    R_cam_to_world = cam_to_world_extrinsic[:3, :3]
    t_cam_to_world = cam_to_world_extrinsic[:3, 3]
    world_coords_points = np.dot(cam_coords_points, R_cam_to_world.T) + t_cam_to_world
    return (world_coords_points, cam_coords_points, point_mask)

def depth_to_cam_coords_points(depth_map: np.ndarray, intrinsic: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    H, W = depth_map.shape
    assert intrinsic.shape == (3, 3), 'Intrinsic matrix must be 3x3'
    assert intrinsic[0, 1] == 0 and intrinsic[1, 0] == 0, 'Intrinsic matrix must have zero skew'
    fu, fv = (intrinsic[0, 0], intrinsic[1, 1])
    cu, cv = (intrinsic[0, 2], intrinsic[1, 2])
    u, v = np.meshgrid(np.arange(W), np.arange(H))
    x_cam = (u - cu) * depth_map / fu
    y_cam = (v - cv) * depth_map / fv
    z_cam = depth_map
    cam_coords = np.stack((x_cam, y_cam, z_cam), axis=-1).astype(np.float32)
    return cam_coords

def closed_form_inverse_se3(se3, R=None, T=None):
    is_numpy = isinstance(se3, np.ndarray)
    if se3.shape[-2:] != (4, 4) and se3.shape[-2:] != (3, 4):
        raise ValueError(f'se3 must be of shape (N,4,4), got {se3.shape}.')
    if R is None:
        R = se3[:, :3, :3]
    if T is None:
        T = se3[:, :3, 3:]
    if is_numpy:
        R_transposed = np.transpose(R, (0, 2, 1))
        top_right = -np.matmul(R_transposed, T)
        inverted_matrix = np.tile(np.eye(4), (len(R), 1, 1))
    else:
        R_transposed = R.transpose(1, 2)
        top_right = -torch.bmm(R_transposed, T)
        inverted_matrix = torch.eye(4, 4)[None].repeat(len(R), 1, 1)
        inverted_matrix = inverted_matrix.to(R.dtype).to(R.device)
    inverted_matrix[:, :3, :3] = R_transposed
    inverted_matrix[:, :3, 3:] = top_right
    return inverted_matrix

def project_world_points_to_camera_points_batch(world_points, cam_extrinsics):
    ones = torch.ones_like(world_points[..., :1])
    world_points_h = torch.cat([world_points, ones], dim=-1)
    extrinsics_exp = cam_extrinsics.unsqueeze(2).unsqueeze(3)
    world_points_h_exp = world_points_h.unsqueeze(-1)
    camera_points = torch.matmul(extrinsics_exp, world_points_h_exp).squeeze(-1)
    return camera_points

def project_world_points_to_cam(world_points, cam_extrinsics, cam_intrinsics=None, distortion_params=None, default=0, only_points_cam=False):
    device = world_points.device
    with torch.autocast(device_type=device.type, enabled=False):
        B = cam_extrinsics.shape[0]
        world_points_homogeneous = torch.cat([world_points, torch.ones_like(world_points[..., 0:1])], dim=1)
        world_points_homogeneous = world_points_homogeneous.unsqueeze(0).expand(B, -1, -1)
        cam_points = torch.bmm(cam_extrinsics, world_points_homogeneous.transpose(-1, -2))
        if only_points_cam:
            return (None, cam_points)
        image_points = img_from_cam(cam_intrinsics, cam_points, distortion_params, default=default)
        return (image_points, cam_points)

def img_from_cam(cam_intrinsics, cam_points, distortion_params=None, default=0.0):
    cam_points = cam_points / cam_points[:, 2:3, :]
    ndc_xy = cam_points[:, :2, :]
    if distortion_params is not None:
        x_distorted, y_distorted = apply_distortion(distortion_params, ndc_xy[:, 0], ndc_xy[:, 1])
        distorted_xy = torch.stack([x_distorted, y_distorted], dim=1)
    else:
        distorted_xy = ndc_xy
    cam_coords_homo = torch.cat((distorted_xy, torch.ones_like(distorted_xy[:, :1, :])), dim=1)
    pixel_coords = torch.bmm(cam_intrinsics, cam_coords_homo)
    pixel_coords = pixel_coords[:, :2, :]
    pixel_coords = torch.nan_to_num(pixel_coords, nan=default)
    return pixel_coords.transpose(1, 2)

def cam_from_img(pred_tracks, intrinsics, extra_params=None):
    principal_point = intrinsics[:, [0, 1], [2, 2]].unsqueeze(-2)
    focal_length = intrinsics[:, [0, 1], [0, 1]].unsqueeze(-2)
    tracks_normalized = (pred_tracks - principal_point) / focal_length
    if extra_params is not None:
        try:
            tracks_normalized = iterative_undistortion(extra_params, tracks_normalized)
        except:
            tracks_normalized = single_undistortion(extra_params, tracks_normalized)
    return tracks_normalized

def make_4x4(pose_3x4):
    assert pose_3x4.shape[-2:] == (3, 4)
    shape = pose_3x4.shape[:-2] + (4, 4)
    pose_4x4 = torch.eye(4, device=pose_3x4.device).expand(shape).clone()
    pose_4x4[..., :3, :4] = pose_3x4
    return pose_4x4

def make_4x4_np(pose_3x4):
    assert pose_3x4.shape[-2:] == (3, 4)
    shape = pose_3x4.shape[:-2] + (4, 4)
    pose_4x4 = np.broadcast_to(np.eye(4), shape).copy()
    pose_4x4[..., :3, :4] = pose_3x4
    return pose_4x4

def sRT_to_4x4(scale, R, T, device):
    trf = torch.eye(4, device=device)
    trf[:3, :3] = R * scale
    trf[:3, 3] = T.ravel()
    return trf

def inv(mat):
    if isinstance(mat, torch.Tensor):
        return torch.linalg.inv(mat)
    if isinstance(mat, np.ndarray):
        return np.linalg.inv(mat)
    raise ValueError(f'bad matrix type = {type(mat)}')

def geotrf(Trf, pts, ncol=None, norm=False):
    assert Trf.ndim >= 2
    if isinstance(Trf, np.ndarray):
        pts = np.asarray(pts)
    elif isinstance(Trf, torch.Tensor):
        pts = torch.as_tensor(pts, dtype=Trf.dtype)
    output_reshape = pts.shape[:-1]
    ncol = ncol or pts.shape[-1]
    if isinstance(Trf, torch.Tensor) and isinstance(pts, torch.Tensor) and (Trf.ndim == 3) and (pts.ndim == 4):
        d = pts.shape[3]
        if Trf.shape[-1] == d:
            pts = torch.einsum('bij, bhwj -> bhwi', Trf, pts)
        elif Trf.shape[-1] == d + 1:
            pts = torch.einsum('bij, bhwj -> bhwi', Trf[:, :d, :d], pts) + Trf[:, None, None, :d, d]
        else:
            raise ValueError(f'bad shape, not ending with 3 or 4, for pts.shape={pts.shape!r}')
    else:
        if Trf.ndim >= 3:
            n = Trf.ndim - 2
            assert Trf.shape[:n] == pts.shape[:n], 'batch size does not match'
            Trf = Trf.reshape(-1, Trf.shape[-2], Trf.shape[-1])
            if pts.ndim > Trf.ndim:
                pts = pts.reshape(Trf.shape[0], -1, pts.shape[-1])
            elif pts.ndim == 2:
                pts = pts[:, None, :]
        if pts.shape[-1] + 1 == Trf.shape[-1]:
            Trf = Trf.swapaxes(-1, -2)
            pts = pts @ Trf[..., :-1, :] + Trf[..., -1:, :]
        elif pts.shape[-1] == Trf.shape[-1]:
            Trf = Trf.swapaxes(-1, -2)
            pts = pts @ Trf
        else:
            pts = Trf @ pts.T
            if pts.ndim >= 2:
                pts = pts.swapaxes(-1, -2)
    if norm:
        pts = pts / pts[..., -1:]
        if norm != 1:
            pts *= norm
    res = pts[..., :ncol].reshape(*output_reshape, ncol)
    return res
