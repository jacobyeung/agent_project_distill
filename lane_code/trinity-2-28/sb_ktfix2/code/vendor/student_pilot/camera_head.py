"""Cambrian-P camera supervision: learned camera tokens, a linear projector and a VGGT-style camera head.

The head follows VGGT's CameraHead as Cambrian-P instantiates it (trunk depth 4
of bidirectional self-attention blocks over the per-group camera tokens, adaLN
pose embedding and iterative refinement). The loss is Cambrian-P's weighted L1
on [t, q, fov] with the translation term divided by the trajectory scale.
"""
import math

import torch
from torch import nn
from torch.nn import functional as F

from .camera_config import g3t_prior_enabled, normalize
from .geometry_input import GatedCameraHeadBypass, GatedCameraTokenConnector
from .point_depth_head import PointDepthHead, point_depth_enabled

TARGET_DIM = 9


def canon_unit_quat(q, fallback=None, eps=1e-6):
    """Normalize xyzw quaternion along dim=-1 and canonicalize hemisphere (w > 0, or w == 0 and first nonzero xyz > 0)."""
    id_q = torch.zeros_like(q)
    id_q[..., 3] = 1.0
    if fallback is not None:
        fb = fallback.to(device=q.device, dtype=q.dtype)
        fb = torch.where(fb.norm(dim=-1, keepdim=True) < eps, id_q, fb)
    else:
        fb = id_q
    q_safe = torch.where(q.norm(dim=-1, keepdim=True) < eps, fb, q)
    q_unit = F.normalize(q_safe, dim=-1, eps=eps)
    x, y, z, w = q_unit[..., 0:1], q_unit[..., 1:2], q_unit[..., 2:3], q_unit[..., 3:4]
    neg = (
        (w < 0.0)
        | ((w == 0.0) & (x < 0.0))
        | ((w == 0.0) & (x == 0.0) & (y < 0.0))
        | ((w == 0.0) & (x == 0.0) & (y == 0.0) & (z < 0.0))
    )
    sign = torch.where(neg, -torch.ones_like(w), torch.ones_like(w))
    return q_unit * sign + 0.0


class Mlp(nn.Module):
    def __init__(self, dim, hidden, out):
        super().__init__()
        self.fc1, self.act, self.fc2 = nn.Linear(dim, hidden), nn.GELU(), nn.Linear(hidden, out)

    def forward(self, x):
        return self.fc2(self.act(self.fc1(x)))


class Attention(nn.Module):
    def __init__(self, dim, heads):
        super().__init__()
        self.heads = heads
        self.qkv, self.proj = nn.Linear(dim, 3 * dim), nn.Linear(dim, dim)

    def forward(self, x, key_mask=None):
        batch, length, dim = x.shape
        q, k, v = self.qkv(x).view(batch, length, 3, self.heads, dim // self.heads).permute(2, 0, 3, 1, 4)
        # key_mask [B, L] (True = a real camera token) hides the padded groups of a pose-only sample with fewer
        # than 16 groups; None (every token real) keeps the original call exactly.
        mask = None if key_mask is None else key_mask[:, None, None, :]
        out = F.scaled_dot_product_attention(q, k, v, attn_mask=mask, is_causal=False)
        return self.proj(out.transpose(1, 2).reshape(batch, length, dim))


class Block(nn.Module):
    def __init__(self, dim, heads, mlp_ratio=4, init_values=0.01):
        super().__init__()
        self.norm1, self.attn = nn.LayerNorm(dim), Attention(dim, heads)
        self.norm2, self.mlp = nn.LayerNorm(dim), Mlp(dim, int(dim * mlp_ratio), dim)
        self.ls1 = nn.Parameter(torch.full((dim,), float(init_values)))
        self.ls2 = nn.Parameter(torch.full((dim,), float(init_values)))

    def forward(self, x, key_mask=None):
        x = x + self.ls1 * self.attn(self.norm1(x), key_mask)
        return x + self.ls2 * self.mlp(self.norm2(x))


class CameraHead(nn.Module):
    """VGGT CameraHead: trunk over the 16 camera tokens, refined pose encodings [T3, quat4, fov2].

    With has_scale, a learned scale token joins the trunk and regresses log d-bar; with has_gravity,
    the group-0 (origin-group) trunk output regresses the origin camera's unit up vector."""

    def __init__(self, dim, depth=4, heads=16, has_gravity=False, has_scale=False, has_g3t_prior=False,
                 fov_activation=None):
        super().__init__()
        self.has_gravity = bool(has_gravity)
        self.has_scale = bool(has_scale)
        self.has_g3t_prior = bool(has_g3t_prior)
        if fov_activation not in (None, 'bounded_sigmoid_v1'):
            raise ValueError('Unknown FoV activation')
        self.fov_activation = fov_activation
        self.token_norm, self.trunk_norm = nn.LayerNorm(dim), nn.LayerNorm(dim)
        self.trunk = nn.Sequential(*[Block(dim, heads) for _ in range(depth)])
        self.empty_pose_tokens = nn.Parameter(torch.zeros(1, 1, TARGET_DIM))
        self.embed_pose = nn.Linear(TARGET_DIM, dim)
        self.pose_modulation = nn.Sequential(nn.SiLU(), nn.Linear(dim, 3 * dim))
        self.adaln_norm = nn.LayerNorm(dim, elementwise_affine=False, eps=1e-6)
        self.pose_branch = Mlp(dim, dim // 2, TARGET_DIM)
        if self.has_gravity:
            self.gravity_branch = Mlp(dim, dim // 2, 3)
        if self.has_scale:
            self.scale_token = nn.Parameter(torch.zeros(1, 1, dim))
            self.scale_branch = Mlp(dim, dim // 2, 1)
        if self.has_g3t_prior:
            self.alpha_pose = nn.Parameter(torch.zeros(1))
            self.alpha_grav = nn.Parameter(torch.zeros(1))
        else:
            self.register_parameter('alpha_pose', None)
            self.register_parameter('alpha_grav', None)

    def run_trunk(self, x, key_mask):
        if key_mask is None:
            return self.trunk(x)
        for block in self.trunk:
            x = block(x, key_mask)
        return x

    def activate_fov(self, value):
        if self.fov_activation == 'bounded_sigmoid_v1':
            # Keep finite FP32 outputs strictly inside the physical interval,
            # and supply a recovery gradient for ordinary negative logits.
            return 1e-4 + (math.pi - 2e-4) * torch.sigmoid(value)
        return F.relu(value)

    def forward_with_extras(self, tokens, iterations=4, key_mask=None,
                            g3t_pose_9d=None, g3t_gravity_up=None, g3t_step_scale=None,
                            return_fov_raw=False):
        tokens = self.token_norm(tokens)
        prediction, stages = None, []
        grav_pred, grav_stages = None, []
        scale_pred, scale_stages = None, []
        for _ in range(iterations):
            source = self.empty_pose_tokens.expand(tokens.shape[0], tokens.shape[1], -1) if prediction is None else prediction.detach()
            shift, scale, gate = self.pose_modulation(self.embed_pose(source)).chunk(3, dim=-1)
            modulated = gate * (self.adaln_norm(tokens) * (1 + scale) + shift) + tokens
            if self.has_scale:
                scale_tok = self.scale_token.expand(tokens.shape[0], 1, -1)
                scale_mask = None if key_mask is None else torch.cat((key_mask, key_mask.new_ones(key_mask.shape[0], 1)), 1)
                trunk_out = self.trunk_norm(self.run_trunk(torch.cat((modulated, scale_tok), dim=1), scale_mask))
                cam_trunk, scale_trunk = trunk_out[:, :-1, :], trunk_out[:, -1, :]
                delta_scale = self.scale_branch(scale_trunk).squeeze(-1)
                scale_pred = delta_scale if scale_pred is None else scale_pred + delta_scale
                scale_stages.append(scale_pred)
            else:
                cam_trunk = self.trunk_norm(self.run_trunk(modulated, key_mask))
            delta = self.pose_branch(cam_trunk)
            prediction = delta if prediction is None else prediction + delta
            # Legacy heads retain VGGT's ReLU; fresh heads may opt into bounded FoV.
            raw_stage = torch.cat((prediction[..., :7], self.activate_fov(prediction[..., 7:])), dim=-1)
            if g3t_pose_9d is not None:
                pose_prior = g3t_pose_9d.to(device=prediction.device, dtype=prediction.dtype)
                w_pose = (torch.tanh(self.alpha_pose).to(prediction.dtype)
                          if self.alpha_pose is not None else prediction.new_zeros(()))
                has_pose_prior = pose_prior[..., 3:7].norm(dim=-1, keepdim=True).amax(dim=1, keepdim=True) > 0.5
                if scale_pred is not None and g3t_step_scale is not None:
                    d_bar_m = torch.exp(scale_pred.clamp(-10.0, 10.0))[:, None, None].to(prediction.dtype)
                    step_s = g3t_step_scale.to(device=prediction.device, dtype=prediction.dtype).view(-1, 1, 1)
                    u_g3t = pose_prior[..., :3] / step_s.clamp_min(1e-4)
                    t_prior = d_bar_m * u_g3t
                    prior_rows = (step_s.view(-1) >= 0.0)[:, None, None] & has_pose_prior
                else:
                    t_prior = pose_prior[..., :3]
                    if g3t_step_scale is not None:
                        step_s = g3t_step_scale.to(device=prediction.device, dtype=prediction.dtype).view(-1, 1, 1)
                        prior_rows = (step_s.view(-1) >= 0.0)[:, None, None] & has_pose_prior
                    else:
                        prior_rows = has_pose_prior
                t_stage = t_prior + w_pose * prediction[..., :3]
                q_stage = canon_unit_quat(pose_prior[..., 3:7] + w_pose * prediction[..., 3:7], fallback=pose_prior[..., 3:7])
                fov_stage = F.relu(pose_prior[..., 7:9] + w_pose * prediction[..., 7:9])
                prior_stage = torch.cat((t_stage, q_stage, fov_stage), dim=-1).to(raw_stage.dtype)
                stages.append(torch.where(prior_rows, prior_stage, raw_stage))
            else:
                stages.append(raw_stage)
            if self.has_gravity:
                delta_grav = self.gravity_branch(cam_trunk[:, 0, :])
                grav_pred = delta_grav if grav_pred is None else grav_pred + delta_grav
                raw_grav = F.normalize(grav_pred, dim=-1, eps=1e-6)
                if g3t_gravity_up is not None:
                    grav_prior = g3t_gravity_up.to(device=grav_pred.device, dtype=grav_pred.dtype)
                    w_grav = (torch.tanh(self.alpha_grav).to(grav_pred.dtype)
                              if self.alpha_grav is not None else grav_pred.new_zeros(()))
                    prior_grav = F.normalize(grav_prior + w_grav * grav_pred, dim=-1, eps=1e-6).to(raw_grav.dtype)
                    grav_rows = grav_prior.norm(dim=-1, keepdim=True) > 0.5
                    if g3t_step_scale is not None:
                        step_ok = (g3t_step_scale.to(device=grav_pred.device).view(-1, 1) >= 0.0)
                        grav_rows = grav_rows & step_ok
                    grav_stages.append(torch.where(grav_rows, prior_grav, raw_grav))
                else:
                    grav_stages.append(raw_grav)
        if return_fov_raw:
            fov_raw = self.activate_fov(prediction[..., 7:9])
            return stages, grav_stages, scale_stages, fov_raw
        return stages, grav_stages, scale_stages

    def forward(self, tokens, iterations=4):
        return self.forward_with_extras(tokens, iterations=iterations)[0]


def initialize(module):
    """Cambrian-P's reconstructor init: trunc-normal Linear weights, zero biases, unit LayerNorms."""
    if isinstance(module, nn.Linear):
        nn.init.trunc_normal_(module.weight, std=0.02)
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    elif isinstance(module, nn.LayerNorm) and module.weight is not None:
        nn.init.ones_(module.weight)
        nn.init.zeros_(module.bias)


def scale_gradient(tensor, scale):
    """Identity in the forward pass; the backward pass multiplies the gradient by `scale` (0 detaches)."""
    if scale >= 1.0:
        return tensor
    if scale <= 0.0:
        return tensor.detach()
    return tensor.detach() + scale * (tensor - tensor.detach())


class CameraSupervision(nn.Module):
    def __init__(self, hidden_size, config, vit_dim=None):
        super().__init__()
        self.settings = normalize(config)
        self.has_gravity = bool(self.settings['weight_gravity'] > 0)
        self.has_scale = bool(self.settings['weight_scale'] > 0)
        prior = self.settings.get('g3t_prior') if g3t_prior_enabled(self.settings) else None
        self.has_g3t_prior = bool(prior is not None)
        dim = self.settings['embed_dim']
        # c_first and c_rest (Cambrian-P Eq. 1), initialized N(0, 1e-6) as in its reconstructor.
        self.tokens = nn.Parameter(torch.randn(2, hidden_size) * 1e-6)
        self.pose_reference = self.settings.get('pose_reference')
        self.spatial_pose = None
        if self.settings.get('pose_input') == 'spatial_tokens_v1':
            from .spatial_pose import SpatialPose
            self.spatial_pose = SpatialPose(hidden_size, dim)
        self.projector = nn.Linear(hidden_size * (2 if self.pose_reference else 1), dim)
        layers = self.settings['feature_layers']
        if layers is not None and len(layers) > 1:
            # Ablation only: softmax mix over the chosen layers' carrier states; zeros give a uniform mix at init.
            self.layer_logits = nn.Parameter(torch.zeros(len(layers)))
        else:
            self.register_parameter('layer_logits', None)
        self.head = CameraHead(dim, self.settings['trunk_depth'], self.settings['num_heads'],
                               has_gravity=self.has_gravity, has_scale=self.has_scale,
                               has_g3t_prior=bool(prior and prior.get('pose_prior')),
                               fov_activation=self.settings.get('fov_activation'))
        tokens = self.tokens.detach().clone()
        self.apply(initialize)
        if self.has_scale:
            nn.init.trunc_normal_(self.head.scale_token, std=0.02)
        with torch.no_grad():
            self.tokens.copy_(tokens)
        if prior and prior.get('carrier_connector'):
            # The zero-output graft must not perturb subsequent CP1 head init.
            with torch.random.fork_rng(devices=[], enabled=prior.get('connector_out_init') == 'zero'):
                self.cam_token_connector = GatedCameraTokenConnector(
                    prior['cam_token_dim'], hidden_size, out_init=prior.get('connector_out_init', 'tanh_gate'))
        else:
            self.cam_token_connector = None
        if prior and prior.get('head_bypass'):
            self.cam_head_bypass = GatedCameraHeadBypass(prior['cam_token_dim'], dim)
        else:
            self.cam_head_bypass = None
        if point_depth_enabled(self.settings['point_depth']):
            self.point_depth = PointDepthHead(hidden_size, self.settings['point_depth'], vit_dim=vit_dim)
        else:
            self.point_depth = None
        for name in self.settings.get('freeze_modules', []):
            if name == 'geometry':  # The trainer freezes the separately attached, pinned projector.
                continue
            module = getattr(self, name)
            if module is None:
                raise ValueError('Camera freeze_modules names a module that is not attached: ' + name)
            module.requires_grad_(False)
        # Scale on the head losses' gradient into the student (head-only warmup); set per optimizer step.
        self.backbone_scale = 1.0
        self.last_components = {}

    @property
    def mixes_layers(self):
        return self.layer_logits is not None

    def carrier_states(self, hidden, positions, layer_states=None):
        """[B, 16, H] carrier states the head reads: final-norm states, or the configured layer mix."""
        layers = self.settings['feature_layers']
        if layers is None:
            return gather_positions(hidden, positions)
        if layer_states is None:
            raise ValueError('Camera feature layers were configured but not captured')
        return self.mix(layer_states)

    def embedding_hook(self, output, positions, g3t_cam_tokens=None, g3t_step_scale=None):
        """Replace carrier positions in `output` [B, L, H] with c_first/c_rest plus optional G3T camera-token delta."""
        rows, slots = torch.nonzero(positions >= 0, as_tuple=True)
        if not rows.numel():
            return output
        columns = positions[rows, slots]
        chosen = self.tokens[(slots > 0).long()].to(output.dtype)
        if self.cam_token_connector is not None and g3t_cam_tokens is not None:
            cam_in = g3t_cam_tokens[rows, slots].to(device=output.device, dtype=torch.float32)
            delta = self.cam_token_connector(cam_in).to(output.dtype)
            if g3t_step_scale is not None:
                valid = (g3t_step_scale.to(device=output.device)[rows].view(-1) >= 0.0)[:, None]
                delta = torch.where(valid, delta, torch.zeros_like(delta))
            chosen = chosen + delta
        return output.index_put((rows, columns), chosen)

    def predict_all(self, states, key_mask=None, g3t_cam_tokens=None,
                    g3t_pose_9d=None, g3t_gravity_up=None, g3t_step_scale=None,
                    return_fov_raw=False, spatial_grids=None, frame_queries=None):
        pose_states = states.float()
        if self.spatial_pose is not None:
            groups = states.shape[1]
            spatial_mask = key_mask
            if frame_queries is not None:
                if groups % 2 or frame_queries.shape != states.shape[1:]:
                    raise ValueError('Spatial frame queries must match the per-frame positions')
                groups //= 2
                spatial_mask = None if key_mask is None else key_mask.reshape(-1, groups, 2).any(-1)
            pose_states = self.spatial_pose(spatial_grids, groups, spatial_mask)
            if frame_queries is not None:
                # Each fused RGB group supplies both frames; learned queries distinguish them.
                pose_states = pose_states.repeat_interleave(2, dim=1) + frame_queries.float()[None]
        if pose_states.shape != states.shape:
            raise ValueError('Spatial pose batch or channel shape differs')
        if self.pose_reference == 'first_group_concat_v1':
            # The first fused pair contains the origin frame. A bidirectional
            # trunk over unmarked ViT groups cannot identify it from order alone.
            pose_states = torch.cat((pose_states, pose_states[:, :1].expand_as(pose_states)), dim=-1)
        if getattr(self, 'projector_fp32', False):
            # C1-r teacher-space projector (c1r_align.attach): FP32 even under autocast.
            with torch.autocast(device_type=pose_states.device.type, enabled=False):
                projected = self.projector(pose_states.float())
        else:
            projected = self.projector(pose_states)
        if self.cam_head_bypass is not None and g3t_cam_tokens is not None:
            bypass_in = g3t_cam_tokens.to(device=projected.device, dtype=projected.dtype)
            bypass_delta = self.cam_head_bypass(bypass_in).to(projected.dtype)
            if g3t_step_scale is not None:
                valid_rows = (g3t_step_scale.to(device=projected.device).view(-1) >= 0.0)[:, None, None]
                bypass_delta = torch.where(valid_rows, bypass_delta, torch.zeros_like(bypass_delta))
            projected = projected + bypass_delta
        if not self.head.has_g3t_prior:
            g3t_pose_9d = None
            g3t_gravity_up = None
        return self.head.forward_with_extras(
            projected, self.settings['refine_iterations'], key_mask,
            g3t_pose_9d=g3t_pose_9d, g3t_gravity_up=g3t_gravity_up, g3t_step_scale=g3t_step_scale,
            return_fov_raw=return_fov_raw,
        )

    def predict(self, states, g3t_cam_tokens=None, g3t_pose_9d=None, g3t_gravity_up=None, g3t_step_scale=None,
                spatial_grids=None, frame_queries=None):
        return self.predict_all(states, g3t_cam_tokens=g3t_cam_tokens,
                                g3t_pose_9d=g3t_pose_9d, g3t_gravity_up=g3t_gravity_up,
                                g3t_step_scale=g3t_step_scale, spatial_grids=spatial_grids,
                                frame_queries=frame_queries)[0]

    def mix(self, layer_states):
        """Weighted sum of the feature layers' carrier states [B,16,H] with softmax(layer_logits)."""
        layers = self.settings['feature_layers']
        missing = [k for k in layers if k not in layer_states]
        if missing:
            raise ValueError(f'Camera feature layers were not captured: {missing}')
        if self.layer_logits is None:
            return layer_states[layers[0]].float()
        stacked = torch.stack([layer_states[k].float() for k in layers])
        return torch.einsum('l,lbsh->bsh', self.layer_logits.softmax(dim=0), stacked)

    def loss(self, hidden, targets, layer_states=None, visual_grids=None, vit_grids=None,
             frame_queries=None):
        """Per-row weighted camera loss [B]; rows without carriers contribute zero but keep every parameter in the graph.

        visual_grids: per row [16, Hm, Wm, H] final-norm states at the row's visual tokens.
        vit_grids: per row three [16, 2Hm, 2Wm, D_vit] ViT block outputs in raster order."""
        positions = targets['aux_camera_positions']
        target, mask, scale = targets['aux_camera_target'].float(), targets['aux_camera_mask'], targets['aux_camera_scale'].float()
        batch = hidden.shape[0]
        groups = positions.shape[1] if positions.ndim == 2 else 0
        if (not 16 <= groups <= self.settings.get('max_groups', 16)
                or positions.shape != (batch, groups) or mask.shape != (batch, groups) or target.shape != (batch, groups, TARGET_DIM)
                or scale.shape != (batch,)):
            raise ValueError('Camera target shape mismatch')
        # A row has camera tokens for its first G groups (G = 16 for 32-frame rows; G = N / 2 for an N-frame
        # pose-only sample) and -1 after them, or none at all.
        valid = positions >= 0
        present = valid[:, 0]
        if (torch.any(valid != (valid.long().cumprod(dim=1) > 0)) or torch.any(mask & ~valid)
                or torch.any(mask.any(dim=1) & ~present)):
            raise ValueError('Camera rows need a prefix of token positions (all 16 for a 32-frame row) or none')
        visible = valid | ~present[:, None]
        key_mask = None if bool(visible.all()) else visible
        if present.any():
            states = scale_gradient(self.carrier_states(hidden, positions, layer_states), self.backbone_scale)
        else:
            # No camera row in this micro-batch: a zero-weighted pass keeps DDP/FSDP gradients defined.
            states = self.tokens[[0] + [1] * (groups - 1)].float()[None].expand(batch, -1, -1)
            if self.layer_logits is not None:
                states = states + self.layer_logits.sum() * 0.0
        g3t_cam_tokens = targets.get('aux_g3t_cam_tokens')
        g3t_pose_9d = targets.get('aux_g3t_pose_9d') if self.head.has_g3t_prior else None
        g3t_gravity_up = targets.get('aux_g3t_gravity_up') if self.head.has_g3t_prior else None
        g3t_step_scale = targets.get('aux_g3t_step_scale')
        spatial = None
        if self.spatial_pose is not None:
            if vit_grids is None or len(vit_grids) != batch:
                raise ValueError('Spatial pose requires per-row captured ViT grids')
            spatial = [scale_gradient(row[-1][::2] if frame_queries is not None else row[-1],
                                      self.backbone_scale) for row in vit_grids]
        stages, grav_stages, scale_stages, fov_raw = self.predict_all(
            states, key_mask,
            g3t_cam_tokens=g3t_cam_tokens,
            g3t_pose_9d=g3t_pose_9d,
            g3t_gravity_up=g3t_gravity_up,
            g3t_step_scale=g3t_step_scale,
            return_fov_raw=True,
            spatial_grids=spatial,
            frame_queries=None if frame_queries is None else scale_gradient(frame_queries, self.backbone_scale),
        )
        mask = mask & present[:, None]
        balance = scale.clamp_min(self.settings['min_trajectory_scale_m']) if self.settings['trajectory_balance'] else torch.ones_like(scale)
        count = len(stages)
        weights = [self.settings['stage_gamma'] ** (count - index - 1) for index in range(count)]
        pose = sum(w * self.stage_loss(p, target, mask, balance) for w, p in zip(weights, stages)) / count
        pose = torch.where(mask.any(dim=1), pose, pose * 0)
        total = self.settings['weight'] * pose
        components = {'pose': pose.detach(), **self._stage_terms}

        if self.has_gravity:
            if 'aux_gravity_target' not in targets or 'aux_gravity_mask' not in targets:
                raise ValueError('The gravity branch requires gravity targets for every camera row')
            grav_target = targets['aux_gravity_target'].float()
            grav_mask = targets['aux_gravity_mask'].bool() & present
            gravity = sum(w * self.gravity_stage_loss(g, grav_target, grav_mask) for w, g in zip(weights, grav_stages)) / count
            gravity = torch.where(grav_mask, gravity, gravity * 0)
            total = total + self.settings['weight_gravity'] * gravity
            components['gravity'] = gravity.detach()

        if self.has_scale:
            scale_mask = mask.any(dim=1) & (scale > 0)
            scale_loss = sum(w * self.scale_stage_loss(s, scale, scale_mask) for w, s in zip(weights, scale_stages)) / count
            scale_loss = torch.where(scale_mask, scale_loss, scale_loss * 0)
            total = total + self.settings['weight_scale'] * scale_loss
            components['scale'] = scale_loss.detach()

        if self.point_depth is not None:
            depth = self.depth_loss(targets, present, stages[-1], visual_grids, vit_grids, batch, fov_override=fov_raw)
            total = total + self.point_depth.settings['weight'] * depth
            components['point_depth'] = depth.detach()

        extra_touch = total.new_zeros(())
        for mod in (self.cam_token_connector, self.cam_head_bypass):
            if mod is not None:
                extra_touch = extra_touch + sum(p.sum() for p in mod.parameters()) * 0.0
        for param in (self.head.alpha_pose, self.head.alpha_grav):
            if param is not None:
                extra_touch = extra_touch + param.sum() * 0.0
        self.last_components = components
        return torch.where(present, total, total * 0) + extra_touch

    def depth_loss(self, targets, present, last_pose, visual_grids, vit_grids, batch, fov_override=None):
        """Per-row point-depth loss [B]. The head runs only on rows with depth labels."""
        keys = ('aux_point_depth_uv', 'aux_point_depth_gt', 'aux_point_depth_mask')
        if any(key not in targets for key in keys):
            raise ValueError('The point-depth head requires point-depth targets for every camera row')
        uv, gt, depth_mask = (targets[key] for key in keys)
        if uv.ndim != 4 or uv.shape[:2] != last_pose.shape[:2] or gt.shape != uv.shape[:3] or depth_mask.shape != gt.shape:
            raise ValueError('Point-depth target shape mismatch')
        labelled = depth_mask.bool().any(dim=(1, 2))
        if torch.any(labelled & ~present):
            raise ValueError('A depth-supervised row lacks its camera tokens')
        # The pose head's predicted field of view conditions the depth head, in training as at inference.
        raw_fov = fov_override if fov_override is not None else last_pose[..., 7:9]
        fov = raw_fov.detach().clamp(0.1, math.pi - 0.1)
        result = [last_pose.new_zeros(())] * batch
        if labelled.any():
            if visual_grids is None or vit_grids is None or len(visual_grids) != batch or len(vit_grids) != batch:
                raise ValueError('The point-depth head requires per-row visual and ViT grids')
            for row in torch.nonzero(labelled).flatten().tolist():
                # A 32-frame row has 16 temporal groups; an N-frame pose-only sample has N / 2, its later slots unlabelled.
                groups = visual_grids[row].shape[0]
                if not 1 <= groups <= self.settings.get('max_groups', 16) or bool(depth_mask[row, groups:].any()):
                    raise ValueError("Point-depth labels beyond the row's temporal groups")
                llm = scale_gradient(visual_grids[row], self.backbone_scale)
                vit = [scale_gradient(grid, self.backbone_scale) for grid in vit_grids[row]]
                prediction = self.point_depth(llm, vit, fov[row, :groups], uv[row, :groups].float())
                result[row] = self.point_depth.row_loss(prediction, gt[row, :groups].float(), depth_mask[row, :groups].bool())
        touch = sum(p.sum() for p in self.point_depth.parameters()) * 0.0
        return torch.stack(result) + touch

    def gravity_stage_loss(self, pred_grav, target_grav, grav_mask):
        safe_target = torch.where(grav_mask[:, None], target_grav, pred_grav.detach())
        l1 = (pred_grav - safe_target).abs().mean(dim=-1)
        cos = 1.0 - (pred_grav * safe_target).sum(dim=-1).clamp(-1.0, 1.0)
        loss = (l1 + cos).clamp(max=self.settings['loss_clamp'])
        return torch.where(grav_mask, loss, loss * 0.0)

    def scale_stage_loss(self, pred_log_scale, target_scale, scale_mask):
        """L1 on log d-bar (the trajectory's mean step between consecutive anchor frames, metres)."""
        min_s = self.settings['min_trajectory_scale_m']
        safe_target = torch.where(scale_mask, torch.log(target_scale.clamp_min(min_s)), pred_log_scale.detach())
        err = (pred_log_scale - safe_target).abs().clamp(max=self.settings['loss_clamp'])
        return torch.where(scale_mask, err, err * 0.0)

    def stage_loss(self, prediction, target, mask, balance):
        reduce = (lambda x: x.mean(dim=-1)) if self.settings['component_reduction'] == 'mean' else (lambda x: x.sum(dim=-1))
        clamp = self.settings['loss_clamp']
        # Mask before arithmetic so masked groups carry no gradient.
        target = torch.where(mask[..., None], target, prediction.detach())
        error = (prediction - target).abs()
        trans = reduce((error[..., :3] / balance[:, None, None]).clamp(max=clamp))
        rot = reduce(error[..., 3:7].clamp(max=clamp))
        focal = reduce(error[..., 7:].clamp(max=clamp))
        per_group = (self.settings['weight_trans'] * trans + self.settings['weight_rot'] * rot
                     + self.settings['weight_focal'] * focal)
        per_group = torch.where(mask, per_group, torch.zeros_like(per_group))
        denom = mask.sum(dim=1).clamp_min(1)
        # Logging only: this stage's unweighted translation, rotation and FoV terms per row (the last
        # call of a loss() is its final stage).
        self._stage_terms = {k: (torch.where(mask, v, torch.zeros_like(v)).sum(dim=1) / denom).detach()
                             for k, v in (('trans', trans), ('rot', rot), ('fov', focal))}
        return per_group.sum(dim=1) / denom


def gather_positions(hidden, positions):
    """States [B,16,H] at the carrier positions; rows without carriers read position 0 (masked later)."""
    rows = torch.arange(hidden.shape[0], device=hidden.device)[:, None]
    return hidden[rows, positions.clamp_min(0)]


def decoder_layers(module):
    """Zero-based decoder-layer index -> module, preferring the inner module under FSDP wrapping."""
    import re

    found = {}
    for name, child in module.named_modules():
        match = re.search(r'language_model\.layers\.(\d+)(\._fsdp_wrapped_module)?$', name)
        if match and (match.group(2) or int(match.group(1)) not in found):
            found[int(match.group(1))] = child
    return found


def layer_hooks(module, supervision, final_layer, store):
    """Forward hooks that keep each chosen decoder layer's output from the first forward call.

    A hook runs inside its layer's gradient-checkpoint region, and the recomputation in backward
    must save exactly the tensors the first pass saved. The hook therefore only keeps a reference
    (no operation); the carrier gather happens later, outside every checkpointed layer. The kept
    output is the next layer's checkpoint input anyway, so it costs no extra memory."""
    layers = decoder_layers(module)
    handles = []
    for k in supervision.settings['feature_layers'] or []:
        if k == final_layer:
            continue
        if k - 1 not in layers:
            raise ValueError(f'Camera feature layer {k} has no decoder layer')

        def hook(layer, args, output, k=k):
            if k not in store:
                store[k] = output[0] if isinstance(output, tuple) else output
        handles.append(layers[k - 1].register_forward_hook(hook))
    return handles


def embedding_hook(supervision, batch, carrier):
    """Forward hook for the input embeddings: carrier positions take c_first (group 0) or c_rest
    plus the optional gated G3T camera-token connector delta."""
    positions = batch['aux_camera_positions']
    g3t_cam_tokens = batch.get('aux_g3t_cam_tokens')
    g3t_step_scale = batch.get('aux_g3t_step_scale')

    def hook(module, args, output):
        rows, slots = torch.nonzero(positions >= 0, as_tuple=True)
        if not rows.numel():
            return output
        columns = positions[rows, slots]
        if torch.any(args[0][rows, columns] != carrier):
            raise ValueError('Camera token positions do not hold the carrier token')
        chosen = supervision.tokens[(slots > 0).long()].to(output.dtype)
        if supervision.cam_token_connector is not None and g3t_cam_tokens is not None:
            cam_in = g3t_cam_tokens[rows, slots].to(device=output.device, dtype=torch.float32)
            delta = supervision.cam_token_connector(cam_in).to(output.dtype)
            if g3t_step_scale is not None:
                valid = (g3t_step_scale[rows].to(device=output.device).view(-1) >= 0.0)[:, None]
                delta = torch.where(valid, delta, delta * 0.0)
            chosen = chosen + delta
        return output.index_put((rows, columns), chosen)
    return hook
