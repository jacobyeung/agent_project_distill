from .flow import FlowExpert, cosine_alpha_bar, euler, sample_tau
from .regression import RegressionHead
from .tokens import TokensHead

HEAD_CLASSES = {'regression': RegressionHead, 'flow': FlowExpert, 'tokens': TokensHead}


def make_head(cfg, **kw):
    """Build the head `cfg.head` names (tokens heads accept codec= and tokenizer=)."""
    return HEAD_CLASSES[cfg.head](cfg, **kw) if cfg.head == 'tokens' else HEAD_CLASSES[cfg.head](cfg)
