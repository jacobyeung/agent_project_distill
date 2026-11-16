"""Early-stop gates: on the camera loss (CameraGate) and on the text-row LM loss (LMGate, below).

At check_step the gate compares the mean camera loss over the window ending
at check_step with the mean over the window ending at baseline_step. Only
optimizer steps with pose-supervised rows count; each step's value is its
all-reduced loss sum divided by its all-reduced supervised-row count, so
every rank reaches the same decision. A relative drop below
min_relative_drop stops the run after check_step with GATE_STOPPED.json, a
checkpoint, and process exit status GATE_STOPPED_EXIT_CODE.
"""
import math

GATE_STOPPED_EXIT_CODE = 3
GATE_KEYS = frozenset({'baseline_step', 'check_step', 'min_relative_drop', 'window'})


def normalize_gate(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != GATE_KEYS:
        raise ValueError('Camera gate needs exactly baseline_step, check_step, min_relative_drop and window')
    if any(type(value[k]) is not int or value[k] < 1 for k in ('baseline_step', 'check_step', 'window')):
        raise ValueError('Camera gate steps and window must be positive integers')
    drop = value['min_relative_drop']
    if type(drop) not in (int, float) or not math.isfinite(drop) or not 0 <= drop < 1:
        raise ValueError('Camera gate min_relative_drop must lie in [0, 1)')
    if value['window'] > value['baseline_step'] or value['check_step'] - value['window'] < value['baseline_step']:
        raise ValueError('Camera gate windows must start at step 1 or later and must not overlap')
    return dict(value)


class CameraGate:
    def __init__(self, config):
        self.config = normalize_gate(config)
        self.samples = {}

    def record(self, step, loss_sum, rows):
        """One optimizer step's all-reduced camera-loss sum and pose-supervised row count."""
        if rows > 0:
            self.samples[int(step)] = (float(loss_sum), float(rows))

    def restore(self, metrics):
        """Rebuild the history from earlier metrics lines (resume)."""
        for metric in metrics:
            sample = metric.get('auxiliary', {}).get('camera_gate_sample')
            if sample is not None:
                self.record(sample['step'], sample['loss_sum'], sample['rows'])

    def window(self, end):
        steps = [step for step in range(end - self.config['window'] + 1, end + 1) if step in self.samples]
        values = [self.samples[step][0] / self.samples[step][1] for step in steps]
        return (sum(values) / len(values) if values else None), steps

    def decide(self, step):
        """None before check_step; at check_step a GATE_PASSED or GATE_STOPPED record."""
        if step != self.config['check_step']:
            return None
        baseline, baseline_steps = self.window(self.config['baseline_step'])
        check, check_steps = self.window(self.config['check_step'])
        record = {'baseline_mean': baseline, 'check_mean': check, 'relative_drop': None,
                  'baseline_steps': baseline_steps, 'check_steps': check_steps, **self.config}
        if not baseline_steps or not check_steps:
            reason = 'a gate window holds no optimizer step with pose-supervised rows'
        elif baseline <= 0:
            reason = 'the baseline camera loss is not positive'
        else:
            record['relative_drop'] = (baseline - check) / baseline
            if record['relative_drop'] >= self.config['min_relative_drop']:
                return {'status': 'GATE_PASSED', **record}
            reason = (f"camera loss fell by {record['relative_drop']:.4f} of its baseline, "
                      f"under the required {self.config['min_relative_drop']}")
        return {'status': 'GATE_STOPPED', 'reason': reason, 'exit_code': GATE_STOPPED_EXIT_CODE, **record}


def exit_status(result):
    """Process exit status of a trainer result: GATE_STOPPED_EXIT_CODE for a gate stop, else 0."""
    return GATE_STOPPED_EXIT_CODE if isinstance(result, dict) and result.get('status') == 'GATE_STOPPED' else 0


LM_GATE_KEYS = frozenset({'check_step', 'window', 'max_relative_increase', 'reference'})
LM_REFERENCE_KEYS = frozenset({'run', 'metrics_sha256', 'steps', 'values'})


def normalize_lm_gate(value):
    """A gate on the language-model loss of text-supervised rows against a reference run's same steps."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != LM_GATE_KEYS:
        raise ValueError('LM gate needs exactly check_step, window, max_relative_increase and reference')
    if any(type(value[k]) is not int or value[k] < 1 for k in ('check_step', 'window')) or value['window'] > value['check_step']:
        raise ValueError('LM gate check_step and window must be positive integers with window <= check_step')
    increase = value['max_relative_increase']
    if type(increase) not in (int, float) or not math.isfinite(increase) or not 0 <= increase < 1:
        raise ValueError('LM gate max_relative_increase must lie in [0, 1)')
    reference = value['reference']
    if not isinstance(reference, dict) or set(reference) != LM_REFERENCE_KEYS:
        raise ValueError('LM gate reference needs exactly run, metrics_sha256, steps and values')
    if not isinstance(reference['run'], str) or not reference['run']:
        raise ValueError('LM gate reference run must be named')
    digest = reference['metrics_sha256']
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Invalid LM gate reference metrics SHA256')
    expected = list(range(value['check_step'] - value['window'] + 1, value['check_step'] + 1))
    if reference['steps'] != expected:
        raise ValueError('LM gate reference steps must be the window ending at check_step')
    values = reference['values']
    if (not isinstance(values, list) or len(values) != len(expected)
            or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values)):
        raise ValueError('LM gate reference values must be one positive loss per window step')
    return {**value, 'reference': {**reference, 'steps': list(expected), 'values': [float(v) for v in values]}}


class LMGate:
    """Stops a run whose text-row language-model loss runs too far above a reference run's.

    Each optimizer step's value is the all-reduced language-model loss sum over
    text-supervised active rows divided by their all-reduced count, so pose-only
    rows (LM weight 0) neither add loss nor dilute the mean. At check_step the
    mean over the window ending there is compared with the reference run's mean
    over the same steps; more than max_relative_increase above it stops the run.
    """

    def __init__(self, config):
        self.config = normalize_lm_gate(config)
        self.samples = {}
        values = self.config['reference']['values']
        self.reference_mean = sum(values) / len(values)

    def record(self, step, loss_sum, rows):
        if rows > 0:
            self.samples[int(step)] = (float(loss_sum), float(rows))

    def restore(self, metrics):
        for metric in metrics:
            sample = metric.get('auxiliary', {}).get('lm_gate_sample')
            if sample is not None:
                self.record(sample['step'], sample['loss_sum'], sample['rows'])

    def decide(self, step):
        if step != self.config['check_step']:
            return None
        steps = [s for s in self.config['reference']['steps'] if s in self.samples]
        values = [self.samples[s][0] / self.samples[s][1] for s in steps]
        check = sum(values) / len(values) if values else None
        record = {'gate': 'lm', 'reference_mean': self.reference_mean, 'check_mean': check, 'relative_increase': None,
                  'check_steps': steps, 'check_step': self.config['check_step'], 'window': self.config['window'],
                  'max_relative_increase': self.config['max_relative_increase'], 'reference': self.config['reference']}
        if not steps:
            reason = 'the LM gate window holds no optimizer step with text-supervised rows'
        else:
            record['relative_increase'] = (check - self.reference_mean) / self.reference_mean
            if record['relative_increase'] <= self.config['max_relative_increase']:
                return {'status': 'GATE_PASSED', **record}
            reason = (f"language-model loss {check:.5f} is {record['relative_increase']:.4f} above the reference "
                      f"{self.reference_mean:.5f} of {self.config['reference']['run']}, over the allowed "
                      f"{self.config['max_relative_increase']}")
        return {'status': 'GATE_STOPPED', 'reason': reason, 'exit_code': GATE_STOPPED_EXIT_CODE, **record}
