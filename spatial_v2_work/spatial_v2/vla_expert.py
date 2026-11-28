"""300M-scalable System-1 SE(3) FlowExpert VLA action head (<18 ms/chunk)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import FlowExpertConfig
from .epi_adapter import RMSNorm
from .geo_heads import matrix_to_rotation_6d


def _sinusoidal_time_embedding(t: torch.Tensor, freqs: torch.Tensor, dim: int) -> torch.Tensor:
    args = t.float().unsqueeze(-1) * freqs.unsqueeze(0) * 1000.0
    emb = torch.cat([torch.sin(args), torch.cos(args)], dim=-1)
    return (F.pad(emb, (0, 1)) if dim % 2 == 1 else emb).to(t.dtype)


class _CrossAttention(nn.Module):
    def __init__(self, d_model: int, num_heads: int) -> None:
        super().__init__()
        self.num_heads, self.head_dim = num_heads, d_model // num_heads
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.kv_proj = nn.Linear(d_model, 2 * d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)

    def project_kv(self, memory: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        bsz, mem_len, _ = memory.shape
        k, v = self.kv_proj(memory).view(bsz, mem_len, 2, self.num_heads, self.head_dim).unbind(dim=2)
        return k.transpose(1, 2), v.transpose(1, 2)

    def forward(
        self, x: torch.Tensor, kv_cache: Tuple[torch.Tensor, torch.Tensor], memory_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        bsz, seqlen, dim = x.shape
        q = self.q_proj(x).view(bsz, seqlen, self.num_heads, self.head_dim).transpose(1, 2)
        attn_mask = memory_mask[:, None, None, :] if memory_mask is not None else None
        out = F.scaled_dot_product_attention(q, kv_cache[0], kv_cache[1], attn_mask=attn_mask, is_causal=False)
        return self.out_proj(out.transpose(1, 2).contiguous().view(bsz, seqlen, dim))


class _FlowExpertBlock(nn.Module):
    def __init__(self, d_model: int, num_heads: int, mlp_ratio: float = 4.0) -> None:
        super().__init__()
        self.num_heads, self.head_dim = num_heads, d_model // num_heads
        self.norm_sa = RMSNorm(d_model)
        self.sa_qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.sa_out = nn.Linear(d_model, d_model, bias=False)
        self.norm_ca = RMSNorm(d_model)
        self.cross_attn = _CrossAttention(d_model, num_heads)
        self.ca_gate = nn.Parameter(torch.zeros(d_model))  # zero-init residual conditioning gate
        self.norm_ffn = RMSNorm(d_model)
        hid = int(d_model * mlp_ratio)
        self.w12 = nn.Linear(d_model, 2 * hid, bias=False)
        self.w3 = nn.Linear(hid, d_model, bias=False)
        self.ada_mod = nn.Linear(d_model, 4 * d_model)
        nn.init.zeros_(self.ada_mod.weight)
        nn.init.zeros_(self.ada_mod.bias)

    def forward(
        self, x: torch.Tensor, t_emb: torch.Tensor, kv_cache: Tuple[torch.Tensor, torch.Tensor],
        memory_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        bsz, seqlen, dim = x.shape
        s_sa, b_sa, s_ffn, b_ffn = self.ada_mod(t_emb).unsqueeze(1).chunk(4, dim=-1)
        h = self.norm_sa(x) * (1.0 + s_sa) + b_sa
        q, k, v = self.sa_qkv(h).view(bsz, seqlen, 3, self.num_heads, self.head_dim).unbind(dim=2)
        sa = F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2), is_causal=False)
        x = x + self.sa_out(sa.transpose(1, 2).contiguous().view(bsz, seqlen, dim))
        x = x + self.ca_gate.to(x.dtype) * self.cross_attn(self.norm_ca(x), kv_cache, memory_mask=memory_mask)
        u, g = self.w12(self.norm_ffn(x) * (1.0 + s_ffn) + b_ffn).chunk(2, dim=-1)
        return x + self.w3(F.silu(g) * u)


@dataclass
class FlowMemoryCache:
    layer_kvs: List[Tuple[torch.Tensor, torch.Tensor]]
    memory_mask: Optional[torch.Tensor]


class FlowExpert(nn.Module):
    """System-1 SE(3) Flow-Matching Action Expert reading mid-trunk 3D + 4D flow taps."""

    def __init__(self, cfg: FlowExpertConfig, lm_hidden_size: int) -> None:
        super().__init__()
        self.cfg = cfg
        d = cfg.d_model
        self.tap_projs = nn.ModuleDict(
            {str(l): nn.Sequential(RMSNorm(lm_hidden_size), nn.Linear(lm_hidden_size, d, bias=False)) for l in cfg.tap_layers}
        )
        self.tap_ids = nn.ParameterDict({str(l): nn.Parameter(torch.zeros(1, 1, d)) for l in cfg.tap_layers})
        self.geo_proj = nn.Linear(cfg.geo_token_dim, d)
        self.mem_norm = RMSNorm(d)
        self.proprio_proj = nn.Sequential(nn.Linear(cfg.proprio_dim, d), nn.SiLU(), nn.Linear(d, d))
        self.subgoal_proj = nn.Sequential(nn.Linear(cfg.subgoal_dim, d), nn.SiLU(), nn.Linear(d, d))
        self.subgoal_gate = nn.Parameter(torch.zeros(d))  # zero-init ONLY the multiplicative gate
        self.action_in = nn.Linear(cfg.action_dim, d)
        self.action_pos = nn.Parameter(torch.randn(1, cfg.chunk_size, d) * 0.02)
        half = d // 2
        self.register_buffer(
            "time_freqs",
            torch.exp(-math.log(10000.0) * torch.arange(half, dtype=torch.float32) / max(half - 1, 1)),
            persistent=False,
        )
        self.time_mlp = nn.Sequential(nn.Linear(d, d), nn.SiLU(), nn.Linear(d, d))
        self.blocks = nn.ModuleList([_FlowExpertBlock(d, cfg.num_heads, cfg.mlp_ratio) for _ in range(cfg.num_layers)])
        self.out_norm = RMSNorm(d)
        self.action_out = nn.Linear(d, cfg.action_dim)

    @staticmethod
    def _encode_subgoal(t_goal: torch.Tensor) -> torch.Tensor:
        if t_goal.ndim == 3 and t_goal.shape[-2:] == (4, 4):
            return torch.cat([matrix_to_rotation_6d(t_goal[:, :3, :3]), t_goal[:, :3, 3]], dim=-1)
        return t_goal

    def precompute_memory(
        self,
        backbone_taps: Dict[int, torch.Tensor],
        geo_tokens: Optional[torch.Tensor] = None,
        memory_mask: Optional[torch.Tensor] = None,
        detach_backbone: Optional[bool] = None,
    ) -> FlowMemoryCache:
        do_detach = self.cfg.detach_backbone if detach_backbone is None else detach_backbone
        parts: List[torch.Tensor] = []
        for l_str, proj in self.tap_projs.items():
            lid = int(l_str)
            if lid not in backbone_taps:
                continue
            feat = backbone_taps[lid].detach() if do_detach else backbone_taps[lid]
            if feat.ndim > 3:
                feat = feat.reshape(feat.shape[0], -1, feat.shape[-1])
            parts.append(proj(feat) + self.tap_ids[l_str].to(feat.dtype))
        if geo_tokens is not None:
            g = geo_tokens.detach() if do_detach else geo_tokens
            if g.ndim > 3:
                g = g.reshape(g.shape[0], -1, g.shape[-1])
            parts.append(self.geo_proj(g.to(self.geo_proj.weight.dtype)))
        if not parts:
            raise ValueError("FlowExpert requires at least one backbone tap or geo_tokens tensor")
        memory = self.mem_norm(torch.cat(parts, dim=1))
        return FlowMemoryCache([blk.cross_attn.project_kv(memory) for blk in self.blocks], memory_mask)

    def predict_velocity(
        self,
        noisy_actions: torch.Tensor,
        flow_t: torch.Tensor,
        proprio: torch.Tensor,
        memory_cache: FlowMemoryCache,
        t_goal: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        t_emb = self.time_mlp(_sinusoidal_time_embedding(flow_t, self.time_freqs, self.cfg.d_model))
        prop_tok = self.proprio_proj(proprio).unsqueeze(1)
        if t_goal is not None:
            g_vec = self._encode_subgoal(t_goal).to(proprio.dtype)
            prop_tok = prop_tok + (self.subgoal_gate.to(proprio.dtype) * self.subgoal_proj(g_vec)).unsqueeze(1)
        act_tok = self.action_in(noisy_actions) + self.action_pos[:, : noisy_actions.shape[1], :].to(noisy_actions.dtype)
        x = torch.cat([prop_tok, act_tok], dim=1)
        for blk, kv in zip(self.blocks, memory_cache.layer_kvs):
            x = blk(x, t_emb=t_emb, kv_cache=kv, memory_mask=memory_cache.memory_mask)
        return self.action_out(self.out_norm(x[:, 1:, :]))

    def compute_loss(
        self,
        actions_gt: torch.Tensor,
        proprio: torch.Tensor,
        backbone_taps: Dict[int, torch.Tensor],
        geo_tokens: Optional[torch.Tensor] = None,
        t_goal: Optional[torch.Tensor] = None,
        memory_mask: Optional[torch.Tensor] = None,
        detach_backbone: Optional[bool] = None,
    ) -> torch.Tensor:
        bsz = actions_gt.shape[0]
        flow_t = (
            torch.distributions.Beta(self.cfg.beta_alpha, self.cfg.beta_beta)
            .sample((bsz,))
            .to(device=actions_gt.device, dtype=torch.float32)
            .clamp(1e-3, 1.0 - 1e-3)
        )
        noise = torch.randn_like(actions_gt)
        t_v = flow_t.to(actions_gt.dtype).view(bsz, 1, 1)
        cache = self.precompute_memory(backbone_taps, geo_tokens, memory_mask, detach_backbone)
        pred_v = self.predict_velocity((1.0 - t_v) * noise + t_v * actions_gt, flow_t.to(actions_gt.dtype), proprio, cache, t_goal)
        return F.mse_loss(pred_v.float(), (actions_gt - noise).float())

    @torch.no_grad()
    def sample_actions(
        self,
        proprio: torch.Tensor,
        backbone_taps: Dict[int, torch.Tensor],
        geo_tokens: Optional[torch.Tensor] = None,
        t_goal: Optional[torch.Tensor] = None,
        memory_mask: Optional[torch.Tensor] = None,
        num_steps: Optional[int] = None,
        noise: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        steps = self.cfg.default_ode_steps if num_steps is None else num_steps
        bsz = proprio.shape[0]
        x = (
            torch.randn((bsz, self.cfg.chunk_size, self.cfg.action_dim), device=proprio.device, dtype=proprio.dtype)
            if noise is None
            else noise.clone()
        )
        cache = self.precompute_memory(backbone_taps, geo_tokens, memory_mask)
        dt = 1.0 / float(steps)
        for s in range(steps):
            t_cur = torch.full((bsz,), s * dt, device=proprio.device, dtype=proprio.dtype)
            x = x + dt * self.predict_velocity(x, t_cur, proprio, cache, t_goal)
        return x
