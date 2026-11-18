"""Artifact-bound, parameter-free readouts of the model's own geometry heads."""
import math
import numpy as np
import torch
from torch import nn


class DepthReadout(nn.Module):
    inputs = ['depth_map', 'fov_hw', 'uv', 'frame', 'depth_head']
    outputs = ['depth_p30', 'spread', 'camera_point', 'stencil_depth']

    def __init__(self):
        super().__init__()
        # Integer ratios survive model-wide dtype conversions without changing decimal constants.
        self.register_buffer('stencil', torch.tensor([(x,y) for x in (-10,-5,0,5,10) for y in (-10,-5,0,5,10)]))
        self.register_buffer('clip_ratio', torch.tensor([9999,10]))
        self.register_buffer('percentiles', torch.tensor([20,30,50,80]))
        self.register_buffer('spread_floor_ratio', torch.tensor([1,1000]))
        self.register_buffer('half_grid', torch.tensor(500))
        self.register_buffer('camera_precision', torch.tensor(8))

    def forward(self, depth_map, fov_hw, uv, frame, depth_head, *, sampled=None):
        uv = np.asarray(uv, dtype=np.float64)
        clip = self.clip_ratio.tolist()
        points = np.clip(uv[None] + self.stencil.cpu().numpy(), 0, clip[0]/clip[1])
        if sampled is None:
            query = torch.full((depth_map.shape[0],len(points),2),float(self.half_grid),device=depth_map.device)
            query[frame-1] = torch.as_tensor(points,dtype=torch.float32,device=query.device)
            sampled = depth_head.query(depth_map,query)[frame-1]
        values = sampled.detach().double().cpu().numpy() if isinstance(sampled,torch.Tensor) else np.asarray(sampled,dtype=np.float64)
        if values.shape != (len(points),) or not np.isfinite(values).all() or (values<=0).any():
            raise ValueError('invalid own depth')
        p20,p30,p50,p80 = (np.percentile(values,q) for q in self.percentiles.tolist())
        floor = self.spread_floor_ratio.tolist()
        spread = (p80-p20)/max(p50,floor[0]/floor[1])
        vertical,horizontal = map(float,fov_hw)
        ray = np.array([(uv[0]/int(self.half_grid)-1)*math.tan(horizontal/2),
                        (uv[1]/int(self.half_grid)-1)*math.tan(vertical/2),1.])
        # Match the row producer's rounding before its public-coordinate transform.
        camera = np.round(ray*p30,int(self.camera_precision)) + 0.0
        return dict(depth_p30=float(p30),spread=float(spread),camera_point=torch.from_numpy(camera),
                    stencil_depth=torch.from_numpy(values))


class HeadingReadout(nn.Module):
    inputs = ['operation', 'first_rotation', 'second_rotation', 'threshold']
    outputs = ['degrees', 'heading_available']

    def __init__(self, heading_plane_min=0.3):
        super().__init__()
        self.register_buffer('half_circle',torch.tensor(180))
        self.register_buffer('full_circle',torch.tensor(360))
        self.register_buffer('pi_ratio',torch.tensor(math.pi.as_integer_ratio()))
        if not 0<float(heading_plane_min)<1:raise ValueError('invalid heading threshold')
        self.register_buffer('threshold_ratio',torch.tensor(float(heading_plane_min).as_integer_ratio()))

    def forward(self, operation, first_rotation, second_rotation=None, threshold=None):
        first=np.asarray(first_rotation,dtype=np.float64)
        pi_num,pi_den=self.pi_ratio.tolist()
        pi=pi_num/pi_den
        if operation=='availability':
            num,den=self.threshold_ratio.tolist()
            saved=num/den
            if threshold is not None and threshold!=saved:raise ValueError('heading threshold differs from artifact')
            down=np.asarray(second_rotation,dtype=np.float64)
            down=down/np.linalg.norm(down)
            return bool(np.linalg.norm((first.T@down)[:2])>=saved)
        if operation=='yaw':
            return round(math.atan2(-first[0][2],first[2][2])*(int(self.half_circle)/pi))
        if operation!='turn':raise ValueError('unknown heading operation')
        a=first[[0,2],2];b=np.asarray(second_rotation,dtype=np.float64)[[0,2],2]
        angle=round(math.atan2(a[0]*b[1]-a[1]*b[0],float(a@b))*(int(self.half_circle)/pi))
        half,full=int(self.half_circle),int(self.full_circle)
        return (angle+half)%full-half if (angle+half)%full else half
