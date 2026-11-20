"""The measurement loop. No model, tool, or scoring imports."""
OPENINGS = ('<ground', '<move', '<turn', '<pose', '<depth_at', '<gap',
            '<dist', '<closest', '<cam_dist', '<angle', '<area',
            '<surface_pair', '<extent_ends', '<box_3d')
CAP = 64


def detect(text):
    return [i for i, opening in enumerate(OPENINGS) if opening in text]


def decode(first, choose, advance, tokenizer, eos, deadline=lambda: None):
    """Check cumulative decoded output after every token, including token 64."""
    ids = []
    output = first
    for _ in range(CAP):
        deadline()
        token = int(choose(output))
        ids.append(token)
        text = tokenizer.decode(ids, skip_special_tokens=False)
        opened = detect(text)
        if opened:
            finish = 'call'
            break
        if token in eos:
            finish = 'eos'
            break
        if len(ids) == CAP:
            finish = 'cap'
            break
        output = advance(ids)
    return dict(text=text, tokens=ids, n=len(ids), g=0 in opened,
                o=[i for i in opened if i != 0], finish=finish)
