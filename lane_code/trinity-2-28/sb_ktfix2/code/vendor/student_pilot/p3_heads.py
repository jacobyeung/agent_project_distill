"""Authenticated head architecture and single-prefix feature capture."""
from contextlib import AbstractContextManager
import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .camera_head import CameraSupervision
from .auxiliary_losses import final_norm, camera_hooks, camera_head_inputs, visual_grids
from .point_depth_head import vit_layer_hooks, vit_grids_by_row
from .camera_targets import to_gravity_reference_frame, gravity_reference_rotation
from .p3_geometry import Geometry


class P3Heads(nn.Module):
    def __init__(self, config):
        super().__init__()
        settings = config.p3
        backing = settings['feature_backing']
        if backing not in ('decoupled_v', 'decoupled_vc', 'carrier'):
            raise ValueError('Unknown feature backing')
        self.backing = backing
        self.camera_final_layer = config.text_config.num_hidden_layers
        self.camera_carrier = settings.get('carrier_id')
        self.has_camera = True
        dim = config.vision_config.hidden_size if backing != 'carrier' else config.text_config.hidden_size
        self.camera = CameraSupervision(dim, settings['camera'], vit_dim=config.vision_config.hidden_size)
        if self.camera.spatial_pose is not None and backing == 'carrier':
            raise ValueError('Spatial pose input requires a decoupled ViT backing')
        if max(self.camera.settings['feature_layers'] or [0])>self.camera_final_layer:
            raise ValueError('Carrier feature layer exceeds actual decoder depth')
        if max(self.camera.point_depth.settings['vit_layers'] if self.camera.point_depth else [0])>config.vision_config.depth:
            raise ValueError('Head feature layer exceeds actual vision depth')
        if self.camera.point_depth is None or not self.camera.has_gravity or not self.camera.has_scale:
            raise ValueError('P3 needs depth, FoV, pose, gravity and trajectory-scale branches')
        if backing != 'carrier' and self.camera.settings['feature_layers'] is not None:
            raise ValueError('decoupled_v cannot consume decoder layers')
        anchors = settings['anchors']
        if anchors not in (list(range(2,33,2)),list(range(1,33))):
            raise ValueError('Head artifacts must name fused anchors or all 32 frames')
        if len(anchors) != 16:
            # Stage-1 all-frame artifacts explicitly carry this enlarged group embedding.
            old = self.camera.point_depth.group_embed
            self.camera.point_depth.group_embed = nn.Parameter(torch.zeros(len(anchors), old.shape[1]))
            if backing == 'carrier' or settings['temporal_grouping'] != 'fused_pairs_all_frames':
                raise ValueError('All-frame heads require the explicit decoupled per-frame-query artifact')
            self.frame_queries = nn.Parameter(torch.zeros(32, dim))


class PrefixCapture(AbstractContextManager):
    """Hooks run during the actual language prefix forward, never a carrier re-prefill.

    Carrier features are prefix causal states and change when the LM trains.
    decoupled_v never reads a decoder state; its coarse stream is pooled ViT.
    """
    def __init__(self, model, batch):
        self.model, self.batch = model, batch
        self.heads = model.auxiliary_heads
        self.captured, self.vit, self.states, self.grids, self.vits = {}, {}, None, None, None
        self.handles = []
        self.forward_count = 0

    def __enter__(self):
        if self.heads.backing == 'carrier':
            if len(self.model.config.p3['anchors']) != 16:
                raise ValueError('Legacy carrier supervision requires its 16 anchor groups')
            self.group_handles = camera_hooks(self.model, self.heads, self.batch, self.captured, self.vit)

            def norm_hook(module, args, output):
                if self.states is not None:
                    return
                self.forward_count += 1
                layers, grids, vits = camera_head_inputs(self.heads, self.model, self.batch, output,
                                                        self.captured, self.vit, True)
                self.states = self.heads.camera.carrier_states(output, self.batch['aux_camera_positions'], layers)
                self.grids, self.vits = grids, vits
                self.hidden, self.layers = output, layers
            self.handles.append(final_norm(self.model).register_forward_hook(norm_hook))
        else:
            self.group_handles = None
            self.handles.extend(vit_layer_hooks(self.model, self.heads.camera.point_depth.settings['vit_layers'], self.vit))
        return self

    def finish(self):
        if self.heads.backing in ('decoupled_v', 'decoupled_vc') and self.states is None:
            layers = self.heads.camera.point_depth.settings['vit_layers']
            if set(self.vit) != set(layers):
                raise ValueError('Ordinary video prefix did not capture every ViT feature layer')
            merge = self.model.config.vision_config.spatial_merge_size
            streams = [vit_grids_by_row(self.vit[k], self.batch['video_grid_thw'], merge) for k in layers]
            self.vits = [[stream[i] if self.heads.backing == 'decoupled_vc' else stream[i].detach()
                          for stream in streams] for i in range(len(streams[0]))]
            self.grids = [F.avg_pool2d(v[-1].permute(0, 3, 1, 2), 2).permute(0, 2, 3, 1) for v in self.vits]
            self.states = torch.stack([grid.mean((1, 2)) for grid in self.grids])
            if hasattr(self.heads, 'frame_queries'):
                copies = 1 if self.model.config.p3.get('frame_layout', 'spread') in ('duplicate', 'paired') else 2
                self.grids = [grid.repeat_interleave(copies,dim=0) for grid in self.grids]
                self.vits = [[v.repeat_interleave(copies,dim=0) for v in streams] for streams in self.vits]
                self.states = self.states.repeat_interleave(copies,dim=1)+self.heads.frame_queries[None, :self.states.shape[1] * copies]
            self.forward_count += 1
        if self.states is None:
            raise ValueError('No ordinary prefix features captured')
        if self.states.shape[1] != len(self.model.config.p3['anchors']):
            raise ValueError('Temporal grouping differs from the authenticated head artifact')
        return self

    def pose_inputs(self, row=None):
        """Spatial camera tokens use fused grids; depth retains its per-frame grids."""
        if self.heads.camera.spatial_pose is None:
            return {}
        rows = self.vits if row is None else [self.vits[row]]
        if hasattr(self.heads, 'frame_queries'):
            return dict(spatial_grids=[v[-1][::2] for v in rows],
                        frame_queries=self.heads.frame_queries[:self.states.shape[1]])
        return dict(spatial_grids=[v[-1] for v in rows])

    def geometry(self, row=0):
        self.finish()
        camera = self.heads.camera
        with torch.no_grad():
            stages, gravity, scale = camera.predict_all(self.states[row:row+1], **self.pose_inputs(row))
            raw = stages[-1][0].double().cpu().numpy()
            up = gravity[-1][0].double().cpu().numpy()
            # Existing camera targets are metric. trajectory scale never rescales them.
            unit = self.model.config.p3['translation_convention']
            factor = 1. if unit == 'metric' else float(torch.exp(scale[-1][0]).item())
            if unit not in ('metric', 'trajectory_normalized'):
                raise ValueError('Unknown translation convention')
            r, c, fov = to_gravity_reference_frame(raw, up)
            fmap = camera.point_depth.encode(self.grids[row], self.vits[row], stages[-1][0, :, 7:9])
        anchors = tuple(self.model.config.p3['anchors'])

        def depth(k, points):
            with torch.no_grad():
                uv = torch.as_tensor(points, dtype=torch.float32, device=fmap.device)[None]
                return camera.point_depth.query(fmap[anchors.index(k):anchors.index(k)+1], uv)[0].double().cpu().numpy()
        return Geometry(r, c, fov, depth, anchors=anchors, origin_rotation=gravity_reference_rotation(up),
                        up=(0, 0, 1),translation_scale_m=factor,depth_scale_m=1.,
                        pose_input=camera.settings.get('pose_input'))

    def supervised_loss(self, targets):
        self.finish()
        if self.heads.backing != 'carrier':
            raise ValueError('Stage-2 decoupled heads are frozen and do not accept a head loss')
        needed = ('aux_camera_target', 'aux_camera_mask', 'aux_camera_scale', 'aux_gravity_target',
                  'aux_gravity_mask', 'aux_point_depth_uv', 'aux_point_depth_gt', 'aux_point_depth_mask')
        if any(k not in targets for k in needed):
            raise ValueError('Carrier supervised head loss needs complete explicit targets')
        for key in ('aux_camera_mask', 'aux_gravity_mask', 'aux_point_depth_mask'):
            if not bool(targets[key].any()):
                raise ValueError('Carrier supervised head loss requires valid targets: ' + key)
        for key in needed:
            if targets[key].is_floating_point() and not torch.isfinite(targets[key]).all():
                raise ValueError('Nonfinite head supervision')
        return self.heads.camera.loss(self.hidden, {**targets, 'aux_camera_positions': self.batch['aux_camera_positions']},
                                      self.layers, self.grids, self.vits)

    def __exit__(self, *exc):
        for h in self.handles:
            h.remove()
        if self.group_handles is not None:
            self.group_handles.remove()
