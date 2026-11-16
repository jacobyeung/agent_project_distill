import torch
import torch.nn as nn
from huggingface_hub import PyTorchModelHubMixin
from u0.models.aggregator import Aggregator
from u0.heads.camera_head import CameraHead
from u0.heads.dpt_head import DPTHead

class N0(nn.Module, PyTorchModelHubMixin):

    def __init__(self, img_size=518, patch_size=14, embed_dim=1024, enable_point=True, enable_depth=True, enable_gravity_camera_heads=True):
        super().__init__()
        self.aggregator = Aggregator(img_size=img_size, patch_size=patch_size, embed_dim=embed_dim)
        if enable_gravity_camera_heads:
            self.local_camera_head = CameraHead(dim_in=2 * embed_dim, pose_encoding_type='noT_quaR_FoV')
            self.global_camera_head = CameraHead(dim_in=2 * embed_dim, pose_encoding_type='absT_quaRy_noFoV')
        else:
            self.local_camera_head = None
            self.global_camera_head = None
        self.point_head = DPTHead(dim_in=2 * embed_dim, output_dim=4, activation='inv_log', conf_activation='expp1') if enable_point else None
        self.depth_head = DPTHead(dim_in=2 * embed_dim, output_dim=2, activation='exp', conf_activation='expp1') if enable_depth else None

    def forward(self, images: torch.Tensor):
        if len(images.shape) == 4:
            images = images.unsqueeze(0)
        aggregated_tokens_list, patch_start_idx = self.aggregator(images)
        predictions = {}
        with torch.amp.autocast('cuda', enabled=False):
            if self.local_camera_head is not None and self.global_camera_head is not None:
                local_pose_enc_list = self.local_camera_head(aggregated_tokens_list)
                global_pose_enc_list = self.global_camera_head(aggregated_tokens_list)
                predictions['local_pose_enc'] = local_pose_enc_list[-1]
                predictions['global_pose_enc'] = global_pose_enc_list[-1]
                predictions['local_pose_enc_list'] = local_pose_enc_list
                predictions['global_pose_enc_list'] = global_pose_enc_list
            if self.depth_head is not None:
                depth, depth_conf = self.depth_head(aggregated_tokens_list, images=images, patch_start_idx=patch_start_idx)
                predictions['depth'] = depth
                predictions['depth_conf'] = depth_conf
            if self.point_head is not None:
                pts3d, pts3d_conf = self.point_head(aggregated_tokens_list, images=images, patch_start_idx=patch_start_idx)
                predictions['world_points'] = pts3d
                predictions['world_points_conf'] = pts3d_conf
        if not self.training:
            predictions['images'] = images
        return predictions
