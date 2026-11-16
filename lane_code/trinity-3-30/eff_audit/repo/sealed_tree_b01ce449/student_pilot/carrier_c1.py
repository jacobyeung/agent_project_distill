"""C1: native final-layer camera carriers, full LM training, private V-C depth.

The base vision tower stays frozen. No LM state enters the depth branch and no
private-encoder feature enters the pose branch. Both branches start from base.
"""
import copy
from contextlib import ExitStack
import math
import time

import torch
from torch import nn
from torch.nn import functional as F

from .camera_head import CameraSupervision
from .decoupled_v import features
from .point_depth_head import PointDepthHead
from . import full_ft
from .carrier_c1_data import C1_A, C1_B, C1_C, PLACEMENTS, frame_position_ids, standard_attention_mask


RECIPE = dict(steps=800, global_batch=32, world_size=8, seed=17,
              learning_rate=1e-4, lm_learning_rate=1e-5, encoder_learning_rate=1e-5,
              weight_decay=.01, warmup_ratio=.03, clip_norm=1.,
              resume_every_seconds=1800, milestones=[100, 200, 400, 800],
              mix=['pose', 'pose', 'vqa', 'pointing'],
              weights=dict(pose=1., depth=.05, depth_fov=.05, vqa=1., pointing=1.),
              wall_seconds=14400, stop_before_seconds=900)

def camera_settings(source):
    """Use the CPDM carrier path, not A1's spatial/origin-concat projector."""
    settings = {k: v for k, v in source.items() if k not in
                ('pose_input', 'pose_reference', 'g3t_prior', 'freeze_modules', 'row_routing')}
    return {**settings, 'weight': 1., 'feature_layers': None, 'point_depth': None,
            'trunk_depth': 4, 'max_groups': 32, 'head_only_steps': 0,
            'gate': None, 'lm_gate': None, 'fov_activation': 'bounded_sigmoid_v1'}


class PrivateDepth(nn.Module):
    """V-C native BF16 feature computation with FP32 trainable master tensors."""
    def __init__(self, config, visual, depth_settings):
        super().__init__()
        self.config = copy.deepcopy(config)
        self.config.p3 = dict(feature_backing='decoupled_vc', anchors=list(range(1, 33)),
                              temporal_grouping='fused_pairs_all_frames')
        self.model = nn.Module()
        self.model.visual = copy.deepcopy(visual).float().requires_grad_(True)
        # V-C reads block outputs before the merger; the merger is not trained.
        self.model.visual.merger.requires_grad_(False)
        self.auxiliary_heads = nn.Module()
        self.auxiliary_heads.backing = 'decoupled_vc'
        self.auxiliary_heads.camera = nn.Module()
        dim = config.vision_config.hidden_size
        head = PointDepthHead(dim, depth_settings, vit_dim=dim)
        head.group_embed = nn.Parameter(torch.zeros(32, head.group_embed.shape[1]))
        self.auxiliary_heads.camera.point_depth = head
        self.auxiliary_heads.frame_queries = nn.Parameter(torch.zeros(32, dim))
        self.fov = nn.Linear(dim, 2)
        self.gradient_checkpointing = True

    def forward(self, batch, targets=None, uv=None, fov=None):
        """`fov` [1, n, 2] (pose head slots 7:9) replaces the private FoV as the one
        conditioning FoV; the private FoV branch then trains nothing."""
        captured = features(self, batch, allow_short=True)
        states = captured.states.float()
        conditioning = fov
        fov = 1e-4 + (math.pi - 2e-4) * self.fov(states).sigmoid()
        n = states.shape[1]
        if uv is None:
            uv = torch.where(targets['aux_point_depth_mask'][:, :n, :, None].bool(),
                             targets['aux_point_depth_uv'][:, :n], 0.)
        if conditioning is not None and conditioning.shape != fov.shape:
            raise ValueError('Pose-head FoV must give one (vertical, horizontal) pair per depth slot')
        head = self.auxiliary_heads.camera.point_depth
        prediction = head(captured.grids[0], captured.vits[0],
                          (fov if conditioning is None else conditioning)[0].float().detach(), uv[0].float())
        if targets is None:
            return prediction, fov
        mask = targets['aux_point_depth_mask'][0]
        if mask[n:].any():
            raise ValueError('Depth supervision exceeds visible frames')
        labels = targets['aux_point_depth_gt'][0, :n].float()
        if not (mask[:n].bool() & torch.isfinite(labels) & (labels >= head.min_depth_m)
                & (labels <= head.max_depth_m)).any():
            # Rank-aligned final mode runs depth on every pose row; unlabelled rows add a zero term.
            self.last_absrel = None
            zero = prediction.float().sum() * 0.
            return zero, zero
        depth = head.row_loss(prediction, labels, mask[:n])
        with torch.no_grad():
            gt = targets['aux_point_depth_gt'][0, :n].float()
            valid = mask[:n] & (gt > 0)
            self.last_absrel = float(((prediction.float() - gt).abs() / gt.clamp_min(1e-6))[valid].mean()) \
                if valid.any() else None
        if conditioning is not None:
            return depth, depth * 0.
        valid = targets['aux_camera_mask'][:, :n]
        gt = targets['aux_camera_target'][:, :n, 7:9]
        safe = torch.where(valid[..., None], gt, fov.detach())
        fov_loss = ((fov - safe).abs().mean(-1) * valid).sum() / valid.sum().clamp_min(1)
        return depth, fov_loss


class CarrierC1(nn.Module):
    """Keep native parameter names so full_ft's reviewed FSDP/shard tools apply."""
    def __init__(self, base, camera, depth, carrier_id, carrier_placement=C1_A,
                 training_mode='mixed', depth_enabled=True, recipe=None,
                 skip_unsupervised_lm=None, frame_layout='spread', depth_fov_source='private',
                 geometry_online=None, geometry_runtime=None):
        super().__init__()
        if carrier_placement not in PLACEMENTS or training_mode not in ('mixed', 'pose_only', 'final'):
            raise ValueError('Unknown C1 placement or training mode')
        if depth_fov_source not in ('private', 'pose_head'):
            raise ValueError('depth_fov_source must be private or pose_head')
        self.depth_fov_source = depth_fov_source
        self.carrier_placement, self.training_mode = carrier_placement, training_mode
        self.skip_unsupervised_lm = False if skip_unsupervised_lm is None else skip_unsupervised_lm
        if frame_layout not in ('spread', 'duplicate', 'paired'):
            raise ValueError('Unknown frame_layout')
        self.frame_layout = frame_layout
        self.geometry_online = None
        self.gx_zero_feature = False
        self.gx_metrics = {}
        if geometry_online is not None:
            from . import g3t_online
            self.geometry_online = g3t_online.normalize(geometry_online)
            g3t_online.validate_arm(self.geometry_online, training_mode, frame_layout, depth_enabled)
            if geometry_runtime is None or set(geometry_runtime) != {'image_mean', 'image_std'}:
                raise ValueError('GX requires processor video statistics')
            self.geometry_runtime = copy.deepcopy(geometry_runtime)
        self.carrier_position_policy = 'frame_grid_anchor_v2' if carrier_placement == C1_B else 'native_v1'
        self.recipe = RECIPE if recipe is None else recipe
        block = full_ft.normalize(
            {'train': dict(llm=False, vision_blocks=False, merger=False)}
            if self.geometry_online and self.geometry_online.get('gf1', {}).get('stage') == 1
            else {'learning_rates': {'llm': RECIPE['lm_learning_rate']}})
        _, self.full_ft_report = full_ft.prepare_model(base, block)
        self.config, self.model, self.lm_head = base.config, base.model, base.lm_head
        self.carrier_id = carrier_id
        self.auxiliary_heads = nn.Module()
        settings = camera_settings(camera)
        if self.geometry_online is not None:
            from .rehearsal import feature_width
            geometry_width = feature_width(self.geometry_online)
            settings['g3t_prior'] = dict(enabled=True, cam_token_dim=geometry_width + 10, carrier_connector=True,
                head_bypass=False, pose_prior=False, connector_out_init='zero')
        if training_mode == 'pose_only':
            settings.update(weight_gravity=0., weight_scale=0.)
        if training_mode == 'final':
            # Routed direction/route/camera programs need gravity (SELF_ROUTING_DESIGN 1.1).
            settings.update(weight_gravity=1.)
        self.auxiliary_heads.pose = CameraSupervision(self.config.text_config.hidden_size, settings).float()
        if self.geometry_online is not None:
            with torch.random.fork_rng(devices=[]):
                self.auxiliary_heads.geometry_encoder = g3t_online.G3TEncoder(self.geometry_online)
                if 'patch_fusion' in self.geometry_online:
                    self.auxiliary_heads.patch_fusion = g3t_online.PatchFusion(
                        self.config.vision_config.out_hidden_size, self.geometry_online['patch_fusion']['hidden']).float()
        if self.geometry_online is not None and 'gf1' in self.geometry_online:
            from .gf1 import Fusion, install_decoder_hooks
            self.auxiliary_heads.gf1 = Fusion(self.config.vision_config.out_hidden_size, self.geometry_online['gf1'],
                                              input_dim=geometry_width)
            if self.geometry_online['gf1']['injection'] == 'lm_012':
                install_decoder_hooks(self)
        if carrier_placement == C1_B:
            self.auxiliary_heads.frame_embeddings = nn.Embedding(32, self.config.text_config.hidden_size)
            # Initialize frame identity as a small perturbation. Pair it with
            # frame-grid M-RoPE coordinates; either change alone failed the
            # permanent 200-step carrier learning guard.
            nn.init.normal_(self.auxiliary_heads.frame_embeddings.weight, std=1e-4)
        if depth_enabled:
            self.auxiliary_heads.depth = PrivateDepth(self.config, self.model.visual, depth).float()
            self.auxiliary_heads.depth.config.p3['frame_layout'] = frame_layout
        # The mask travels in checkpointed kwargs. No global/temporary mask state
        # survives a call, and backward recomputation uses that forward's mask.
        if carrier_placement == C1_C:
            # This hook supplies a 4D boolean allow-mask. Eager interprets it
            # as an additive bias; flash/flex interfaces require other mask
            # formats. Pin the native text model too, so cached decoding builds
            # masks for the same backend. Vision and causal DeltaNet stay native.
            self.model.language_model.set_attn_implementation('sdpa')
            for layer in self.model.language_model.layers:
                if layer.layer_type == 'full_attention':
                    layer.self_attn.register_forward_pre_hook(self._attention_mask, with_kwargs=True)
        self.model.visual.eval()
        self.model.language_model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={'use_reentrant': False})
        if self.geometry_online and 'gf1' in self.geometry_online:
            from .gf1 import configure_trainables
            configure_trainables(self)

    def get_input_embeddings(self):
        return self.model.get_input_embeddings()

    def get_output_embeddings(self):
        return self.lm_head

    @staticmethod
    def _attention_mask(module, args, kwargs):
        mask = kwargs.pop('c1_prefix_mask', None)
        if mask is not None:
            kwargs['attention_mask'] = mask
        return args, kwargs

    def geometry_features(self, batch, _camera_only=False):
        """Compute online geometry from the configured view of each video's viewpoints."""
        if self.geometry_online is None:
            return None
        if 'image_grid_thw' in batch and 'video_grid_thw' not in batch:
            # CP1 image-only rows have no temporal carriers. Retain their native
            # image tower path; a 32-view geometry prior is undefined here.
            self.gx_metrics = dict(single_image_fusion_skipped=True)
            return None
        if 'gf1' in self.geometry_online and not _camera_only:
            from .gf1 import geometry_features
            return geometry_features(self, batch)
        active = None
        if 'patch_fusion' not in self.geometry_online:
            positions = batch.get('aux_camera_positions')
            if positions is None or not (positions >= 0).any():
                self.gx_metrics = dict(no_carriers_geometry_skipped=True)
                return None
            active = (positions >= 0).any(dim=1)
        from . import g3t_online
        started = time.perf_counter()
        encoder = self.auxiliary_heads.geometry_encoder
        if ('patch_fusion' in self.geometry_online and
                batch['video_grid_thw'].shape != (batch['input_ids'].shape[0], 3)):
            raise ValueError('GX patch fusion requires one video grid per batch row')
        if self.geometry_online['input'] == g3t_online.NATIVE_INPUT:
            if 'aux_g3t_images' not in batch or 'aux_g3t_coords' not in batch:
                raise ValueError('Native GX requires aux_g3t_images and aux_g3t_coords')
            images, coords = batch['aux_g3t_images'], batch['aux_g3t_coords']
            rows = batch['input_ids'].shape[0]
            if images.shape != (rows, 32, 3, 518, 518) or coords.shape != (rows, 32, 4):
                raise ValueError('Native GX requires one 32-viewpoint clip per batch row')
            device = next(encoder.parameters()).device
            clips = zip(images.to(device=device, dtype=torch.float32), coords.to(device=device, dtype=torch.float32))
        else:
            frames = g3t_online.student_frames(batch['pixel_values_videos'], batch['video_grid_thw'],
                                              self.config.vision_config, **self.geometry_runtime)
            if len(frames) != batch['input_ids'].shape[0]:
                raise ValueError('GX requires one video per batch row')
            clips = (g3t_online.square_518(f, encoder.image_size) for f in frames)
        values, patches = [], []
        for i, (images, coords) in enumerate(clips):
            if active is not None and not active[i]:
                continue
            value = g3t_online.features(encoder, images, coords)
            if _camera_only:
                value = value[0]
            if 'patch_fusion' in self.geometry_online:
                value, patch = value
                if self.geometry_online['patch_fusion'].get('checkpointing', False):
                    patches.append((torch.zeros_like(patch) if self.gx_zero_feature else patch,
                                    coords, batch['video_grid_thw'][i]))
                else:
                    patches.append(g3t_online.pool_patch_features(patch, coords, batch['video_grid_thw'][i]))
            values.append(value)
        values = torch.stack(values)
        if active is not None:
            # Preserve the original batch indices for carrier lookup, while only
            # encoding clips whose rows contain CAM slots.
            values = values.new_zeros((len(active), *values.shape[1:])).index_copy(
                0, active.nonzero(as_tuple=True)[0].to(values.device), values)
        if self.gx_zero_feature:
            values = torch.zeros_like(values)
        self.gx_metrics = dict(feature_rms=float(values.detach().square().mean().sqrt()),
                              feature_finite=bool(torch.isfinite(values).all()),
                              g3t_seconds=time.perf_counter()-started,
                              rms_cam=float(self.auxiliary_heads.pose.cam_token_connector.rms_cam.item()))
        if getattr(encoder, 'parity', None) is not None and not getattr(self, 'gx_parity_logged', False):
            # The once-per-process lean-vs-native G3T check rides along with the first step's metrics.
            self.gx_metrics['parity'], self.gx_parity_logged = encoder.parity, True
        if patches:
            if self.geometry_online['patch_fusion'].get('checkpointing', False):
                return values, patches
            patches = torch.cat(patches)
            return values, torch.zeros_like(patches) if self.gx_zero_feature else patches
        return values

    def patch_injection(self, stack, batch, geometry):
        """Install this forward's patch hook and return the CAM features."""
        if geometry is not None and self.geometry_online is not None and 'gf1' in self.geometry_online:
            cameras, clips = geometry
            stack.enter_context(self.auxiliary_heads.gf1.inject(self, clips, batch, self.gx_metrics))
            return cameras
        if geometry is not None and self.geometry_online is not None and 'patch_fusion' in self.geometry_online:
            geometry, patches = geometry
            stack.enter_context(self.auxiliary_heads.patch_fusion.inject(
                self.model.visual, patches, batch['video_grid_thw'], self.gx_metrics,
                **({'checkpointing': True} if self.geometry_online['patch_fusion'].get('checkpointing', False) else {})))
        return geometry

    def carrier_embeddings(self, output, positions, g3t=None):
        pose = self.auxiliary_heads.pose
        if g3t is not None:
            with torch.no_grad():
                rows, slots = torch.nonzero(positions >= 0, as_tuple=True)
                delta = pose.cam_token_connector(g3t[rows, slots].detach().float()).to(output.dtype).float()
                carrier = pose.tokens[(slots > 0).long()].to(output.dtype).float()
                if self.carrier_placement == C1_B:
                    carrier = (carrier.to(output.dtype) +
                               self.auxiliary_heads.frame_embeddings.weight[slots].to(output.dtype)).float()
                self.gx_metrics['delta_ratio'] = float(delta.square().mean().sqrt() /
                                                      carrier.square().mean().sqrt().clamp_min(1e-12))
        output = pose.embedding_hook(output, positions, g3t_cam_tokens=g3t)
        if self.carrier_placement == C1_B:
            output = output.clone()
            for row, pos in enumerate(positions):
                valid = pos >= 0
                output[row, pos[valid]] += self.auxiliary_heads.frame_embeddings.weight[valid].to(output.dtype)
        return output

    def check_placement(self, batch):
        value = batch.get('aux_carrier_placement')
        if value is None or not (value == PLACEMENTS.index(self.carrier_placement)).all():
            raise ValueError('Batch carrier_placement differs from the model')
        layout = batch.get('aux_frame_layout', 0)
        if not torch.as_tensor(layout == ('spread', 'duplicate', 'paired').index(self.frame_layout)).all():
            raise ValueError('Batch frame_layout differs from the model')

    def train(self, mode=True):
        super().train(mode)
        self.model.visual.eval()
        if self.geometry_online is not None:
            self.auxiliary_heads.geometry_encoder.eval()
        return self

    @torch.no_grad()
    def generate(self, batch, **kwargs):
        """Native greedy/sampling harness adapter with C1's prefix embeddings.

        Construct only a meta wrapper; reuse every loaded tensor. Install the
        carrier hook for prefill only, then let native KV/recurrent caching run.
        The caller supplies a prompt-only batch from insert_frame_carriers.
        """
        if self.training:
            raise ValueError('C1 generation requires eval mode')
        carriers = 'video_grid_thw' in batch
        if carriers:
            self.check_placement(batch)
        geometry = self.geometry_features(batch)
        from transformers import Qwen3_5ForConditionalGeneration
        with torch.device('meta'):
            native=Qwen3_5ForConditionalGeneration(self.config)
        native.model,native.lm_head=self.model,self.lm_head
        positions=batch.get('aux_camera_positions'); seen=[False]
        def replace(module,args,output):
            if seen[0]:
                return output
            seen[0]=True
            return self.carrier_embeddings(output,positions,g3t)
        def prefill(module, args, values):
            # Native generation owns all cache and subsequent-token positions.
            if carriers and values['inputs_embeds'].shape[1] == batch['input_ids'].shape[1]:
                if self.carrier_placement == C1_B:
                    values['position_ids'] = frame_position_ids(values['position_ids'], batch)
                if self.carrier_placement == C1_C:
                    values['c1_prefix_mask'] = standard_attention_mask(batch, True)
            return args, values
        inputs={k:batch[k] for k in ('input_ids','attention_mask','pixel_values_videos',
                                      'video_grid_thw','pixel_values','image_grid_thw','mm_token_type_ids') if k in batch}
        with ExitStack() as stack:
            g3t = self.patch_injection(stack, batch, geometry)
            if carriers:
                hook = self.get_input_embeddings().register_forward_hook(replace)
                stack.callback(hook.remove)
            prefix_hook = self.model.language_model.register_forward_pre_hook(prefill, with_kwargs=True)
            stack.callback(prefix_hook.remove)
            if 'aux_gf1_cache' in batch:
                stack.callback(batch['aux_gf1_cache'].clear)
            return native.generate(**inputs,**{**kwargs,'use_cache':True})

    def hidden(self, batch, carriers=True):
        if carriers:
            self.check_placement(batch)
        ids = batch['input_ids']
        geometry = None
        if carriers or self.geometry_online is not None:
            geometry = self.geometry_features(batch)
        if carriers:
            positions = batch['aux_camera_positions']
            present = positions >= 0
            if (ids.gather(1, positions.clamp_min(0))[present] != self.carrier_id).any():
                raise ValueError('Carrier positions do not name carriers')
        # Native IDs retain Qwen's visual placeholders and timestamp-aware mRoPE.
        # Replace values at the embedding output, as in the existing CPDM path.
        inputs = {k: batch[k] for k in ('input_ids', 'attention_mask', 'pixel_values_videos',
                                       'video_grid_thw', 'pixel_values', 'image_grid_thw', 'mm_token_type_ids') if k in batch}
        if carriers and self.carrier_placement == C1_B:
            native, _ = self.model.get_rope_index(
                ids, batch['mm_token_type_ids'], video_grid_thw=batch['video_grid_thw'],
                attention_mask=batch['attention_mask'])
            inputs['position_ids'] = frame_position_ids(native, batch)
        if carriers and self.carrier_placement == C1_C:
            inputs['c1_prefix_mask'] = standard_attention_mask(batch, True)
        with ExitStack() as stack:
            g3t = self.patch_injection(stack, batch, geometry)
            if carriers:
                hook = self.get_input_embeddings().register_forward_hook(
                    lambda module, args, output: self.carrier_embeddings(output, positions, g3t))
                stack.callback(hook.remove)
            return self.model(**inputs, use_cache=False, return_dict=True).last_hidden_state

    def pose_prediction(self, hidden, batch):
        """No-grad final-stage pose codes [1, 32, 9]; slots 7:9 are the one FoV."""
        pose = self.auxiliary_heads.pose
        positions = batch['aux_camera_positions']
        with torch.no_grad():
            stages = pose.predict_all(pose.carrier_states(hidden.float(), positions), key_mask=positions >= 0)[0]
        return stages[-1].detach()

    def pose_fov(self, hidden, batch):
        """The one FoV: pose head slots 7:9 (vertical, horizontal), detached."""
        return self.pose_prediction(hidden, batch)[..., 7:9]

    @staticmethod
    def pose_errors(prediction, targets, batch):
        """Rotation and FoV errors (degrees) on supervised slots; the own-value gate metrics."""
        mask = targets['aux_camera_mask'] & (batch['aux_camera_positions'] >= 0)
        if not mask.any():
            return {}
        gt = targets['aux_camera_target'].float()
        q = F.normalize(prediction[..., 3:7].float(), dim=-1)
        rotation = 2 * torch.acos((q * gt[..., 3:7]).sum(-1).abs().clamp(max=1)) * 180 / math.pi
        fov = (prediction[..., 7:9].float() - gt[..., 7:9]).abs().mean(-1) * 180 / math.pi
        return dict(rotation_deg=float(rotation[mask].mean()), fov_deg=float(fov[mask].mean()))

    @torch.no_grad()
    def readout_heads(self, hidden, batch, uv):
        """Own-head values for routed calls: all-frame pose, gravity, point depth at uv [32, K, 2]."""
        pose = self.auxiliary_heads.pose
        positions = batch['aux_camera_positions']
        if not (positions >= 0).all():
            raise ValueError('Routing readout requires all 32 frame carriers')
        stages, gravity, _ = pose.predict_all(pose.carrier_states(hidden.float(), positions), key_mask=positions >= 0)
        prediction = stages[-1]
        depth = None
        if hasattr(self.auxiliary_heads, 'depth') and uv is not None:
            if self.depth_fov_source != 'pose_head':
                raise ValueError('Routed depth requires the pose-head FoV as its one conditioning FoV')
            depth, _ = self.auxiliary_heads.depth(batch, uv=uv[None], fov=prediction[..., 7:9])
        return dict(pose=prediction.float(), gravity=gravity[-1].float() if gravity else None,
                    depth=None if depth is None else depth.float())

    def forward(self, batch, targets=None, stream='pose', return_states=False):
        if stream == 'mdg':
            from .stageb_mdg import forward
            return forward(self, batch, targets)
        if stream not in ('pose', 'vqa', 'pointing', 'routing', 'readout'):
            raise ValueError('Unknown C1 stream')
        if self.training_mode == 'pose_only' and stream != 'pose':
            raise ValueError('Pose-only mode refuses VQA, pointing and routing')
        if stream in ('routing', 'readout') and self.training_mode != 'final':
            raise ValueError('Routing streams require training_mode final')
        image = 'image_grid_thw' in batch and 'video_grid_thw' not in batch
        hidden = self.hidden(batch, carriers=not image)
        if stream == 'readout':
            # A no-grad FSDP collective that every rank runs in the same microstep.
            return self.readout_heads(hidden, batch, None if targets is None else targets.get('uv'))
        zero = hidden.sum() * 0.
        if self.geometry_online and self.geometry_online.get('gf1', {}).get('stage') == 1:
            # Image-only rows preserve the current mix but have no geometry signal.
            zero = zero + self.auxiliary_heads.gf1.outputs[0].weight.sum() * 0.
        components = dict(pose=zero, depth=zero, depth_fov=zero, vqa=zero, pointing=zero, routing=zero)
        metrics = {'gx': dict(self.gx_metrics)} if self.geometry_online is not None else {}
        align = None
        if stream == 'pose':
            if self.geometry_online is not None:
                metrics['gx'] = dict(self.gx_metrics)
            pose = self.auxiliary_heads.pose
            projected = []
            # C1-r teacher package: capture the projector output the pose head consumes.
            hook = (pose.projector.register_forward_hook(lambda module, args, value: projected.append(value))
                    if hasattr(self, 'align_settings') else None)
            try:
                components['pose'] = pose.loss(hidden.float(),
                    {**targets, 'aux_camera_positions': batch['aux_camera_positions']}).mean()
                # Logging only: the camera head's unweighted parts (pose, gravity, scale, point_depth).
                metrics['pose_parts'] = {k: float(v.float().mean()) for k, v in pose.last_components.items()}
            finally:
                if hook is not None:
                    hook.remove()
            if hook is not None:
                from .c1r_align import alignment_loss
                if self.align_settings['cam']['layer'] != 'final':
                    raise ValueError('Final mode aligns the final-layer carrier states only')
                align = alignment_loss(self, hidden, None, batch, targets, projected=projected[0])
            prediction = None
            if self.training_mode == 'final':
                prediction = self.pose_prediction(hidden, batch)
                metrics.update(self.pose_errors(prediction, targets, batch))
            # Pose-only/mixed modes skip private-encoder work for rows without depth
            # labels. Final mode runs depth on every pose row so every rank executes
            # the same branch in a pose microstep (unlabelled rows add a zero term).
            # With depth_fov_source pose_head, depth reads the pose head's FoV, the
            # same FoV the fixed unprojection layer uses at inference.
            if hasattr(self.auxiliary_heads, 'depth') and (self.training_mode == 'final'
                                                           or targets['aux_point_depth_mask'].any()):
                fov = None
                if self.depth_fov_source == 'pose_head':
                    fov = (prediction if prediction is not None else self.pose_prediction(hidden, batch))[..., 7:9]
                components['depth'], components['depth_fov'] = self.auxiliary_heads.depth(batch, targets, fov=fov)
                metrics['depth_absrel'] = getattr(self.auxiliary_heads.depth, 'last_absrel', None)
        elif stream == 'routing':
            labels = batch['labels'][:, 1:]
            valid = labels != -100
            if not valid.any():
                raise ValueError('Routing rows require assistant labels')
            logits = self.lm_head(hidden[:, :-1][valid]).float()
            losses = F.cross_entropy(logits, labels[valid], reduction='none')
            components['routing'] = losses.mean()
            if 'aux_segments' in batch:
                from .carrier_c1_routing import SEGMENTS
                tags = batch['aux_segments'][:, 1:][valid]
                detached = losses.detach()
                metrics['segments'] = {name: [float(detached[tags == i].sum()), int((tags == i).sum())]
                                       for i, name in enumerate(SEGMENTS) if (tags == i).any()}
        else:
            labels = batch['labels'][:, 1:]
            valid = labels != -100
            if not valid.any():
                raise ValueError('Preservation/pointing rows require assistant labels')
            # Only assistant positions need vocabulary logits (large memory saving).
            logits = self.lm_head(hidden[:, :-1][valid]).float()
            losses = F.cross_entropy(logits, labels[valid], reduction='none')
            if stream == 'pointing' and 'aux_token_weights' in batch:
                # Config pointing_weights: the null-or-point decision token weighs more (mean row weight fixed).
                components[stream] = (losses * batch['aux_token_weights'][:, 1:][valid].to(losses.dtype)).mean()
            else:
                components[stream] = losses.mean()
            if 'aux_segments' in batch:
                # Per-segment [CE sum, token count] (logging only; the loss is the row mean above).
                from .carrier_c1_data import STREAM_SEGMENTS
                tags = batch['aux_segments'][:, 1:][valid]
                detached = losses.detach()
                metrics['segments'] = {name: [float(detached[tags == i].sum()), int((tags == i).sum())]
                                       for i, name in enumerate(STREAM_SEGMENTS) if (tags == i).any()}
        # All replicated parameters participate in every synchronized step.
        # The legacy path touches the LM head with a zero gradient. Pose-only
        # training can omit it: every rank follows the same stream schedule.
        touch = sum(p.reshape(-1)[0] * 0. for p in self.auxiliary_heads.parameters() if p.requires_grad)
        if stream == 'pose' and not (self.skip_unsupervised_lm and
                ('labels' not in batch or not (batch['labels'][:, 1:] != -100).any())):
            touch = touch + self.lm_head(hidden[:, :1]).sum() * 0.
        # Pre-final recipes carry no routing weight; their routing component is always zero.
        loss = sum(self.recipe['weights'].get(k, 0.) * v for k, v in components.items()) + touch
        if align is not None:
            # Teacher terms carry their own weights (align settings); uncovered rows add zero.
            loss = loss + align[0]
            components.update(align[1])
        if 'aux_gf1_cache' in batch:
            # Checkpoint arguments retain this row's bank until backward; prefetched
            # rows must not keep a second GPU reference after their supervised call.
            batch['aux_gf1_cache'].clear()
        result = dict(loss=loss, components={k: v.detach() for k, v in components.items()}, metrics=metrics)
        if return_states and not image:
            result['states'] = self.auxiliary_heads.pose.carrier_states(
                hidden.float(), batch['aux_camera_positions'])
        return result

    @torch.no_grad()
    def probe(self, batch, targets):
        hidden = self.hidden(batch).float()
        camera = self.auxiliary_heads.pose
        states = camera.carrier_states(hidden, batch['aux_camera_positions'])
        valid = batch['aux_camera_positions'] >= 0
        stages = camera.predict_all(states, key_mask=valid)[0]
        pred = stages[-1]
        mask = targets['aux_camera_mask'] & valid
        gt = targets['aux_camera_target']
        q = F.normalize(pred[..., 3:7], dim=-1)
        rotation = 2 * torch.acos((q * gt[..., 3:7]).sum(-1).abs().clamp(max=1)) * 180 / math.pi
        # q is xyzw, so its last coordinate measures rotation from identity.
        magnitude = 2 * torch.acos(q[..., 3].abs().clamp(max=1)) * 180 / math.pi
        return dict(valid_frames=int(mask.sum()), rotation_mean_deg=float(rotation[mask].mean()),
                    rotation_median_deg=float(rotation[mask].median()),
                    prediction_magnitude_median_deg=float(magnitude[mask].median()),
                    carrier_state_std=float(states[valid].std()),
                    final_layer_only=camera.settings['feature_layers'] is None,
                    finite=bool(torch.isfinite(pred[mask]).all()))

    @torch.no_grad()
    def pose_readout(self, batch):
        self.eval()
        camera = self.auxiliary_heads.pose
        valid = batch['aux_camera_positions'] >= 0
        if not valid.all():
            raise ValueError('Clip pose readout requires all 32 frames')
        states = camera.carrier_states(self.hidden(batch).float(), batch['aux_camera_positions'])
        return camera.predict_all(states, key_mask=valid)[0][-1][0].double().cpu().numpy()

    @torch.no_grad()
    def readout(self, batch, uv):
        """All-frame pose and private depth in the existing head_acc row layout."""
        self.eval()
        camera=self.auxiliary_heads.pose
        states=camera.carrier_states(self.hidden(batch).float(),batch['aux_camera_positions'])
        valid=batch['aux_camera_positions']>=0
        pose,gravity,scale=camera.predict_all(states,key_mask=valid)
        points=torch.as_tensor(uv,dtype=torch.float32,device=states.device)
        even=points.shape[0]==16
        if even:
            points=points.repeat_interleave(2,dim=0)
        if points.shape[0]!=32 or not valid.all():
            raise ValueError('Readout requires 32 visible frames and 16 or 32 depth slots')
        depth = None
        if hasattr(self.auxiliary_heads, 'depth'):
            # The one FoV: in pose_head mode the milestone readout conditions depth as training did.
            fov=pose[-1][...,7:9] if self.depth_fov_source=='pose_head' else None
            depth,_=self.auxiliary_heads.depth(batch,uv=points[None],fov=fov)
        raw=pose[-1][0].double().cpu().tolist()
        return dict(raw_pose=raw,gravity_up=gravity[-1][0].double().cpu().tolist() if gravity else None,
                    trajectory_step_m=float(scale[-1][0].exp()) if scale else None,
                    point_depth=None if depth is None else (depth[1::2] if even else depth).double().cpu().tolist(),
                    invalid_fov_frames=[dict(frame=i+1,fov_hw_rad=p[7:9]) for i,p in enumerate(raw)
                                        if any(not 0<x<math.pi for x in p[7:9])],geometry_error=None)


def parameter_groups(model, recipe=RECIPE, inherited=(), pose_lr_scale=1.0, lm_lr_scale=1.0, _gf1=True):
    """`inherited`: pose-head tensor names copied from a teacher head (C1-r); they keep the LM rate.
    `pose_lr_scale` (config pose_lr_scale) moves the pose head and carriers into their own group at that
    fraction of the head rate; at 1.0 the groups are unchanged."""
    if _gf1 and 'gf1' in (getattr(model, 'geometry_online', None) or {}):
        from .gf1 import parameter_groups as gf1_groups
        return gf1_groups(model, recipe, inherited, pose_lr_scale, lm_lr_scale)
    groups = dict(llm=[], heads_pretrained=[], heads=[], pose=[], encoder_copy=[], geometry_encoder=[])
    mdg = getattr(model, 'mdg_settings', None)
    if mdg:
        groups['heads_mdg'] = []
        groups['mdg_lora'] = []
    fusion = 'patch_fusion' in (getattr(model, 'geometry_online', None) or {})
    if fusion:
        groups['pose_connector'] = []
        if model.training_mode == 'final':
            groups['heads_cp1'] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        name = full_ft.clean_name(name)
        connector = name.startswith('auxiliary_heads.pose.cam_token_connector.')
        group = ('geometry_encoder' if name.startswith('auxiliary_heads.geometry_encoder.') else
                 'encoder_copy' if name.startswith('auxiliary_heads.depth.model.visual.') else
                 'pose_connector' if fusion and connector and pose_lr_scale != 1.0 else
                 'heads' if fusion and (connector or name.startswith('auxiliary_heads.patch_fusion.')) else
                 'heads_pretrained' if (name.startswith('auxiliary_heads.pose.head.')
                                        and name.removeprefix('auxiliary_heads.pose.head.') in inherited) else
                 'pose' if ((fusion and name.startswith('auxiliary_heads.')) or
                            (pose_lr_scale != 1.0 and name.startswith('auxiliary_heads.pose.'))) else
                 'heads' if name.startswith('auxiliary_heads.') else 'llm')
        if fusion and model.training_mode == 'final' and name.startswith('auxiliary_heads.') and not (
                connector or name.startswith(('auxiliary_heads.patch_fusion.', 'auxiliary_heads.geometry_encoder.'))):
            # Preserve CP1's rates for depth, frame embeddings and inherited pose
            # tensors. Only the new projector and connector align for 50 steps.
            group = ('encoder_copy' if name.startswith('auxiliary_heads.depth.model.visual.') else
                     'heads_pretrained' if name.startswith('auxiliary_heads.pose.head.')
                         and name.removeprefix('auxiliary_heads.pose.head.') in inherited else
                     'pose' if pose_lr_scale != 1.0 and name.startswith('auxiliary_heads.pose.') else 'heads_cp1')
        if mdg and name.startswith('auxiliary_heads.mdg.'):
            group = 'heads_mdg'
        if mdg and name.startswith('auxiliary_heads.mdg_lora.'):
            group = 'mdg_lora'
        groups[group].append(parameter)
    # `lm_lr_scale` (config) scales the LM group's rate, e.g. to cap the re-warm when continuing a converged run.
    rates = dict(llm=recipe['lm_learning_rate'] * lm_lr_scale, heads_pretrained=recipe['lm_learning_rate'],
                 heads=recipe['learning_rate'], pose=recipe['learning_rate'] * pose_lr_scale,
                 encoder_copy=recipe['encoder_learning_rate'])
    if mdg:
        rates['heads_mdg'] = recipe['learning_rate'] * mdg['lr_scale']
        rates['mdg_lora'] = mdg['lora_lr']
    if groups['geometry_encoder']:
        rates['geometry_encoder'] = recipe['geometry_learning_rate']
    if fusion:
        rates['pose_connector'] = rates['pose']
        rates['heads_cp1'] = rates['heads']
    return [dict(params=parameters, name=name, lr=rates[name], initial_lr=rates[name],
                 **({'weight_decay': 0.} if name == 'mdg_lora' else {}),
                 **({'gx_alignment': name in ('heads', 'pose_connector')} if fusion else {}))
            for name, parameters in groups.items() if parameters]


def load_depth_stage1(model, artifact_pin, verify=True):
    """Initialize the private depth branch from a Stage-1 V-C p3-head-artifact-v1; freeze its encoder copy.

    The encoder copy loads strictly. Point-depth head tensors load by name; a 16-slot
    group embedding (fused pairs) expands to the 32 per-frame slots by repetition.
    """
    from safetensors.torch import load_file
    from .p3_provenance import load, pinned
    depth = model.auxiliary_heads.depth
    artifact = load(pinned(artifact_pin))
    if artifact.get('schema') != 'p3-head-artifact-v1' or artifact.get('feature_backing') != 'decoupled_vc':
        raise ValueError('Stage-1 depth init requires a decoupled_vc p3-head-artifact-v1')
    saved = artifact['encoder_copy']
    # One rank verifies the file bytes; the others load the same pinned paths (no repeated hashing).
    state = load_file(str(pinned(saved['weights']) if verify else saved['weights']['path']))
    depth.model.visual.load_state_dict({k: v.float() for k, v in state.items()}, strict=True)
    heads = load_file(str(pinned(artifact['weights']) if verify else artifact['weights']['path']))
    prefix = 'camera.point_depth.'
    target = depth.auxiliary_heads.camera.point_depth.state_dict()
    loaded = {}
    for key, value in heads.items():
        if not key.startswith(prefix):
            continue
        name = key[len(prefix):]
        if name not in target:
            raise ValueError('Unknown Stage-1 point-depth tensor ' + name)
        if name == 'group_embed' and value.shape[0] * 2 == target[name].shape[0]:
            value = value.repeat_interleave(2, dim=0)
        if value.shape != target[name].shape:
            raise ValueError('Stage-1 point-depth tensor shape differs: ' + name)
        loaded[name] = value.float()
    if set(loaded) != set(target):
        raise ValueError('Stage-1 artifact lacks point-depth tensors: ' + ', '.join(sorted(set(target) - set(loaded))))
    depth.auxiliary_heads.camera.point_depth.load_state_dict(loaded, strict=True)
    if 'frame_queries' in heads and heads['frame_queries'].shape == depth.auxiliary_heads.frame_queries.shape:
        with torch.no_grad():
            depth.auxiliary_heads.frame_queries.copy_(heads['frame_queries'].float())
    depth.model.visual.requires_grad_(False)
    model.depth_stage1 = True
    return dict(artifact=artifact_pin, point_depth_tensors=len(loaded), encoder_tensors=len(state), encoder_frozen=True)
