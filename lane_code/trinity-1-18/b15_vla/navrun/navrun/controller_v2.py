"""Blocked-step recovery around the schema 8.2 controller, owned by navrun.

Normal decisions retain the backend's lift and quantization. A blocked forward
primitive cancels the remaining leg. Recovery turns one quantum and probes one
step per decision, keeping the initial direction until a probe moves. This avoids
both the zero-turn deadband and alternating corrections at an obstacle.
"""
from vla_where.nav import controller as controller_v1

# Same numerical zero-motion tolerance as click_diagnostics; not a distance budget.
BLOCKED_EPS_M = 1e-6


class ControllerV2:
    def __init__(self):
        self.reset()

    def reset(self):
        self.recovering = False
        self.direction = 'turn_left'

    def decide(self, primitives, waypoint, info):
        if 'stop' in primitives:
            return primitives, dict(info, recovery=False)
        if self.recovering:
            # Ignore a new bearing until a probe moves: its sign can flip as we turn.
            return [self.direction, 'forward'], dict(info, recovery=True)
        bearing = info.get('bearing_deg', (waypoint or {}).get('heading_deg', 0.))
        # A centered click has no preferred side; use a deterministic left tie.
        self.direction = 'turn_left' if bearing >= 0 else 'turn_right'
        return primitives, dict(info, recovery=False)

    def executed(self, action, displacement_m):
        """Return whether the runner must end this leg. Never expose motion to a model."""
        if action != 'forward':
            return False
        blocked = displacement_m < BLOCKED_EPS_M
        self.recovering = blocked
        return blocked
