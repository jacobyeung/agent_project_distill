"""One flat configuration for every head, codec, conditioning mode and backbone adapter.

Every key has a default; `VLAConfig.from_dict` rejects unknown keys. `VLAConfig.from_spec` reads the
nested run spec of the design record (VLA_ACTION_HEAD_DESIGN_20261111 section 5.3) and maps it onto
these keys; spec sections that do not configure the head (backbone path, optim, train, data, nav)
are returned untouched for the trainer.
"""
from dataclasses import asdict, dataclass, field, fields
import hashlib
import json

HEADS = ('regression', 'flow', 'tokens')
HEAD_ALIASES = {'generative': 'flow', 'diffusion': 'flow', 'discrete': 'tokens'}
CONDS = ('none', 'g3t_tokens', 'spatial_readouts', 'both')
OBJECTIVES = ('flow', 'ddpm')
TIME_DISTS = ('beta', 'uniform', 'logit_normal')
CODECS = ('fast', 'bins', 'dct', 'digits', 'nav')
TRAIN_MODES = ('full', 'lora', 'frozen')
INJECT = ('head', 'lm')
WHERE_FEATURES = 18


@dataclass
class VLAConfig:
    # shared
    head: str = 'regression'
    action_dim: int = 7
    chunk: int = 8
    hidden_size: int = 4096
    proprio_dim: int = 8
    proprio_inject: str = 'head'
    taps: list = field(default_factory=list)       # LM layers read; [] = head default; -1 = last
    tap_norm: bool = False                          # final norm on taps below the last layer
    detach_backbone: bool = False                   # flow: no expert gradient into the LM
    lm_token_loss: str = 'none'                     # 'none' | a codec: the LM also writes the chunk
    lm_token_weight: float = 1.0
    # conditioning
    cond: str = 'none'
    cond_dim: int = 1024
    cond_inject: str = 'head'
    where_entities: int = 2                         # target, place
    where_features: int = WHERE_FEATURES
    where_dropout: float = 0.2                      # training: drop the where input for this share of rows
    max_views: int = 32
    g3t_cam_dim: int = 2058
    g3t_patch_dim: int = 2048
    g3t_patch_grid: int = 0                         # 0 = camera tokens only; g = g x g pooled patch tokens per view
    readout_depth_grid: int = 4
    readout_hidden: int = 256
    # (a) regression
    reg_hidden: int = 1024
    reg_blocks: int = 2
    reg_block: str = 'mlp2'                          # 'mlp2' = LN-Linear-act-Linear; 'oft' = LN-Linear-act (StarVLA/OFT)
    reg_act: str = 'gelu'
    reg_input_act: bool = False                      # activation after the first projection (OFT: true)
    reg_final_norm: bool = False                     # LayerNorm before the output layer (OFT: true)
    reg_cond_heads: int = 8
    # (b) flow / diffusion expert
    flow_layers: int = 8
    flow_width: int = 1024
    flow_heads: int = 16
    flow_mlp_ratio: float = 4.0
    flow_objective: str = 'flow'
    flow_time_dist: str = 'beta'
    flow_steps: int = 10
    flow_time_cond: str = 'concat'                   # 'concat' = MLP([W_a x ; phi(tau)]) (pi0); 'adaln'
    flow_dropout: float = 0.0
    ddpm_train_steps: int = 100
    ddpm_clip_sample: bool = True
    ddpm_prediction: str = 'epsilon'                # 'epsilon' | 'sample' (x0, as Diffusion Policy's option)
    # (c) tokens
    tok_codec: str = 'fast'
    tok_vocab: int = 1024                            # FAST BPE vocabulary
    tok_bins: int = 256
    tok_dct_scale: float = 10.0
    tok_dct_keep: int = 0                            # 0 = all chunk coefficients
    tok_dct_clip: int = 127
    tok_max_tokens: int = 64                         # decode cap for variable-length codecs
    tok_ids: str = 'append'                          # 'append' new rows | path to a reserved-id JSON
    tok_ce: str = 'full'                             # 'full' vocabulary | 'restricted' to codec ids
    tok_codec_path: str = ''                         # fitted codec state (FAST BPE JSON)
    # backbone adapter
    train_mode: str = 'full'
    train_vision: bool = False
    lora_rank: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    lora_targets: list = field(default_factory=lambda: [
        'q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj',
        'in_proj_qkv', 'in_proj_z', 'out_proj'])

    def __post_init__(self):
        self.head = HEAD_ALIASES.get(self.head, self.head)
        checks = (('head', HEADS), ('cond', CONDS), ('flow_objective', OBJECTIVES), ('flow_time_dist', TIME_DISTS),
                  ('tok_codec', CODECS), ('train_mode', TRAIN_MODES), ('cond_inject', INJECT),
                  ('proprio_inject', INJECT), ('tok_ce', ('full', 'restricted')), ('reg_block', ('mlp2', 'oft')),
                  ('reg_act', ('gelu', 'relu')), ('flow_time_cond', ('concat', 'adaln')),
                  ('lm_token_loss', ('none',) + CODECS), ('ddpm_prediction', ('epsilon', 'sample')))
        for key, allowed in checks:
            if getattr(self, key) not in allowed:
                raise ValueError(f'{key}={getattr(self, key)!r}; choose one of {allowed}')
        for key in ('action_dim', 'chunk', 'hidden_size', 'cond_dim', 'reg_hidden', 'flow_layers', 'flow_width',
                    'flow_heads', 'flow_steps', 'ddpm_train_steps', 'tok_vocab', 'tok_bins', 'max_views',
                    'readout_depth_grid', 'where_entities', 'tok_max_tokens'):
            if type(getattr(self, key)) is not int or getattr(self, key) < 1:
                raise ValueError(f'{key} must be a positive int')
        if self.proprio_dim < 0 or self.reg_blocks < 0 or self.g3t_patch_grid < 0:
            raise ValueError('proprio_dim, reg_blocks and g3t_patch_grid must be >= 0')
        if self.where_features != WHERE_FEATURES:
            raise ValueError(f'where_features is fixed at {WHERE_FEATURES} (the provider record)')
        if self.flow_width % self.flow_heads or self.reg_hidden % self.reg_cond_heads:
            raise ValueError('widths must divide by their head counts')
        if self.flow_objective == 'ddpm' and self.flow_steps > self.ddpm_train_steps:
            raise ValueError('DDIM flow_steps cannot exceed ddpm_train_steps')
        if not 0 <= self.tok_dct_keep <= self.chunk:
            raise ValueError('tok_dct_keep must be in [0, chunk]')
        if not 0.0 <= self.where_dropout < 1.0:
            raise ValueError('where_dropout must be in [0, 1)')
        if self.detach_backbone and self.head != 'flow':
            raise ValueError('detach_backbone applies to the flow head only')
        if self.lm_token_loss != 'none' and self.head != 'flow':
            raise ValueError('lm_token_loss trains the LM beside the flow head; the tokens head already is one')
        if self.head == 'tokens':
            # The LM writes the tokens, so it must also read cond and proprio: 'lm' is the only option.
            self.cond_inject = self.proprio_inject = 'lm'
        if not self.taps:
            self.taps = [16, -1] if self.head == 'flow' else [-1]
        self.taps = [int(t) for t in self.taps]
        if any(t == 0 or t < -1 for t in self.taps) or len(set(self.taps)) != len(self.taps):
            raise ValueError('taps are distinct layer numbers >= 1, or -1 for the last layer')
        if self.head in ('regression', 'tokens') and self.taps[-1] != -1:
            raise ValueError('regression and tokens heads read the last layer: taps must end with -1')

    @property
    def token_codec(self):
        """The codec the LM writes: the tokens head's, or the flow head's auxiliary token loss."""
        return self.tok_codec if self.head == 'tokens' else (None if self.lm_token_loss == 'none' else self.lm_token_loss)

    @classmethod
    def from_dict(cls, value):
        names = {f.name for f in fields(cls)}
        unknown = set(value) - names
        if unknown:
            raise ValueError(f'Unknown config keys: {sorted(unknown)}')
        return cls(**value)

    @classmethod
    def from_spec(cls, spec, **overrides):
        """Design-record run spec (dict with a top-level `vla`, or its body) -> (VLAConfig, rest).
        `rest` holds the sections the trainer reads (backbone, input, optim, train, data, nav, where)."""
        vla = spec.get('vla', spec)
        head = vla.get('head', {})
        kind = head.get('type', 'regression')
        out = dict(head=kind, chunk=head.get('chunk', 8), action_dim=head.get('action_dim', 7))
        reg = head.get('regression', {})
        if reg.get('loss', 'l1') != 'l1':
            raise ValueError('The regression head trains with L1 only')
        out.update({k2: reg[k1] for k1, k2 in (('hidden', 'reg_hidden'), ('blocks', 'reg_blocks')) if k1 in reg})
        flow = head.get('flow', {})
        time_dist = flow.get('time_dist', 'beta_1.5_1')
        out.update({k2: flow[k1] for k1, k2 in (('layers', 'flow_layers'), ('width', 'flow_width'), ('heads', 'flow_heads'),
                                                ('objective', 'flow_objective'), ('steps', 'flow_steps')) if k1 in flow})
        out['flow_time_dist'] = 'beta' if time_dist == 'beta_1.5_1' else time_dist
        if kind == 'flow' and 'taps' in flow:
            out['taps'] = list(flow['taps'])
        tok = head.get('tokens', {})
        out.update({k2: tok[k1] for k1, k2 in (('codec', 'tok_codec'), ('vocab', 'tok_vocab'), ('bins', 'tok_bins')) if k1 in tok})
        out['cond'] = vla.get('cond', 'none')
        where = vla.get('where', {})
        if 'dropout' in where:
            out['where_dropout'] = where['dropout']
        out['detach_backbone'] = bool(vla.get('detach_backbone', False))
        out['lm_token_loss'] = vla.get('lm_token_loss', 'none')
        backbone = vla.get('backbone', {})
        if 'train' in backbone:
            out['train_mode'] = backbone['train']
        out['train_vision'] = backbone.get('vision', 'frozen') != 'frozen'
        proprio = vla.get('input', {}).get('proprio', True)
        if not proprio:
            out['proprio_dim'] = 0
        out.update(overrides)
        if out['head'] == 'flow' and out.get('taps') and 32 in out['taps']:
            # The design names absolute layers of the 32-layer 9B LM; 32 is the last one.
            out['taps'] = [-1 if t == 32 else t for t in out['taps']]
        rest = {k: v for k, v in vla.items() if k not in ('head', 'cond', 'detach_backbone', 'lm_token_loss')}
        return cls.from_dict(out), rest

    def to_dict(self):
        return asdict(self)

    def sha256(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()

    def replace(self, **changes):
        return VLAConfig.from_dict({**self.to_dict(), **changes})
