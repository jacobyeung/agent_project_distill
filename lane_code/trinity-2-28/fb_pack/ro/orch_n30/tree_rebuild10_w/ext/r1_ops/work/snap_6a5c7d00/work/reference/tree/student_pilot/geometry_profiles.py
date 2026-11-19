"""Explicit metric geometry. OpenCV cameras; gravity-aligned z-up world.

Pixels use edge-origin centres (column+.5,row+.5). K maps camera rays to
source pixels. canvas_to_source maps normalized [0,1000] coordinates through
the inverse crop/resize. No implicit pose, depth or scale conversions occur.
"""
from dataclasses import dataclass
import hashlib
import math
import numpy as np
from .scene_state import FrameMap, digest


class GeometryError(ValueError):
    pass


PROFILES = {
    'scaled_g3t_metric': dict(depth_source='g3t', depth_unit='metric', pose_unit='metric',
                              depth_scale_count=1, pose_scale_count=1),
    'legacy_v3122': dict(depth_source='vc', depth_unit='metric', pose_unit='metric',
                        depth_scale_count=0, pose_scale_count=1),
    'scaled_g3t_depth': dict(depth_source='g3t', depth_unit='unscaled', pose_unit='unscaled',
                           depth_scale_count=0, pose_scale_count=0),
}


def profile(name):
    if name not in PROFILES:
        raise GeometryError('unknown_geometry_profile:' + str(name))
    return dict(PROFILES[name])


@dataclass(frozen=True)
class GeometryContract:
    profile: str
    frame_map: FrameMap
    reference_source_frame: int
    K: object
    canvas_to_source: object
    camera_to_world: object
    scale: float
    depth_source: str
    depth_unit: str
    pose_unit: str
    depth_scale_count: int
    pose_scale_count: int
    depth_kind: str = 'optical_axis'
    pixel_centres: str = 'edge_origin_half'
    camera_axes: str = 'x_right_y_down_z_forward'
    world_axes: str = 'x_right_y_heading_z_up'
    gravity_up: tuple = (0., 0., 1.)
    point_space: str = 'camera'
    pose_application_count: int = 0
    ground_truth_substitution: bool = False

    def validate(self):
        expected = profile(self.profile)
        if self.ground_truth_substitution:
            if self.profile != 'legacy_v3122' or self.scale != 1.:
                raise GeometryError('gt_requires_legacy_metric_geometry')
            expected = dict(depth_source='gt',depth_unit='metric',pose_unit='metric',
                            depth_scale_count=0,pose_scale_count=0)
        for k, v in expected.items():
            if getattr(self, k) != v:
                raise GeometryError('profile_contract_mismatch:' + k)
        if self.reference_source_frame != self.frame_map.source_indices[0]:
            raise GeometryError('wrong_reference_camera')
        if (self.camera_axes != 'x_right_y_down_z_forward'
                or self.world_axes != 'x_right_y_heading_z_up'
                or self.pixel_centres != 'edge_origin_half'
                or not np.array_equal(self.gravity_up, [0., 0., 1.])):
            raise GeometryError('coordinate_convention_mismatch')
        if self.point_space != 'camera' or self.pose_application_count != 0:
            raise GeometryError('points_already_transformed')
        if self.depth_kind not in ('optical_axis', 'ray'):
            raise GeometryError('unknown_depth_kind')
        if not math.isfinite(self.scale) or self.scale <= 0:
            raise GeometryError('invalid_scale')
        K = np.asarray(self.K, float)
        A = np.asarray(self.canvas_to_source, float)
        C = np.asarray(self.camera_to_world, float)
        if (K.shape != (32, 3, 3) or A.shape != (32, 3, 3) or C.shape != (32, 4, 4)
                or not all(np.isfinite(v).all() for v in (K, A, C))):
            raise GeometryError('missing_or_invalid_K_transform')
        if (np.any(K[:, [0, 1], [0, 1]] <= 0) or not np.allclose(K[:, 2], [0, 0, 1])
                or not np.allclose(K[:, 1, 0], 0) or not np.allclose(K[:, 0, 1], 0)
                or not np.allclose(A[:, 2], [0, 0, 1])
                or np.any(np.linalg.det(A[:, :2, :2]) <= 0)
                or not np.allclose(C[:, 3], [0, 0, 0, 1])):
            raise GeometryError('invalid_intrinsics_or_affine')
        R = C[:, :3, :3]
        if (not np.allclose(R @ R.transpose(0, 2, 1), np.eye(3), atol=1e-6)
                or not np.allclose(np.linalg.det(R), 1., atol=1e-6)):
            raise GeometryError('camera_rotation_not_proper')
        if -R[0, 2, 1] <= 0:
            raise GeometryError('reference_camera_up_opposes_gravity')
        return self

    @property
    def identity(self):
        scalar = {k: v for k, v in vars(self).items() if k not in
                  ('K', 'canvas_to_source', 'camera_to_world', 'frame_map')}
        scalar['frames'] = self.frame_map.source_indices
        for k in ('K', 'canvas_to_source', 'camera_to_world'):
            scalar[k] = hashlib.sha256(np.asarray(getattr(self, k), dtype='<f8').tobytes()).hexdigest()
        return digest(scalar)


@dataclass(frozen=True)
class Points:
    values: object
    space: str = 'camera'
    pose_applications: int = 0


class ProfileGeometry:
    def __init__(self, contract, depth_grid, grid_uv=None):
        self.contract = contract.validate()
        self.frame_map = contract.frame_map
        self.identity = contract.identity
        self.depth_grid = np.array(depth_grid, dtype=float, copy=True)
        if self.depth_grid.ndim != 3 or self.depth_grid.shape[0] != 32:
            raise GeometryError('expected_depth_grid_32_H_W')
        self.grid_uv = np.asarray(np.linspace(0, 1000, self.depth_grid.shape[1]) if grid_uv is None else grid_uv)
        if (self.depth_grid.shape[1] != self.depth_grid.shape[2]
                or not np.array_equal(self.grid_uv, np.linspace(0, 1000, len(self.grid_uv)))
                or self.depth_grid.shape[1] != len(self.grid_uv)):
            raise GeometryError('depth_grid_requires_square_endpoint_canvas')
        self.K = np.array(contract.K, dtype=float, copy=True)
        self.A = np.array(contract.canvas_to_source, dtype=float, copy=True)
        self.C = np.array(contract.camera_to_world, dtype=float, copy=True)
        if contract.profile == 'scaled_g3t_depth':
            self.depth_grid *= contract.scale
            self.C[:, :3, 3] *= contract.scale
        self.depth_scale_count = contract.depth_scale_count + (contract.profile == 'scaled_g3t_depth')
        self.pose_scale_count = 1
        self.identity = digest(dict(contract=self.identity, depth=hashlib.sha256(self.depth_grid.tobytes()).hexdigest()))
        for array in (self.depth_grid,self.K,self.A,self.C):
            array.setflags(write=False)

    def has(self, frame):
        return type(frame) is int and 1 <= frame <= 32

    def cam(self, frame):
        if not self.has(frame):
            raise GeometryError('invalid_display_frame')
        return self.C[frame-1, :3, :3], self.C[frame-1, :3, 3]

    def rays(self, frame, uv):
        p = np.column_stack((uv, np.ones(len(uv)))) @ self.A[frame-1].T
        return p @ np.linalg.inv(self.K[frame-1]).T

    def _raw_depth(self, frame, uv):
        d = self.depth_grid[frame-1]
        x, y = np.clip(np.asarray(uv) * ((len(d)-1)/1000), 0, len(d)-1).T
        x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
        x1, y1 = np.minimum(x0+1, len(d)-1), np.minimum(y0+1, len(d)-1)
        fx, fy = x-x0, y-y0
        return d[y0,x0]*(1-fx)*(1-fy)+d[y0,x1]*fx*(1-fy)+d[y1,x0]*(1-fx)*fy+d[y1,x1]*fx*fy

    def depth(self, frame, uv):
        d = self._raw_depth(frame, uv)
        if self.contract.depth_kind == 'ray':
            d = d / np.linalg.norm(self.rays(frame, uv), axis=1)
        return d

    def to_world(self, frame, points):
        if points.space != 'camera' or points.pose_applications != 0:
            raise GeometryError('double_pose_application')
        R, t = self.cam(frame)
        return Points(np.asarray(points.values) @ R.T + t, 'world', 1)

    def lift(self, frame, uv, mode='center'):
        if mode != 'center':
            raise GeometryError('centre_depth_required')
        uv = np.asarray(uv, float)
        offsets = np.array([(dx,dy) for dx in np.linspace(-10,10,5) for dy in np.linspace(-10,10,5)])
        stencil = np.clip(uv[:,None]+offsets,0,1000)
        d = self.depth(frame, stencil.reshape(-1,2)).reshape(len(uv),25)
        p20,p50,p80 = np.percentile(d,(20,50,80),axis=1)
        pc = self.rays(frame,uv) * self.depth(frame,uv)[:,None]
        return self.to_world(frame,Points(pc)).values, pc, (p80-p20)/np.maximum(p50,1e-3)

    def fov_of(self, frame):
        # ofs visibility assumes a centred, uncropped pinhole. Refuse other
        # canvases rather than silently project them with symmetric FoV.
        Kc = np.linalg.inv(self.A[frame-1]) @ self.K[frame-1]
        if not np.allclose(Kc[:2,2],[500,500]):
            raise GeometryError('ofs_visibility_requires_centred_canvas')
        return 2*np.arctan(500/Kc[1,1]), 2*np.arctan(500/Kc[0,0])

    def _depth(self, index, u, v):
        return self.depth(index+1, np.column_stack((u,v)))


class ContractAdapter:
    """Validate provenance while retaining an existing exact lifting arithmetic."""
    def __init__(self, geometry, contract, *, depth_identity):
        self.contract = contract.validate()
        if contract.profile not in ('legacy_v3122','scaled_g3t_metric') or contract.depth_kind != 'optical_axis':
            raise GeometryError('exact_adapter_requires_legacy_optical_depth')
        self.geometry, self.frame_map = geometry, contract.frame_map
        if not depth_identity:
            raise GeometryError('depth_identity_required')
        self.identity = digest(dict(contract=contract.identity,depth=depth_identity))
        for k in range(1,33):
            R,t = geometry.cam(k)
            if not (np.allclose(R, np.asarray(contract.camera_to_world)[k-1,:3,:3],atol=1e-9)
                    and np.allclose(t,np.asarray(contract.camera_to_world)[k-1,:3,3],atol=1e-9)):
                raise GeometryError('camera_contract_mismatch')
        if hasattr(geometry,'fov_of'):
            for k in range(1,33):
                fh,fw=geometry.fov_of(k)
                effective=np.linalg.inv(np.asarray(contract.canvas_to_source)[k-1]) @ np.asarray(contract.K)[k-1]
                expected=np.array([[500/np.tan(fw/2),0,500],[0,500/np.tan(fh/2),500],[0,0,1]])
                if not np.allclose(effective,expected,atol=1e-7):
                    raise GeometryError('K_disagrees_with_exact_geometry')

    def __getattr__(self, name):
        return getattr(self.geometry,name)


def legacy_from_heads(path, frame_map, loader):
    """Bind the declared ttower legacy cache format, including its FoV-derived K.

    These caches already scale pose translation and retain metric V-C depth.
    FoV defines a centred pinhole on the native canvas; it is never a missing-K
    fallback for arbitrary inputs. The file hash pins depth and pose together.
    """
    from .ground_sources import file_sha256
    with np.load(path,allow_pickle=False) as z:
        frame_map.require(z['anchor_frame_indices'].tolist())
        if 'depth_grid' not in z or z['depth_grid'].shape != (32,51,51):
            raise GeometryError('legacy_requires_depth_grid_32_51_51')
        if 'grid_uv' not in z or not np.array_equal(z['grid_uv'],np.linspace(0,1000,51)):
            raise GeometryError('legacy_requires_endpoint_grid')
        if str(z['layout']) != 'per_frame':
            raise GeometryError('legacy_requires_exact_per_frame_layout')
        R,t,fov=z['r_grav'],z['t_grav'],z['fov_hw']
        H,W=map(int,z['source_hw'])
        C=np.repeat(np.eye(4)[None],32,axis=0);C[:,:3,:3]=R;C[:,:3,3]=t
        K=np.zeros((32,3,3));K[:,0,0]=W/(2*np.tan(fov[:,1]/2));K[:,1,1]=H/(2*np.tan(fov[:,0]/2))
        K[:,0,2]=W/2;K[:,1,2]=H/2;K[:,2,2]=1
        A=np.repeat(np.diag([W/1000,H/1000,1.])[None],32,axis=0)
        c=GeometryContract('legacy_v3122',frame_map,frame_map.source_indices[0],K,A,C,
                           float(z['scale']),'vc','metric','metric',0,1)
    return ContractAdapter(loader(path),c,depth_identity=file_sha256(path))


def scaled_from_heads(path, frame_map):
    """Bind an explicitly unscaled G3T export; apply s to depth and translation once."""
    with np.load(path,allow_pickle=False) as z:
        frame_map.require(z['anchor_frame_indices'].tolist())
        required = dict(profile='scaled_g3t_depth',depth_unit='unscaled',pose_unit='unscaled')
        if any(str(z[k]) != v for k,v in required.items()):
            raise GeometryError('scaled_export_requires_unscaled_units')
        c=GeometryContract('scaled_g3t_depth',frame_map,int(z['reference_source_frame']),
            z['K'],z['canvas_to_source'],z['camera_to_world'],float(z['scale']),
            'g3t','unscaled','unscaled',int(z['depth_scale_count']),int(z['pose_scale_count']))
        return ProfileGeometry(c,z['depth_grid'],z['grid_uv'])
