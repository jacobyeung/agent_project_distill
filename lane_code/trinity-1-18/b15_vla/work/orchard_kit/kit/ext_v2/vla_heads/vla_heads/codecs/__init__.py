"""Action codecs for the tokens head and the flow head's LM token loss.

A codec maps normalised chunks [B, K, A] to symbol sequences in [0, vocab) and back:
- encode(actions) -> list of B integer lists;
- decode(seqs) -> (actions [B, K, A] float32, ok [B] bool);
- fixed_length: int, or None for variable-length codecs (the head appends an end symbol);
- error_bound(): the round-trip max-abs bound on [-1, 1].
"""
from .bins import UniformBins
from .digits import CharTokenizer, DigitsCodec
from .fast import DCTCodec, FastCodec, dct_matrix
from . import nav_text, reserved


def make_codec(cfg, name=None, tokenizer=None):
    name = name or cfg.token_codec
    if name == 'bins':
        return UniformBins(cfg.chunk, cfg.action_dim, cfg.tok_bins)
    if name == 'dct':
        return DCTCodec(cfg.chunk, cfg.action_dim, cfg.tok_dct_keep, cfg.tok_dct_scale, cfg.tok_dct_clip)
    if name == 'fast':
        return FastCodec(cfg.chunk, cfg.action_dim, cfg.tok_vocab, cfg.tok_dct_scale, cfg.tok_codec_path)
    if name == 'digits':
        return DigitsCodec(cfg.chunk, cfg.action_dim, tokenizer)
    if name in ('nav_text', 'nav_click'):
        raise ValueError(f'{name} is ordinary LM text under nav_grammar_v1 (codecs.nav_text; LM cross-entropy, '
                         'no head parameters), not a chunk codec')
    raise ValueError(f'Unknown codec {name!r}')
