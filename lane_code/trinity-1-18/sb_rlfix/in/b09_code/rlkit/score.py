"""Benchmark score c of one rollout: MRA for numbers, exact match for option letters.

The parser is the readers' own (vendored student-answer-v1, pinned). MRA follows the
VSI-Bench scorer: thresholds np.linspace(0.5, 0.95, int((0.95-0.5)/0.05 + 2)) (= 10 points
in float arithmetic), credit = mean(|pred - gt| / gt <= 1 - threshold); gt = 0 gives 0.
"""
import math

import numpy as np

from .vendor.answers import parse_answer

_START, _END, _STEP = 0.5, 0.95, 0.05
THRESHOLDS = np.linspace(_START, _END, int((_END - _START) / _STEP + 2))


def mra(pred, gt):
    pred, gt = float(pred), float(gt)
    if not (math.isfinite(pred) and math.isfinite(gt)) or gt == 0:
        return 0.0
    rel = abs(pred - gt) / abs(gt)
    return float((rel <= 1 - THRESHOLDS).mean())


def score(prompt, text):
    """dict(c, answer, parse_failure). `text` is the generated suffix (after the prompt's `<think>\\n`)."""
    options = prompt.get('options') or []
    parsed = parse_answer(text, options)
    answer = parsed['answer']
    if answer is None:
        return dict(c=0.0, answer=None, parse_failure=parsed['parser']['failure_reason'])
    if options:
        c = 1.0 if answer == str(prompt['gt_answer']).strip().upper() else 0.0
    else:
        c = mra(answer, prompt['gt_answer'])
    return dict(c=c, answer=answer, parse_failure=None)
