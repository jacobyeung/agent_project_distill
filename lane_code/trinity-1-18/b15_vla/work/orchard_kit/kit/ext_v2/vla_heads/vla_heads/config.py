"""One flat configuration for every head, codec, conditioning mode and backbone adapter.

Every key has a default; `VLAConfig.from_dict` rejects unknown keys. `VLAConfig.from_spec` loads the
`vla:` tree of VLA_SCHEMA.md section 10 (`vla_schema_v2`) exactly: unknown keys raise, and so does a
bare `tokens.codec` outside `vla.head`. Sections that do not configure the head (control_only,
backbone path, prompt, optim, train, data, eval, provider, nav) come back untouched for the trainer,
plus `train_effective` and `eval_effective` under the navigation precedence rule.
"""
from dataclasses import asdict, dataclass, field, fields
import hashlib
import json

SCHEMA = 'vla_schema_v2'

HEADS = ('regression', 'flow', 'tokens')
HEAD_ALIASES = {'generative': 'flow', 'diffusion': 'flow', 'discrete': 'tokens'}
CONDS = ('none', 'g3t_tokens', 'spatial_readouts', 'both')
OBJECTIVES = ('flow', 'ddpm')
TIME_DISTS = ('beta_1.5_1', 'uniform', 'logit_normal')
CHUNK_CODECS = ('fast', 'bins', 'dct', 'digits')
NAV_CODECS = ('nav_text', 'nav_click')
CODECS = CHUNK_CODECS + NAV_CODECS
TRAIN_MODES = ('full', 'lora', 'frozen')
INJECT = ('head', 'lm')
REG_ARCHS = ('starvla_oft_985c2238', 'custom')
# StarVLA 985c2238 L1RegressionActionHead: LN, Linear(D, H), ReLU, blocks x + ReLU(Linear(LN(x))), LN, Linear(H, A).
STARVLA_OFT = dict(reg_block='oft', reg_act='relu', reg_input_act=True, reg_final_norm=True)
FAST_REFERENCE = 'physical-intelligence/fast processing_action_tokenizer.py@ec4d7aa71691cac0b8bed6942be45684db2110f4'
FAST_REFERENCE_SHA256 = '6f021ca1f4c1b194ab6fa399d80baf3d642eadb17efb8f73301e4ac401522c20'
WHERE_FEATURES = 18


@dataclass
class VLAConfig:
    # shared
    head: str = 'regression'
    action_dim: int = 7
    chunk: int = 8
    hidden_size: int = 4096
    lm_layers: int = 32                             # decoder layers of the LM (Qwen3.5-9B: 32)
    proprio_dim: int = 8
    proprio_inject: str = 'head'
    taps: list = field(default_factory=list)       # one-based layers 1..lm_layers-1, or -1 (final norm); [] = head default
    tap_norm: bool = False                          # also apply the final norm to taps below the last layer
    detach_backbone: bool = False                   # flow: no head gradient into the LM
    lm_token_loss: str = 'none'                     # 'none' | a chunk codec: the LM also writes the chunk
    lm_token_weight: float = 1.0
    # conditioning
    cond: str = 'none'
    cond_dim: int = 1024
    cond_inject: str = 'head'
    where_vector: bool = True                       # feed the where vectors to the head (spatial_readouts, both)
    where_entities: int = 2                         # target, place
    where_features: int = WHERE_FEATURES
    where_dropout: float = 0.2                      # training: share of chunks withheld (sha256 draw, cond.withheld_draw)
    where_seed: int = 17
    max_views: int = 32
    g3t_cam_dim: int = 2058
    g3t_patch_dim: int = 2048
    g3t_patch_grid: int = 0                         # 0 = camera tokens only; g = g x g pooled patch tokens per view
    readout_depth_grid: int = 4
    readout_hidden: int = 256
    # (a) regression
    reg_arch: str = 'starvla_oft_985c2238'          # fixes the four flags below; 'custom' frees them
    reg_hidden: int = 8192
    reg_blocks: int = 2
    reg_block: str = 'oft'                           # 'oft' = x + act(Linear(LN(x))); 'mlp2' = x + Linear(act(Linear(LN(x))))
    reg_act: str = 'relu'
    reg_input_act: bool = True                       # activation after the first projection
    reg_final_norm: bool = True                      # LayerNorm before the output layer
    reg_cond_heads: int = 8
    # (b) flow / diffusion expert
    flow_layers: int = 8
    flow_width: int = 1024
    flow_heads: int = 16
    flow_mlp_ratio: float = 4.0
    flow_objective: str = 'flow'
    flow_time_dist: str = 'beta_1.5_1'
    flow_steps: int = 10
    flow_cond_gate: str = 'zero_init'                # cond tokens enter through a tanh gate initialised to 0
    flow_time_cond: str = 'concat'                   # 'concat' = MLP([W_a x ; phi(tau)]) (pi0); 'adaln'
    flow_dropout: float = 0.0
    ddpm_train_steps: int = 100
    ddpm_clip_sample: bool = True
    ddpm_prediction: str = 'epsilon'                # 'epsilon' | 'sample' (x0, as Diffusion Policy's option)
    # (c) tokens
    tok_codec: str = 'fast'
    tok_vocab: int = 1024                            # FAST BPE vocabulary
    tok_bins: int = 256
    tok_dct_scale: float = 10.0                      # FAST and dct quantisation scale
    tok_dct_keep: int = 0                            # dct only: 0 = all chunk coefficients
    tok_dct_clip: int = 127                          # dct only
    tok_max_tokens: int = 64                         # length cap for variable-length codecs (digits arm: 256)
    tok_ids: str = 'append'                          # 'append' new rows | path to a reserved-id JSON
    tok_ids_sha256: str = ''                         # pin of the reserved-id JSON ('' = not pinned)
    tok_fast_reference: str = FAST_REFERENCE
    tok_ce: str = 'full'                             # 'full' vocabulary | 'restricted' to codec ids
    tok_codec_path: str = ''                         # fitted codec state (FAST JSON)
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
        self.flow_time_dist = 'beta_1.5_1' if self.flow_time_dist == 'beta' else self.flow_time_dist
        checks = (('head', HEADS), ('cond', CONDS), ('flow_objective', OBJECTIVES), ('flow_time_dist', TIME_DISTS),
                  ('tok_codec', CODECS), ('train_mode', TRAIN_MODES), ('cond_inject', INJECT),
                  ('proprio_inject', INJECT), ('tok_ce', ('full', 'restricted')), ('reg_block', ('mlp2', 'oft')),
                  ('reg_act', ('gelu', 'relu')), ('flow_time_cond', ('concat', 'adaln')), ('reg_arch', REG_ARCHS),
                  ('flow_cond_gate', ('zero_init',)), ('lm_token_loss', ('none',) + CHUNK_CODECS),
                  ('ddpm_prediction', ('epsilon', 'sample')))
        for key, allowed in checks:
            if getattr(self, key) not in allowed:
                raise ValueError(f'{key}={getattr(self, key)!r}; choose one of {allowed}')
        for key in ('action_dim', 'chunk', 'hidden_size', 'lm_layers', 'cond_dim', 'reg_hidden', 'flow_layers',
                    'flow_width', 'flow_heads', 'flow_steps', 'ddpm_train_steps', 'tok_vocab', 'tok_bins',
                    'max_views', 'readout_depth_grid', 'where_entities', 'tok_max_tokens'):
            if type(getattr(self, key)) is not int or getattr(self, key) < 1:
                raise ValueError(f'{key} must be a positive int')
        if self.proprio_dim < 0 or self.reg_blocks < 0 or self.g3t_patch_grid < 0:
            raise ValueError('proprio_dim, reg_blocks and g3t_patch_grid must be >= 0')
        if self.where_features != WHERE_FEATURES:
            raise ValueError(f'where_features is fixed at {WHERE_FEATURES} (the where record, schema 5.2)')
        if self.reg_arch == 'starvla_oft_985c2238':
            wrong = {k: getattr(self, k) for k, v in STARVLA_OFT.items() if getattr(self, k) != v}
            if wrong:
                raise ValueError(f'reg_arch starvla_oft_985c2238 fixes {STARVLA_OFT}; got {wrong} (use reg_arch custom)')
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
        if self.head == 'regression' and 'lm' in (self.cond_inject, self.proprio_inject):
            raise ValueError('The regression head reads the in-prompt query tokens; LM-injected cond or proprio '
                             'would follow them and stay unseen: use cond_inject = proprio_inject = head')
        if not self.taps:
            self.taps = [16, -1] if self.head == 'flow' else [-1]
        if any(type(t) is not int for t in self.taps):
            raise ValueError(f'taps must be integers, got {self.taps}')
        self.taps = list(self.taps)
        if any(not (t == -1 or 1 <= t < self.lm_layers) for t in self.taps) or len(set(self.taps)) != len(self.taps):
            raise ValueError(f'taps are distinct layers 1..{self.lm_layers - 1} or -1 (final norm); '
                             f'0 and {self.lm_layers} are invalid, got {self.taps}')
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
        """Schema-10 tree (a dict with a top-level `vla`, or its body) -> (VLAConfig, rest).
        `rest` holds every `vla` section for the trainer (backbone, input, prompt, optim, train, data,
        eval, provider, nav, where). `overrides` are flat VLAConfig keys applied last."""
        if 'tokens' in spec or ('vla' in spec and set(spec) - {'vla'}):
            raise ValueError(f'Unknown top-level spec keys {sorted(set(spec) - {"vla"})}; the codec key is vla.head.tokens.codec')
        vla = spec.get('vla', spec)
        _keys('vla', vla, SPEC_KEYS)
        if vla.get('schema', SCHEMA) != SCHEMA:
            raise ValueError(f'vla.schema={vla["schema"]!r}; this package implements {SCHEMA}')
        head = vla.get('head', {})
        _keys('vla.head', head, SPEC_KEYS['head'])
        kind = head.get('type', 'regression')
        out = dict(head=kind, chunk=head.get('chunk', 8), action_dim=head.get('action_dim', 7))
        if 'taps' in head:
            out['taps'] = list(head['taps'])
        reg = head.get('regression', {})
        if reg.get('loss', 'l1') != 'l1':
            raise ValueError('The regression head trains with L1 only')
        out.update(_take(reg, arch='reg_arch', hidden='reg_hidden', blocks='reg_blocks'))
        out.update(_take(head.get('flow', {}), layers='flow_layers', width='flow_width', heads='flow_heads',
                         objective='flow_objective', time_dist='flow_time_dist', steps='flow_steps',
                         cond_gate='flow_cond_gate'))
        tok = head.get('tokens', {})
        out.update(_take(tok, codec='tok_codec', vocab='tok_vocab', bins='tok_bins', reserved_ids='tok_ids',
                         reserved_sha256='tok_ids_sha256', scale='tok_dct_scale', max_tokens='tok_max_tokens'))
        if 'tok_dct_scale' in out:
            out['tok_dct_scale'] = float(out['tok_dct_scale'])
        if tok.get('fast_reference', FAST_REFERENCE) != FAST_REFERENCE:
            raise ValueError(f'vla.head.tokens.fast_reference={tok["fast_reference"]!r}; the vendored reference is {FAST_REFERENCE}')
        if tok.get('fast_reference_sha256', FAST_REFERENCE_SHA256) != FAST_REFERENCE_SHA256:
            raise ValueError('vla.head.tokens.fast_reference_sha256 does not match the vendored reference')
        out['cond'] = vla.get('cond', 'none')
        nav = out.get('tok_codec') in NAV_CODECS
        if nav and out['cond'] != 'none':
            raise ValueError('A navigation config (tokens.codec nav_text | nav_click) must set vla.cond: none')
        if not isinstance(vla.get('control_only', False), bool):
            raise ValueError('vla.control_only is a bool')
        where = vla.get('where', {})
        if where.get('dropout_draw', 'sha256_seed_episode_t') != 'sha256_seed_episode_t':
            raise ValueError('vla.where.dropout_draw must be sha256_seed_episode_t')
        if where.get('entities', 2) != 2:
            raise ValueError('vla.where.entities is 2 (target, place)')
        out.update(_take(where, dropout='where_dropout', vector='where_vector'))
        if 'seed' in vla.get('train', {}):
            out['where_seed'] = vla['train']['seed']
        out['detach_backbone'] = bool(vla.get('detach_backbone', False))
        out['lm_token_loss'] = vla.get('lm_token_loss', 'none')
        backbone = vla.get('backbone', {})
        if 'train' in backbone:
            out['train_mode'] = backbone['train']
        if backbone.get('vision', 'frozen') not in ('frozen', 'train'):
            raise ValueError('vla.backbone.vision is frozen | train')
        out['train_vision'] = backbone.get('vision', 'frozen') == 'train'
        if not vla.get('input', {}).get('proprio', True):
            out['proprio_dim'] = 0
        if any('.' in k for k in overrides):
            raise ValueError('overrides are flat VLAConfig keys (dotted paths belong in the spec)')
        out.update(overrides)
        rest = {k: v for k, v in vla.items() if k not in ('head', 'cond', 'detach_backbone', 'lm_token_loss', 'schema')}
        rest['control_only'] = vla.get('control_only', False)
        # Schema 10 navigation precedence: nav.train overlays optim and train key by key; nav.eval alone sets evaluation.
        train = {**vla.get('optim', {}), **vla.get('train', {})}
        rest['train_effective'] = {**train, **vla.get('nav', {}).get('train', {})} if nav else train
        rest['eval_effective'] = dict(vla.get('nav', {}).get('eval', {})) if nav else dict(vla.get('eval', {}))
        return cls.from_dict(out), rest

    def to_dict(self):
        return asdict(self)

    def sha256(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()

    def replace(self, **changes):
        return VLAConfig.from_dict({**self.to_dict(), **changes})


_ANY = None  # a section whose contents the trainer validates
SPEC_KEYS = {
    'schema': _ANY, 'control_only': _ANY, 'cond': _ANY, 'detach_backbone': _ANY, 'lm_token_loss': _ANY,
    'backbone': {'kind', 'path', 'revision', 'sha256', 'train', 'vision'},
    'input': {'cameras', 'image_px', 'orientation', 'proprio', 'history_frames'},
    'prompt': {'template'},
    'head': {'type': _ANY, 'chunk': _ANY, 'action_dim': _ANY, 'taps': _ANY,
             'regression': {'arch', 'hidden', 'blocks', 'loss'},
             'flow': {'layers', 'width', 'heads', 'objective', 'time_dist', 'steps', 'cond_gate'},
             'tokens': {'codec', 'vocab', 'bins', 'scale', 'max_tokens', 'reserved_ids', 'reserved_sha256',
                        'fast_reference', 'fast_reference_sha256'}},
    'where': {'text_line', 'vector', 'dropout', 'dropout_draw', 'entities'},
    'optim': _ANY, 'train': _ANY, 'data': _ANY, 'eval': _ANY, 'provider': _ANY, 'nav': _ANY,
}


def _keys(path, section, allowed):
    """Raise on keys the schema does not define (recursively where the schema lists them)."""
    if not isinstance(section, dict):
        raise ValueError(f'{path} must be a mapping')
    names = set(allowed)
    unknown = set(section) - names
    if unknown:
        hint = '; the codec key is vla.head.tokens.codec' if 'tokens' in unknown or 'codec' in unknown else ''
        raise ValueError(f'Unknown keys under {path}: {sorted(unknown)}{hint}')
    if isinstance(allowed, dict):
        for k, sub in allowed.items():
            if sub is not _ANY and k in section:
                _keys(f'{path}.{k}', section[k], sub)


def _take(section, **names):
    return {flat: section[key] for key, flat in names.items() if key in section}
