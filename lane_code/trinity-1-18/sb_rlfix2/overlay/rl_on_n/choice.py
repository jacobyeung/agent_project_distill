"""Align sampled and forced IDs from the A4 reader with policy probabilities."""

def align(record, choice):
    """Per-position source of every generated id: 'f' forced prefix, 's' sampled, 'b' budget EOS,
    'r' tool response forced by the decoder. Also checks the decoder's ids against the choice log.
    """
    ids = record['tokens']
    kinds = [None] * len(ids)
    for call in record.get('calls', []):
        start, n = call['at_token'], call.get('forced_tokens',0)
        for i in range(start, min(start + n, len(ids))):
            kinds[i] = 'r'
    own = [i for i, k in enumerate(kinds) if k is None]
    if len(own) != len(choice.chosen) or any(ids[i] != t for i, t in zip(own, choice.chosen)):
        raise ValueError('decoded ids disagree with the choice log; response spans misaligned')
    lt = [None] * len(ids)
    lr = [None] * len(ids)
    for j, i in enumerate(own):
        kinds[i] = choice.kinds[j]
        lt[i], lr[i] = choice.logp_tempered[j], choice.logp_raw[j]
    return kinds, lt, lr

