"""Fast 3-5 step damped Levenberg-Marquardt Test-Time Bundle Adjustment (TT-BA)."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import TTBAConfig
from .geo_heads import skew_symmetric, so3_exp


@dataclass
class TTBADiagnostics:
    reproj_err_before: float
    reproj_err_after: float
    parallax_deg: float
    scale_consistency: float
    pose_cond: float
    ray_yaw_disagreement_deg: float
    triggered: bool
    committed: bool
    num_steps_run: int
    elapsed_ms: float


@dataclass
class TTBAOutput:
    rot: torch.Tensor
    trans: torch.Tensor
    log_scale: torch.Tensor
    diagnostics: TTBADiagnostics


def compute_ray_yaw_disagreement_deg(
    plucker_pred: torch.Tensor, plucker_geom: torch.Tensor, valid_mask: Optional[torch.Tensor] = None
) -> float:
    d_p = F.normalize(plucker_pred[..., :3].float(), dim=-1, eps=1e-7)
    d_g = F.normalize(plucker_geom[..., :3].float(), dim=-1, eps=1e-7)
    ang = torch.acos((d_p * d_g).sum(dim=-1).clamp(-1.0, 1.0)) * (180.0 / math.pi)
    if valid_mask is not None and valid_mask.any():
        ang = ang[valid_mask.bool()]
    return float(ang.median().item()) if ang.numel() > 0 else 0.0


def _huber_weights_and_loss(res: torch.Tensor, delta: float) -> Tuple[torch.Tensor, torch.Tensor]:
    ar = res.abs()
    quad = ar <= delta
    loss = torch.where(quad, 0.5 * res * res, delta * (ar - 0.5 * delta))
    weight = torch.where(quad, torch.ones_like(ar), delta / ar.clamp_min(1e-7))
    return weight, loss


class TTBA(nn.Module):
    """Damped Levenberg-Marquardt SE(3) + per-frame scale refiner under Huber + p_stat."""

    def __init__(self, cfg: Optional[TTBAConfig] = None) -> None:
        super().__init__()
        self.cfg = cfg or TTBAConfig()

    @torch.no_grad()
    def _eval_residuals(
        self, rot: torch.Tensor, trans: torch.Tensor, log_scale: torch.Tensor, K: torch.Tensor,
        src_idx: torch.Tensor, dst_idx: torch.Tensor, uv_src: torch.Tensor, uv_dst: torch.Tensor,
        depth_src: torch.Tensor, depth_dst: torch.Tensor, stat_w: torch.Tensor,
        support_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        r_i, t_i, r_j, t_j = rot[src_idx], trans[src_idx], rot[dst_idx], trans[dst_idx]
        k_i, k_j = K[src_idx], K[dst_idx]
        fx_i, fy_i, cx_i, cy_i = k_i[:, 0, 0], k_i[:, 1, 1], k_i[:, 0, 2], k_i[:, 1, 2]
        fx_j, fy_j, cx_j, cy_j = k_j[:, 0, 0], k_j[:, 1, 1], k_j[:, 0, 2], k_j[:, 1, 2]

        ray_i = torch.stack([(uv_src[:, 0] - cx_i) / fx_i, (uv_src[:, 1] - cy_i) / fy_i, torch.ones_like(fx_i)], dim=-1)
        q_i = (depth_src * torch.exp(log_scale[src_idx])).unsqueeze(-1) * ray_i
        r_ji = r_j @ r_i.transpose(-1, -2)
        q_j = (r_ji @ (q_i - t_i).unsqueeze(-1)).squeeze(-1) + t_j

        valid_z = (q_j[:, 2] > self.cfg.min_depth) & (q_i[:, 2] > self.cfg.min_depth)
        m0 = (valid_z & (stat_w > 0.0)) if support_mask is None else support_mask
        cheirality_viol = m0 & (~valid_z)

        z_safe = q_j[:, 2].clamp_min(self.cfg.min_depth)
        r_u = fx_j * (q_j[:, 0] / z_safe) + cx_j - uv_dst[:, 0]
        r_v = fy_j * (q_j[:, 1] / z_safe) + cy_j - uv_dst[:, 1]
        r_z = torch.log(z_safe) - (torch.log(depth_dst.clamp_min(self.cfg.min_depth)) + log_scale[dst_idx])
        res = torch.stack([r_u, r_v, r_z], dim=-1)

        w_uv_h, l_uv = _huber_weights_and_loss(res[:, :2], self.cfg.huber_delta_px)
        w_z_h, l_z = _huber_weights_and_loss(res[:, 2:3], self.cfg.huber_delta_logz)
        base_w = (stat_w * m0.float()).unsqueeze(-1)
        inv_f_sq = (100.0 / (0.5 * (fx_j.abs() + fy_j.abs())).clamp_min(1.0)).pow(2).unsqueeze(-1)
        weights = torch.cat([base_w * self.cfg.reproj_weight * inv_f_sq * w_uv_h, base_w * self.cfg.depth_weight * w_z_h], dim=-1)
        cost = (base_w * self.cfg.reproj_weight * inv_f_sq * l_uv).sum() + (base_w * self.cfg.depth_weight * l_z).sum()
        if cheirality_viol.any():
            viol_depth = (self.cfg.min_depth - q_j[:, 2]).clamp_min(0.0) + (self.cfg.min_depth - q_i[:, 2]).clamp_min(0.0)
            cost = cost + (cheirality_viol.float() * (1e6 + 1e6 * viol_depth)).sum()
        return res, weights, cost, q_i, q_j, r_ji, cheirality_viol

    @torch.no_grad()
    def forward(
        self,
        rot_init: torch.Tensor,
        trans_init: torch.Tensor,
        K: torch.Tensor,
        src_idx: torch.Tensor,
        dst_idx: torch.Tensor,
        uv_src: torch.Tensor,
        uv_dst: torch.Tensor,
        depth_src: torch.Tensor,
        depth_dst: torch.Tensor,
        p_stat: torch.Tensor,
        sigma_depth: Optional[torch.Tensor] = None,
        log_scale_init: Optional[torch.Tensor] = None,
        trans_prior: Optional[torch.Tensor] = None,
        trans_prior_weight: float = 0.0,
        scale_prior: Optional[torch.Tensor] = None,
        scale_prior_weight: float = 0.0,
        fix_first_pose: bool = True,
        fix_first_scale: Optional[bool] = None,
        ray_yaw_disagreement_deg: Optional[float] = None,
        force_run: bool = False,
    ) -> TTBAOutput:
        t0 = time.perf_counter()
        orig_dtype, device, n_views = rot_init.dtype, rot_init.device, rot_init.shape[0]
        rot, trans, kf = rot_init.float().clone(), trans_init.float().clone(), K.float()
        log_scale = (
            torch.zeros(n_views, device=device) if log_scale_init is None else log_scale_init.float().clone()
        )
        yaw_dis = 0.0 if ray_yaw_disagreement_deg is None else float(ray_yaw_disagreement_deg)
        triggered = force_run or (ray_yaw_disagreement_deg is None) or (yaw_dis > self.cfg.trigger_yaw_deg)

        stat_w = p_stat.float().clamp(0.0, 1.0)
        if sigma_depth is not None:
            stat_w = stat_w * torch.exp(-0.5 * sigma_depth.float().pow(2).clamp_max(10.0))

        uv_s, uv_d, d_s, d_d = uv_src.float(), uv_dst.float(), depth_src.float(), depth_dst.float()
        res0, weights0, cost0, q_i0, q_j0, r_ji0, _ = self._eval_residuals(
            rot, trans, log_scale, kf, src_idx, dst_idx, uv_s, uv_d, d_s, d_d, stat_w
        )
        support_mask = (q_j0[:, 2] > self.cfg.min_depth) & (q_i0[:, 2] > self.cfg.min_depth) & (stat_w > 0.0)
        stat_mask = (stat_w > 0.25) & support_mask
        reproj_before = float((res0[stat_mask, :2] if stat_mask.any() else res0[:, :2]).norm(dim=-1).mean().item()) if res0.numel() else 0.0

        if not triggered or src_idx.numel() == 0:
            sc0 = float(res0[:, 2].abs().median().item()) if res0.numel() else 0.0
            return TTBAOutput(
                rot.to(orig_dtype), trans.to(orig_dtype), log_scale.to(orig_dtype),
                TTBADiagnostics(reproj_before, reproj_before, 0.0, sc0, 1.0, yaw_dis, triggered, False, 0, (time.perf_counter() - t0) * 1e3),
            )

        has_prior = (trans_prior is not None and trans_prior_weight > 0.0) or (scale_prior is not None and scale_prior_weight > 0.0)
        pin_scale0 = (not has_prior) if fix_first_scale is None else fix_first_scale
        fixed_mask = torch.zeros(7 * n_views, dtype=torch.bool, device=device)
        if fix_first_pose:
            fixed_mask[0:6] = True
        if pin_scale0:
            fixed_mask[6] = True

        tp = trans_prior.float() if trans_prior is not None else None
        sp = scale_prior.float() if scale_prior is not None else None

        def _prior_cost(t_c: torch.Tensor, a_c: torch.Tensor) -> torch.Tensor:
            c = torch.zeros((), device=device)
            if tp is not None and trans_prior_weight > 0.0:
                c = c + 0.5 * trans_prior_weight * (t_c - tp).pow(2).sum()
            if sp is not None and scale_prior_weight > 0.0:
                c = c + 0.5 * scale_prior_weight * (a_c - sp).pow(2).sum()
            return c

        init_total_cost = cost0 + _prior_cost(trans, log_scale)
        cur_cost, lam, pose_cond, steps_run, accepted_steps = init_total_cost, self.cfg.init_damping, 1.0, 0, 0
        last_h_damped: Optional[torch.Tensor] = None
        fx_j, fy_j = kf[dst_idx, 0, 0], kf[dst_idx, 1, 1]
        eye3 = torch.eye(3, device=device).unsqueeze(0)
        v_idx = torch.arange(n_views, device=device)
        cur_eval = (res0, weights0, q_i0, q_j0, r_ji0)
        need_relinearize = True
        hess = torch.empty((7 * n_views, 7 * n_views), device=device)
        grad = torch.empty((7 * n_views,), device=device)

        for step in range(self.cfg.num_steps):
            steps_run = step + 1
            if need_relinearize:
                res, weights, q_i, q_j, r_ji = cur_eval
                inv_z = 1.0 / q_j[:, 2].clamp_min(self.cfg.min_depth)
                inv_z2, zeros = inv_z * inv_z, torch.zeros_like(inv_z)
                m = src_idx.shape[0]

                dr_dqj = torch.stack(
                    [
                        torch.stack([fx_j * inv_z, zeros, -fx_j * q_j[:, 0] * inv_z2], dim=-1),
                        torch.stack([zeros, fy_j * inv_z, -fy_j * q_j[:, 1] * inv_z2], dim=-1),
                        torch.stack([zeros, zeros, inv_z], dim=-1),
                    ],
                    dim=-2,
                )
                j_src = dr_dqj @ torch.cat([r_ji @ skew_symmetric(q_i), -r_ji, r_ji @ q_i.unsqueeze(-1)], dim=-1)
                j_dst = dr_dqj @ torch.cat([-skew_symmetric(q_j), eye3.expand(m, 3, 3), torch.zeros((m, 3, 1), device=device)], dim=-1)
                j_dst[:, 2, 6] = -1.0

                w_res, wj_src, wj_dst = weights * res, weights.unsqueeze(-1) * j_src, weights.unsqueeze(-1) * j_dst
                h_blocks = torch.zeros((n_views * n_views, 7, 7), device=device)
                g_vec = torch.zeros((n_views, 7), device=device)
                h_sd = j_src.transpose(-1, -2) @ wj_dst
                h_blocks.index_add_(0, src_idx * n_views + src_idx, j_src.transpose(-1, -2) @ wj_src)
                h_blocks.index_add_(0, dst_idx * n_views + dst_idx, j_dst.transpose(-1, -2) @ wj_dst)
                h_blocks.index_add_(0, src_idx * n_views + dst_idx, h_sd)
                h_blocks.index_add_(0, dst_idx * n_views + src_idx, h_sd.transpose(-1, -2))
                g_vec.index_add_(0, src_idx, (j_src.transpose(-1, -2) @ w_res.unsqueeze(-1)).squeeze(-1))
                g_vec.index_add_(0, dst_idx, (j_dst.transpose(-1, -2) @ w_res.unsqueeze(-1)).squeeze(-1))

                if tp is not None and trans_prior_weight > 0.0:
                    j_t = torch.cat([-skew_symmetric(trans), eye3.expand(n_views, 3, 3)], dim=-1)  # [N, 3, 6]
                    h_blocks[v_idx * n_views + v_idx, :6, :6] += trans_prior_weight * (j_t.transpose(-1, -2) @ j_t)
                    g_vec[:, :6] += trans_prior_weight * (j_t.transpose(-1, -2) @ (trans - tp).unsqueeze(-1)).squeeze(-1)
                if sp is not None and scale_prior_weight > 0.0:
                    h_blocks[v_idx * n_views + v_idx, 6, 6] += scale_prior_weight
                    g_vec[:, 6] += scale_prior_weight * (log_scale - sp)

                hess = h_blocks.view(n_views, n_views, 7, 7).permute(0, 2, 1, 3).reshape(7 * n_views, 7 * n_views)
                grad = g_vec.reshape(7 * n_views)
                if fixed_mask.any():
                    hess[fixed_mask, :], hess[:, fixed_mask] = 0.0, 0.0
                    hess[fixed_mask, fixed_mask], grad[fixed_mask] = 1.0, 0.0
                need_relinearize = False

            h_damped = hess + torch.diag(lam * hess.diagonal().clamp_min(1e-4))
            last_h_damped = h_damped

            try:
                dx = torch.linalg.solve(h_damped, -grad)
            except RuntimeError:
                lam = min(lam * 10.0, self.cfg.max_damping)
                continue

            dx_v = dx.view(n_views, 7)
            d_rot = so3_exp(dx_v[:, 0:3].clamp(-0.5, 0.5))
            r_cand = d_rot @ rot
            t_cand = (d_rot @ trans.unsqueeze(-1)).squeeze(-1) + dx_v[:, 3:6].clamp(-2.0, 2.0)
            s_cand = (log_scale + dx_v[:, 6].clamp(-1.0, 1.0)).clamp(-3.0, 3.0)

            res_c, weights_c, d_cost, q_ic, q_jc, r_jic, cand_viol = self._eval_residuals(
                r_cand, t_cand, s_cand, kf, src_idx, dst_idx, uv_s, uv_d, d_s, d_d, stat_w, support_mask=support_mask
            )
            cand_cost = d_cost + _prior_cost(t_cand, s_cand)
            if (not cand_viol.any()) and (cand_cost < cur_cost):
                rot, trans, log_scale, cur_cost = r_cand, t_cand, s_cand, cand_cost
                cur_eval = (res_c, weights_c, q_ic, q_jc, r_jic)
                need_relinearize = True
                accepted_steps += 1
                lam = max(lam * 0.3, self.cfg.min_damping)
                if dx.norm().item() < 1e-5:
                    break
            else:
                lam = min(lam * 5.0, self.cfg.max_damping)

        if last_h_damped is not None:
            try:
                sub_h = last_h_damped[~fixed_mask][:, ~fixed_mask]
                if sub_h.numel() > 0:
                    sv = torch.linalg.svdvals(sub_h)
                    pose_cond = float((sv[0] / sv[-1].clamp_min(1e-12)).item())
            except RuntimeError:
                pose_cond = float("inf")

        res_f = cur_eval[0]
        final_viol = torch.zeros((), dtype=torch.bool, device=device)
        reproj_after = float((res_f[stat_mask, :2] if stat_mask.any() else res_f[:, :2]).norm(dim=-1).mean().item())
        scale_cons = float((res_f[stat_mask, 2] if stat_mask.any() else res_f[:, 2]).abs().median().item())

        k_i, k_j = kf[src_idx], kf[dst_idx]
        ray_i_c = F.normalize(torch.stack([(uv_s[:, 0] - k_i[:, 0, 2]) / k_i[:, 0, 0], (uv_s[:, 1] - k_i[:, 1, 2]) / k_i[:, 1, 1], torch.ones_like(uv_s[:, 0])], dim=-1), dim=-1)
        ray_j_c = F.normalize(torch.stack([(uv_d[:, 0] - k_j[:, 0, 2]) / k_j[:, 0, 0], (uv_d[:, 1] - k_j[:, 1, 2]) / k_j[:, 1, 1], torch.ones_like(uv_d[:, 0])], dim=-1), dim=-1)
        ray_i_w = (rot[src_idx].transpose(-1, -2) @ ray_i_c.unsqueeze(-1)).squeeze(-1)
        ray_j_w = (rot[dst_idx].transpose(-1, -2) @ ray_j_c.unsqueeze(-1)).squeeze(-1)
        par = torch.acos((ray_i_w * ray_j_w).sum(dim=-1).clamp(-1.0, 1.0)) * (180.0 / math.pi)
        parallax_deg = float((par[stat_mask] if stat_mask.any() else par).mean().item())

        reproj_improved = (reproj_before >= 1e-4) and (
            reproj_after <= reproj_before * (1.0 - self.cfg.min_improvement_ratio)
        )
        cost_improved = (reproj_before < 1e-4) and (
            float(cur_cost.item()) <= float(init_total_cost.item()) * (1.0 - self.cfg.min_improvement_ratio)
        )
        committed = bool(
            (not final_viol.any())
            and (force_run or ((accepted_steps > 0) and (reproj_improved or cost_improved)))
        )
        if not committed:
            rot, trans = rot_init.float(), trans_init.float()
            log_scale = torch.zeros(n_views, device=device) if log_scale_init is None else log_scale_init.float()
            reproj_after = reproj_before

        return TTBAOutput(
            rot.to(orig_dtype), trans.to(orig_dtype), log_scale.to(orig_dtype),
            TTBADiagnostics(
                reproj_before, reproj_after, parallax_deg, scale_cons, pose_cond,
                yaw_dis, triggered, committed, steps_run, (time.perf_counter() - t0) * 1e3,
            ),
        )
