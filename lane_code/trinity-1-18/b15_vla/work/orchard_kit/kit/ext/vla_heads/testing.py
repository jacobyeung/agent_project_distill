"""CPU fixtures: the tiny native fp32 Qwen3.5 student, stub batches and synthetic cond tensors of the
real shapes. Used by tests/ and examples/; nothing here loads checkpoint weights.
"""
import torch

from .config import VLAConfig


def tiny_qwen35(seed=31):
    """The tree's CPU fixture (integ_v3/scripts/acceptance_cpu_e2e.py): real Qwen3.5-9B config with
    2 hybrid LM layers (linear + full attention) of width 32 and a 3-block vision tower of width 32.
    Vocabulary and special-token ids stay the real ones (248,320 rows)."""
    from transformers import Qwen3_5Config
    try:
        from student_pilot.students import model_class
        klass = model_class('qwen35')
    except ImportError:
        from transformers import Qwen3_5ForConditionalGeneration as klass
    config = Qwen3_5Config()
    text = config.text_config
    text.hidden_size = 32; text.intermediate_size = 64; text.num_hidden_layers = 2
    text.num_attention_heads = 4; text.num_key_value_heads = 2; text.head_dim = 8
    text.layer_types = ['linear_attention', 'full_attention']; text.linear_key_head_dim = 4
    text.linear_value_head_dim = 4; text.linear_num_key_heads = 4; text.linear_num_value_heads = 4
    text.rope_parameters = dict(rope_type='default', rope_theta=10000., mrope_section=[1, 1, 2], partial_rotary_factor=1.)
    visual = config.vision_config
    visual.depth = 3; visual.hidden_size = 32; visual.intermediate_size = 64; visual.num_heads = 4
    visual.out_hidden_size = 32; visual.num_position_embeddings = 16
    for item in (config, text, visual):
        item._attn_implementation = 'sdpa'
    torch.manual_seed(seed)
    return klass(config).float()


def student_batch(model, b=2, lengths=(5, 3), grid=(1, 4, 4), views=2, seed=0, pad='right'):
    """Processor-shaped rows: [text] + per view <vision_start> image tokens <vision_end> + [text], with
    rows of different text length padded on the right (or left). Two camera views per row (agent and
    wrist), each an image of grid (t, h, w) patches."""
    cfg = model.config
    vis = cfg.vision_config
    g = torch.Generator().manual_seed(seed)
    per_image = grid[0] * grid[1] * grid[2] // vis.spatial_merge_size ** 2
    patch_dim = vis.in_channels * vis.temporal_patch_size * vis.patch_size ** 2
    rows = []
    for i in range(b):
        n = lengths[i % len(lengths)]
        ids = torch.randint(100, 5000, (n,), generator=g).tolist()
        for _ in range(views):
            ids += [cfg.vision_start_token_id] + [cfg.image_token_id] * per_image + [cfg.vision_end_token_id]
        ids += torch.randint(100, 5000, (2,), generator=g).tolist()
        rows.append(ids)
    t = max(map(len, rows))
    pad_id = 248044
    input_ids = torch.full((b, t), pad_id)
    mask = torch.zeros(b, t, dtype=torch.long)
    for i, ids in enumerate(rows):
        sl = slice(0, len(ids)) if pad == 'right' else slice(t - len(ids), t)
        input_ids[i, sl] = torch.tensor(ids)
        mask[i, sl] = 1
    n_img = b * views
    pixels = torch.randn(n_img * grid[0] * grid[1] * grid[2], patch_dim, generator=g)
    return dict(input_ids=input_ids, attention_mask=mask, pixel_values=pixels,
                image_grid_thw=torch.tensor([list(grid)] * n_img))


def stub_batch(b=4, t=6, vocab=64, seed=0):
    g = torch.Generator().manual_seed(seed)
    ids = torch.randint(0, vocab, (b, t), generator=g)
    mask = torch.ones(b, t, dtype=torch.long)
    if b > 1:
        mask[1, t - 2:] = 0  # one right-padded row
    return dict(input_ids=ids, attention_mask=mask)


def synthetic_where(b, entities=2, seed=0):
    """Provider records of the 18-column layout (cond.py; vla_where types.py), row 1's place entity
    invalid (an all-zero row)."""
    g = torch.Generator().manual_seed(seed)
    w = torch.zeros(b, entities, 18)
    w[..., 0] = torch.rand(b, entities, generator=g) * 0.5 + 0.5
    w[..., 1] = 1.0
    w[..., 2:6] = torch.rand(b, entities, 4, generator=g) * 1.4 - 0.2
    w[..., 6:12] = torch.randn(b, entities, 6, generator=g) * 0.3
    w[..., 12:15] = torch.rand(b, entities, 3, generator=g) * 0.1 + 0.02
    w[..., 15] = 1.0
    if b > 1 and entities > 1:
        w[1, 1] = 0.0
    return w


def synthetic_cond(cfg, b, views=2, seed=0, patch=True, readouts=False, g3t_hw=37):
    """Raw cond dict of the contract in cond.py, with the real channel widths."""
    g = torch.Generator().manual_seed(seed)
    raw = {}
    if cfg.cond in ('g3t_tokens', 'both'):
        raw['g3t_cam'] = torch.randn(b, views, cfg.g3t_cam_dim, generator=g)
        if patch and cfg.g3t_patch_grid:
            raw['g3t_patch'] = torch.randn(b, views, g3t_hw, g3t_hw, cfg.g3t_patch_dim, generator=g)
        raw['g3t_mask'] = torch.ones(b, views, dtype=torch.bool)
    if cfg.cond in ('spatial_readouts', 'both'):
        raw['where'] = synthetic_where(b, cfg.where_entities, seed)
        if readouts:
            q = torch.nn.functional.normalize(torch.randn(b, views, 4, generator=g), dim=-1)
            raw['pose9'] = torch.cat([torch.randn(b, views, 3, generator=g), q, torch.full((b, views, 2), 1.2)], -1)
            raw['gravity_up'] = torch.nn.functional.normalize(torch.randn(b, 3, generator=g), dim=-1)
            raw['step_scale'] = torch.rand(b, 1, generator=g) + 0.1
            raw['depth_grid'] = torch.rand(b, views, 51, 51, generator=g) * 3 + 0.2
    return raw


def full_batch(cfg, base, b, seed=0):
    """base inputs + proprio, cond, actions and an action mask with one padded tail."""
    g = torch.Generator().manual_seed(seed + 1)
    batch = dict(base)
    if cfg.proprio_dim:
        batch['proprio'] = torch.randn(b, cfg.proprio_dim, generator=g).clamp(-1, 1)
    if cfg.cond != 'none':
        batch['cond'] = synthetic_cond(cfg, b, seed=seed)
    batch['actions'] = torch.rand(b, cfg.chunk, cfg.action_dim, generator=g) * 2 - 1
    mask = torch.ones(b, cfg.chunk, dtype=torch.bool)
    mask[0, -2:] = False
    batch['action_mask'] = mask
    return batch


def small_config(head, **kw):
    """Config sized for CPU tests on a width-32, 2-layer backbone (flow taps [1, -1])."""
    base = dict(head=head, hidden_size=32, action_dim=7, chunk=4, proprio_dim=8, cond_dim=16,
                reg_hidden=32, reg_cond_heads=4, flow_width=32, flow_heads=4, flow_layers=2,
                flow_steps=4, ddpm_train_steps=20, readout_hidden=16, tok_bins=32, tok_codec='bins',
                tok_vocab=300, tok_dct_clip=63, tok_max_tokens=48, where_dropout=0.0)
    if head in ('flow', 'generative') and 'taps' not in kw:
        base['taps'] = [1, -1]
    base.update(kw)
    return VLAConfig(**base)


def build(cfg, backbone='stub', model=None, **kw):
    """A VLAPolicy on the stub (vocab 64) or on a tiny student `model`, with the config's taps."""
    from .adapters import StubBackbone, StudentAdapter
    from .policy import VLAPolicy
    bb = StubBackbone.for_config(cfg) if backbone == 'stub' else StudentAdapter.for_config(model, cfg)
    return VLAPolicy(cfg, bb, **kw)
