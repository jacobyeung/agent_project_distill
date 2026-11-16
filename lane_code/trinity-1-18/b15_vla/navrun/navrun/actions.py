import json
import math
import numpy as np
from .vendor import nav_text as NT
from .click import controller, ClickTranslator

TEXT = dict(A='forward', B='turn_left', C='turn_right', D='stop')

class Decoder:
    def __init__(self, config, click_backend=None):
        self.config = config
        self.click_backend = click_backend or ClickTranslator(history_frames=config.history_frames)
        self.reset()

    def reset(self):
        self.forward_residual = self.turn_residual = 0.
        self.click_backend.reset()

    def decode(self, answer, observation):
        fmt = self.config.output_format
        if fmt in ('nav', 'click'):
            if not isinstance(answer, str) or NT.parse(answer, fmt, self.config.history_frames) is None:
                return None, {}
            if fmt == 'click':
                primitives, waypoint, info = self.click_backend.decide(answer, observation)
                return primitives, dict(info, waypoint=waypoint)
            return NT.primitives(NT.parse(answer, fmt)), {}
        if fmt == 'text':
            if not isinstance(answer, str):
                return None, {}
            answer = NT.answer_text(answer)
            answer = TEXT.get(answer, answer)
            return ([answer], {}) if answer in ('stop', 'forward', 'turn_left', 'turn_right') else (None, {})
        try:
            data = json.loads(NT.answer_text(answer)) if isinstance(answer, str) else answer
            if fmt == 'waypoint':
                if set(data) != {'heading_deg', 'distance_m', 'stop'} or type(data['stop']) is not bool:
                    raise ValueError('Waypoint schema')
                heading, distance = float(data['heading_deg']), float(data['distance_m'])
                if not math.isfinite(heading+distance) or not -180 <= heading <= 180 or not 0 <= distance <= 2:
                    raise ValueError('Waypoint range')
                return (['stop'] if data['stop'] else controller(heading, distance)), dict(waypoint=data)
            a = np.asarray(data, float)
            if a.ndim != 2 or a.shape[1] != 3 or not 1 <= len(a) <= 500 or not np.isfinite(a).all():
                raise ValueError('Chunk must have shape [K,3] and finite values')
            if self.config.chunk_normalised:
                lo, hi = np.array(self.config.chunk_min), np.array(self.config.chunk_max)
                a = lo + (np.clip(a, -1, 1)+1)/2*(hi-lo)
            if np.any(a[:, 0] < 0) or np.any(a[:, 0] > 2) or np.any(abs(a[:, 1]) > 180) or np.any((a[:, 2] < 0) | (a[:, 2] > 1)):
                raise ValueError('Physical chunk outside range')
            out, fr, tr = [], self.forward_residual, self.turn_residual
            for forward, turn, stop in a:
                if stop >= .5:
                    out.append('stop')
                    break
                fr += forward
                tr += turn
                turns, steps = round(tr/15), round(fr/.25)
                tr -= turns*15
                fr -= steps*.25
                out += ['turn_left' if turns > 0 else 'turn_right']*abs(turns)
                out += ['forward']*max(0, steps)
            self.forward_residual, self.turn_residual = fr, tr
            return out, dict(residual=[fr, tr])
        except (ValueError, TypeError, KeyError, OverflowError):
            return None, {}
