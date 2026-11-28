"""Spatial-V2 loss suite: Spatial-Forcing^2, decoupled metric/SI depth, SE(3) & 4D flow."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import LossWeightsConfig, SpatialForcing2Config
from .geo_heads import GeoDepthOutput, GeoPoseOutput, so3_log


class SpatialForcing2Loss(nn.Module):
    """Dense teacher patch-cosine + stratified cross-frame Gram distillation (train-only)."""

    def __init__(self, cfg: SpatialForcing2Config, lm_hidden_size: int) -> None:
        super().__init__()
        self.cfg = cfg
        self.probes = nn.ModuleDict(
            {
                str(l): nn.Sequential(
                    nn.Linear(lm_hidden_size, cfg.probe_hidden_dim),
                    nn.GELU(),
                    nn.Linear(cfg.probe_hidden_dim, cfg.teacher_dim),
                )
                for l in cfg.tap_layers
            }
        )

    @staticmethod
    def _stratified_indices(n_views: int, p_per_view: int, k: int, device: torch.device) -> torch.Tensor:
        total = n_views * p_per_view
        if total <= k:
            return torch.arange(total, device=device)
        per_v = max(1, k // max(n_views, 1))
        idx = torch.cat([v * p_per_view + torch.randperm(p_per_view, device=device)[:per_v] for v in range(n_views)])
        return idx[:k]

    def forward(
        self,
        student_taps: Dict[int, torch.Tensor],
        teacher_feats: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        tea = torch.nan_to_num(teacher_feats.detach().float(), nan=0.0, posinf=0.0, neginf=0.0)
        bsz, n_views, p_per_view, d_tea = tea.shape
        tea_norm = F.normalize(tea.reshape(bsz, n_views * p_per_view, d_tea), dim=-1, eps=1e-6)
        if valid_mask is None:
            vm = torch.ones((bsz, n_views * p_per_view), device=tea.device)
        elif valid_mask.ndim == 2:
            vm = valid_mask.bool().unsqueeze(-1).expand(bsz, n_views, p_per_view).reshape(bsz, -1).float()
        else:
            vm = valid_mask.bool().reshape(bsz, -1).float()

        s_idx = self._stratified_indices(n_views, p_per_view, self.cfg.gram_num_samples, tea.device)
        u_tea = tea_norm[:, s_idx, :]
        gram_tea = torch.bmm(u_tea, u_tea.transpose(1, 2))
        vm_k = vm[:, s_idx]
        g_mask = vm_k.unsqueeze(2) * vm_k.unsqueeze(1)

        feat_losses, gram_losses, details = [], [], {}
        for l_str, probe in self.probes.items():
            lid = int(l_str)
            if lid not in student_taps:
                continue
            stu_norm = F.normalize(probe(student_taps[lid]).float().reshape(bsz, n_views * p_per_view, d_tea), dim=-1, eps=1e-6)
            l_feat = ((1.0 - (stu_norm * tea_norm).sum(dim=-1)) * vm).sum() / vm.sum().clamp_min(1.0)
            u_stu = stu_norm[:, s_idx, :]
            l_gram = ((torch.bmm(u_stu, u_stu.transpose(1, 2)) - gram_tea).pow(2) * g_mask).sum() / g_mask.sum().clamp_min(1.0)
            feat_losses.append(l_feat)
            gram_losses.append(l_gram)
            details[f"sf2_feat_l{lid}"], details[f"sf2_gram_l{lid}"] = l_feat.detach(), l_gram.detach()

        if not feat_losses:
            z = tea.new_zeros(())
            return z, z, details
        return torch.stack(feat_losses).mean(), torch.stack(gram_losses).mean(), details


class DecoupledDepthLoss(nn.Module):
    """Decoupled scale-invariant + metric Laplacian NLL depth loss.

    When `metric_scale_locked[b] == 0`, strictly shift-invariant losses apply so
    uncalibrated clips produce exact zero gradient into `log_gamma_scene`.
    """

    def __init__(self, silog_lambda: float = 0.5, scale_huber_delta: float = 0.2) -> None:
        super().__init__()
        self.silog_lambda = silog_lambda
        self.scale_huber_delta = scale_huber_delta

    @staticmethod
    def _gradient_loss(pred: torch.Tensor, gt: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        mx = mask[..., :, 1:] * mask[..., :, :-1]
        my = mask[..., 1:, :] * mask[..., :-1, :]
        lx = ((pred[..., :, 1:] - pred[..., :, :-1] - (gt[..., :, 1:] - gt[..., :, :-1])).abs() * mx).sum() / mx.sum().clamp_min(1.0)
        ly = ((pred[..., 1:, :] - pred[..., :-1, :] - (gt[..., 1:, :] - gt[..., :-1, :])).abs() * my).sum() / my.sum().clamp_min(1.0)
        return 0.5 * (lx + ly)

    def forward(
        self,
        depth_out: GeoDepthOutput,
        depth_gt: torch.Tensor,
        valid_mask: torch.Tensor,
        metric_scale_locked: torch.Tensor,
        view_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        bsz = depth_gt.shape[0]
        valid_bool = valid_mask.bool() & torch.isfinite(depth_gt) & (depth_gt > 1e-4)
        if view_mask is not None:
            valid_bool = valid_bool & view_mask.bool()[:, :, None, None]
        m = valid_bool.float()
        safe_depth_gt = torch.where(valid_bool, depth_gt.float(), torch.ones_like(depth_gt, dtype=torch.float32))
        log_gt = torch.log(safe_depth_gt.clamp_min(1e-4))
        s_hat = depth_out.log_var_depth.float()
        locked = metric_scale_locked.float().view(bsz)

        # Shift-invariant residual (identically independent of log_gamma_scene)
        r_rel = (depth_out.d_shape.float() + depth_out.mu_view.float()[:, :, None, None] - log_gt) * m
        m_sum_b = m.sum(dim=(1, 2, 3)).clamp_min(1.0)
        r_cent = (r_rel - ((r_rel * m).sum(dim=(1, 2, 3)) / m_sum_b)[:, None, None, None]) * m
        si_var_b = (r_cent.pow(2) * m).sum(dim=(1, 2, 3)) / m_sum_b
        si_nll_b = ((r_cent.abs() * torch.exp(-0.5 * s_hat) + 0.5 * s_hat) * m).sum(dim=(1, 2, 3)) / m_sum_b
        grad_loss = self._gradient_loss(depth_out.d_shape.float(), log_gt, m)

        # Metric-locked losses (strictly zeroed when metric_scale_locked[b] == 0)
        r_m = (depth_out.log_depth.float() - log_gt) * m * locked[:, None, None, None]
        metric_nll_b = ((r_m.abs() * torch.exp(-0.5 * s_hat) + 0.5 * s_hat * locked[:, None, None, None]) * m).sum(
            dim=(1, 2, 3)
        ) / m_sum_b
        r_m_mean = (r_m * m).sum(dim=(1, 2, 3)) / m_sum_b
        silog_b = ((r_m.pow(2) * m).sum(dim=(1, 2, 3)) / m_sum_b - self.silog_lambda * r_m_mean.pow(2)).clamp_min(0.0)
        scale_huber_b = F.huber_loss(r_m_mean, torch.zeros_like(r_m_mean), reduction="none", delta=self.scale_huber_delta)

        per_b = (1.0 - locked) * (si_var_b + 0.5 * si_nll_b) + locked * (silog_b + metric_nll_b + scale_huber_b)
        valid_b = (m.sum(dim=(1, 2, 3)) > 0).float()
        total = (per_b * valid_b).sum() / valid_b.sum().clamp_min(1.0) + 0.5 * grad_loss
        return total, {
            "depth_total": total.detach(),
            "depth_si_var": si_var_b.mean().detach(),
            "depth_grad": grad_loss.detach(),
            "depth_scale_err": (scale_huber_b * locked).sum().detach() / locked.sum().clamp_min(1.0),
        }


class PoseAnd4DLoss(nn.Module):
    """Pairwise SE(3) + gravity + FoV + Plucker raymap + pointmap + 4D rigidity/flow losses."""

    def __init__(self, max_pairs: int = 256) -> None:
        super().__init__()
        self.max_pairs = max_pairs

    def forward(
        self,
        pose_out: GeoPoseOutput,
        depth_out: GeoDepthOutput,
        rot_gt: torch.Tensor,
        trans_gt: torch.Tensor,
        gravity_gt: torch.Tensor,
        log_fx_w_gt: torch.Tensor,
        log_fy_h_gt: torch.Tensor,
        plucker_gt: torch.Tensor,
        metric_scale_locked: torch.Tensor,
        y_stat_gt: Optional[torch.Tensor] = None,
        delta_p_gt: Optional[torch.Tensor] = None,
        pmap_pred: Optional[torch.Tensor] = None,
        pmap_gt: Optional[torch.Tensor] = None,
        view_mask: Optional[torch.Tensor] = None,
        delta_p_rev: Optional[torch.Tensor] = None,
        flow_valid: Optional[torch.Tensor] = None,
        pmap_valid: Optional[torch.Tensor] = None,
    ) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]:
        bsz, n_views = rot_gt.shape[:2]
        device = rot_gt.device
        vm_bool = torch.ones((bsz, n_views), dtype=torch.bool, device=device) if view_mask is None else view_mask.bool()
        vm = vm_bool.float()
        locked = metric_scale_locked.float().view(bsz, 1)
        r_p, t_p = pose_out.rot.float(), pose_out.trans.float()
        eye3 = torch.eye(3, device=device, dtype=torch.float32).view(1, 1, 3, 3).expand(bsz, n_views, 3, 3)
        r_g = torch.where(vm_bool[:, :, None, None] & torch.isfinite(rot_gt), rot_gt.float(), eye3)
        t_g = torch.where(vm_bool[:, :, None] & torch.isfinite(trans_gt), trans_gt.float(), torch.zeros_like(t_p))

        idx_i, idx_j = torch.triu_indices(n_views, n_views, offset=1, device=device)
        if idx_i.numel() > self.max_pairs:
            sel = torch.linspace(0, idx_i.numel() - 1, self.max_pairs, device=device).long()
            idx_i, idx_j = idx_i[sel], idx_j[sel]

        if idx_i.numel() > 0:
            pm = vm[:, idx_i] * vm[:, idx_j]
            r_ij_p = r_p[:, idx_j] @ r_p[:, idx_i].transpose(-1, -2)
            t_ij_p = t_p[:, idx_j] - (r_ij_p @ t_p[:, idx_i].unsqueeze(-1)).squeeze(-1)
            r_ij_g = r_g[:, idx_j] @ r_g[:, idx_i].transpose(-1, -2)
            t_ij_g = t_g[:, idx_j] - (r_ij_g @ t_g[:, idx_i].unsqueeze(-1)).squeeze(-1)

            w_err = so3_log(r_ij_g.transpose(-1, -2) @ r_ij_p)
            rot_loss = (torch.sqrt((w_err * w_err).sum(dim=-1) + 1e-8) * pm).sum() / pm.sum().clamp_min(1.0)

            np_, ng_ = t_ij_p.norm(dim=-1).clamp_min(1e-5), t_ij_g.norm(dim=-1).clamp_min(1e-5)
            has_b = (t_ij_g.norm(dim=-1) > 1e-3).float() * pm
            dir_loss = ((1.0 - ((t_ij_p / np_.unsqueeze(-1)) * (t_ij_g / ng_.unsqueeze(-1))).sum(-1)) * has_b).sum() / has_b.sum().clamp_min(1.0)

            sp = ((np_ * pm).sum(1, keepdim=True) / pm.sum(1, keepdim=True).clamp_min(1.0)).clamp_min(1e-4)
            sg = ((ng_ * pm).sum(1, keepdim=True) / pm.sum(1, keepdim=True).clamp_min(1.0)).clamp_min(1e-4)
            t_huber = (F.huber_loss(t_ij_p / sp.unsqueeze(-1), t_ij_g / sg.unsqueeze(-1), reduction="none", delta=0.5).mean(-1) * pm).sum() / pm.sum().clamp_min(1.0)
            m_b = has_b * locked
            log_base = ((torch.log(np_) - torch.log(ng_)).abs() * m_b).sum() / m_b.sum().clamp_min(1.0)
            pose_loss = rot_loss + dir_loss + t_huber + 0.3 * log_base

            gp = pose_out.gravity.float()
            g_rot = (r_ij_p @ gp[:, idx_i].unsqueeze(-1)).squeeze(-1)
            grav_xv = ((g_rot - gp[:, idx_j]).pow(2).sum(-1) * pm).sum() / pm.sum().clamp_min(1.0)
        else:
            pose_loss, grav_xv = r_p.new_zeros(()), r_p.new_zeros(())

        g_gt_raw = torch.where(
            vm_bool[:, :, None] & torch.isfinite(gravity_gt), gravity_gt.float(), pose_out.gravity.float().detach()
        )
        g_gt = F.normalize(g_gt_raw, dim=-1, eps=1e-7)
        grav_loss = ((1.0 - (pose_out.gravity.float() * g_gt).sum(-1)) * vm).sum() / vm.sum().clamp_min(1.0) + 0.5 * grav_xv

        fx_gt_safe = torch.where(vm_bool & torch.isfinite(log_fx_w_gt), log_fx_w_gt.float(), pose_out.log_fx_w.float().detach())
        fy_gt_safe = torch.where(vm_bool & torch.isfinite(log_fy_h_gt), log_fy_h_gt.float(), pose_out.log_fy_h.float().detach())
        fov_loss = (
            (F.huber_loss(pose_out.log_fx_w.float(), fx_gt_safe, reduction="none", delta=0.2)
             + F.huber_loss(pose_out.log_fy_h.float(), fy_gt_safe, reduction="none", delta=0.2)) * vm
        ).sum() / vm.sum().clamp_min(1.0)

        ray_valid = vm_bool[:, :, None, None, None] & torch.isfinite(plucker_gt)
        plucker_gt_safe = torch.where(ray_valid, plucker_gt.float(), pose_out.plucker_pred.float().detach())
        ray_loss = (F.huber_loss(pose_out.plucker_pred.float(), plucker_gt_safe, reduction="none", delta=0.2).mean(dim=(-3, -2, -1)) * vm).sum() / vm.sum().clamp_min(1.0)

        if pmap_pred is not None and pmap_gt is not None:
            pp_f = pmap_pred.float()
            pm_valid_bool = (
                vm_bool[:, :, None, None].expand(pp_f.shape[:4])
                & torch.isfinite(pmap_gt).all(dim=-1)
                & torch.isfinite(pp_f).all(dim=-1)
            )
            if pmap_valid is not None:
                pv = pmap_valid.bool()
                if pv.shape[-2:] != pp_f.shape[2:4]:
                    pv = (
                        F.interpolate(pv.float().reshape(bsz * n_views, 1, *pv.shape[-2:]), size=pp_f.shape[2:4], mode="nearest")
                        .reshape(bsz, n_views, *pp_f.shape[2:4]) > 0.5
                    )
                pm_valid_bool = pm_valid_bool & pv
            # Gate metric pointmap loss by metric_scale_locked so unlocked samples give strictly 0.0 grad to log_gamma_scene
            pm_mask = pm_valid_bool.float() * locked[:, :, None, None]
            pp_safe = torch.where(pm_valid_bool.unsqueeze(-1) & (locked[:, :, None, None, None] > 0.0), pp_f, pp_f.detach())
            pg_safe = torch.where(pm_valid_bool.unsqueeze(-1), pmap_gt.float(), pp_f.detach())
            pmap_err = F.huber_loss(pp_safe, pg_safe, reduction="none", delta=0.25).mean(dim=-1)
            pmap_loss = (pmap_err * pm_mask).sum() / pm_mask.sum().clamp_min(1.0)
        else:
            pmap_loss = r_p.new_zeros(())

        if y_stat_gt is not None:
            rig_logits = depth_out.rigidity_logits.float()
            rig_valid = vm_bool[:, :, None, None] & torch.isfinite(y_stat_gt)
            y_stat_safe = torch.where(rig_valid, y_stat_gt.float(), torch.zeros_like(rig_logits))
            bce = F.binary_cross_entropy_with_logits(rig_logits, y_stat_safe, reduction="none")
            rig_m = rig_valid.float()
            rig_loss = (bce * rig_m).sum() / rig_m.sum().clamp_min(1.0)
        else:
            rig_loss = r_p.new_zeros(())

        dp_p, lvf = depth_out.delta_p_obj.float(), depth_out.log_var_flow.float()
        f_base_bool = vm_bool[:, :, None, None, None, None].expand(
            bsz, n_views, dp_p.shape[2], dp_p.shape[3], dp_p.shape[4], 1
        )
        if flow_valid is not None:
            fv = flow_valid.bool()
            if fv.ndim == 4:
                fv = fv[:, :, :, :, None, None]
            elif fv.ndim == 5:
                fv = fv.unsqueeze(-1)
            f_base_bool = f_base_bool & fv

        if delta_p_gt is not None:
            f_gt_bool = f_base_bool & torch.isfinite(delta_p_gt).all(dim=-1, keepdim=True)
            dp_gt_safe = torch.where(f_gt_bool.expand_as(dp_p), delta_p_gt.float(), dp_p.detach())
            hf = F.huber_loss(dp_p, dp_gt_safe, reduction="none", delta=0.2).mean(dim=-1, keepdim=True)
            nll_f = hf / torch.exp(0.5 * lvf) + 0.5 * lvf
            f_gt_m = f_gt_bool.float()
            flow_loss = (nll_f * f_gt_m).sum() / f_gt_m.sum().clamp_min(1.0)
        else:
            flow_loss = r_p.new_zeros(())

        # Static pixels (p_stat -> 1) should have sparse / zero residual object motion delta_p_obj
        sp_mask = f_base_bool.expand_as(dp_p).float()
        sparsity = (
            depth_out.p_stat.float()[:, :, :, :, None, None] * dp_p.abs() * sp_mask
        ).sum() / sp_mask.sum().clamp_min(1.0)

        if delta_p_rev is not None:
            f_rev_bool = f_base_bool & torch.isfinite(delta_p_rev).all(dim=-1, keepdim=True)
            f_rev_m = f_rev_bool.expand_as(dp_p).float()
            dp_rev_safe = torch.where(f_rev_bool.expand_as(dp_p), delta_p_rev.float(), -dp_p.detach())
            rev_loss = ((dp_p + dp_rev_safe).abs() * f_rev_m).sum() / f_rev_m.sum().clamp_min(1.0)
        else:
            rev_loss = r_p.new_zeros(())

        terms = {
            "pose": pose_loss, "gravity": grav_loss, "fov": fov_loss, "ray": ray_loss, "pmap": pmap_loss,
            "rigidity": rig_loss, "flow": flow_loss, "flow_sparsity": sparsity, "reversal": rev_loss,
        }
        return terms, {k: v.detach() for k, v in terms.items()}


class SpatialV2CompositeLoss(nn.Module):
    """Unified Spatial-V2 loss combining Spatial-Forcing^2, depth, pose, pointmap, and 4D flow."""

    def __init__(self, sf2_cfg: SpatialForcing2Config, weights_cfg: LossWeightsConfig, lm_hidden_size: int) -> None:
        super().__init__()
        self.w = weights_cfg
        self.sf2 = SpatialForcing2Loss(sf2_cfg, lm_hidden_size=lm_hidden_size)
        self.depth_loss = DecoupledDepthLoss()
        self.pose_4d_loss = PoseAnd4DLoss()

    def forward(
        self,
        student_taps: Dict[int, torch.Tensor],
        teacher_feats: torch.Tensor,
        depth_out: GeoDepthOutput,
        pose_out: GeoPoseOutput,
        targets: Dict[str, torch.Tensor],
        pmap_pred: Optional[torch.Tensor] = None,
        view_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        l_feat, l_gram, sf2_m = self.sf2(student_taps, teacher_feats, valid_mask=view_mask)
        depth_valid = targets["depth_valid"].bool()
        if view_mask is not None:
            depth_valid = depth_valid & view_mask.bool()[:, :, None, None]
        l_depth, depth_m = self.depth_loss(
            depth_out, targets["depth_gt"], depth_valid, targets["metric_scale_locked"], view_mask=view_mask
        )
        p4d, p4d_m = self.pose_4d_loss(
            pose_out=pose_out, depth_out=depth_out,
            rot_gt=targets["rot_gt"], trans_gt=targets["trans_gt"], gravity_gt=targets["gravity_gt"],
            log_fx_w_gt=targets["log_fx_w_gt"], log_fy_h_gt=targets["log_fy_h_gt"], plucker_gt=targets["plucker_gt"],
            metric_scale_locked=targets["metric_scale_locked"],
            y_stat_gt=targets.get("y_stat_gt"), delta_p_gt=targets.get("delta_p_gt"),
            pmap_pred=pmap_pred, pmap_gt=targets.get("pmap_gt"),
            view_mask=view_mask, delta_p_rev=targets.get("delta_p_rev"),
            flow_valid=targets.get("flow_valid"), pmap_valid=targets.get("pmap_valid"),
        )
        total = (
            self.w.sf2_feat * l_feat + self.w.sf2_gram * l_gram + self.w.depth * l_depth
            + self.w.pose * p4d["pose"] + self.w.gravity * p4d["gravity"] + self.w.fov * p4d["fov"]
            + self.w.ray * p4d["ray"] + self.w.pmap * p4d["pmap"] + self.w.rigidity * p4d["rigidity"]
            + self.w.flow * p4d["flow"] + self.w.flow_sparsity * p4d["flow_sparsity"]
            + self.w.reversal * p4d["reversal"]
        )
        return total, {"total_loss": total.detach(), **sf2_m, **depth_m, **p4d_m}
