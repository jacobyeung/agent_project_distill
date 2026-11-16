"""Learning-rate schedule with a warm-up that always ends inside the run (review finding 18)."""
import math


def warmup_cosine(total_steps, warmup_steps=None, floor=0.0, warmup_frac=0.03):
    """LambdaLR factor: linear warm-up over `warmup_steps` (default round(warmup_frac * total), schema
    10 `optim.warmup_frac` 0.03), then cosine decay to `floor` (min_lr / lr). Refuses a warm-up as long
    as the run, so a short budget cannot spend every step warming up."""
    total_steps = int(total_steps)
    warmup = round(warmup_frac * total_steps) if warmup_steps is None else int(warmup_steps)
    if total_steps < 1 or not 0 <= warmup < total_steps:
        raise ValueError(f'warmup_steps={warmup} must lie in [0, total_steps={total_steps})')

    def factor(step):
        if step < warmup:
            return (step + 1) / warmup
        progress = min(1.0, (step - warmup) / max(1, total_steps - warmup))
        return floor + (1 - floor) * 0.5 * (1 + math.cos(math.pi * progress))
    factor.warmup, factor.total = warmup, total_steps
    return factor
