"""Optional successor routing openers; old token IDs remain fixed."""
import re
from .ground_v312_tokens import tokenizer_for_rows as legacy_tokenizer


def tokenizer_for_rows(path, *, keypoint_calls=False):
    tokenizer=legacy_tokenizer(path)
    if keypoint_calls:
        from tokenizers import AddedToken
        for opener in ('<surface_pair','<extent_ends'):
            tokenizer.add_tokens([AddedToken(opener,normalized=False,special=False)])
            assert tokenizer.encode(opener,add_special_tokens=False).ids==[tokenizer.token_to_id(opener)]
    return tokenizer


def gate_positions(tokenizer,suffix,*,keypoint_calls=False):
    pattern=r'<ground obj="[^"<>\n]+"(?: mode="(?:instances|box)")?>'
    if keypoint_calls:
        pattern+=r'|<surface_pair a="[^"<>\n]+" b="[^"<>\n]+" mode="closest_visible">|<extent_ends obj="[^"<>\n]+" axis="longest_observed">'
    pattern+=r'|<ground mode="room">'
    spans=[m.span() for m in re.finditer(pattern,suffix)]
    enc=tokenizer.encode(suffix,add_special_tokens=False)
    return [i for i,(a,b) in enumerate(enc.offsets) if any(a<end and start<b for start,end in spans)]
