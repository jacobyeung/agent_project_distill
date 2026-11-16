"""CP1 atomic opener order and training-row MDG span positions."""
import re

OPENERS = ('<depth_at', '<move', '<pose', '<turn', '<box_3d', '<ground', '<gap')


def tokenizer_for_rows(path):
    from tokenizers import AddedToken, Tokenizer
    tokenizer = Tokenizer.from_file(str(path))
    for opener in OPENERS:
        if opener not in tokenizer.get_vocab():
            tokenizer.add_tokens([AddedToken(opener, normalized=False, special=False)])
        if tokenizer.encode(opener, add_special_tokens=False).ids != [tokenizer.token_to_id(opener)]:
            raise ValueError('non-atomic routing opener')
    return tokenizer


def gate_positions(tokenizer, suffix):
    spans = [m.span() for m in re.finditer(r'<ground obj="[^"<>\n]+">', suffix)]
    encoding = tokenizer.encode(suffix, add_special_tokens=False)
    return [i for i, (a,b) in enumerate(encoding.offsets)
            if any(a < end and start < b for start,end in spans)]
