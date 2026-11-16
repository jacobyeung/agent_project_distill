from dataclasses import asdict, dataclass
from .io import read_json

@dataclass(frozen=True)
class Config:
    output_format: str = 'nav'
    controller_version: str = 'v2'
    history_frames: int = 32
    step_cap: int = 500
    success_radius: float = 3.0
    forward_m: float = 0.25
    turn_deg: float = 15.0
    agent_height: float = 1.5
    agent_radius: float = 0.1
    rgb_px: int = 512
    hfov_deg: float = 90.0
    height_m: float = 1.25
    sliding: bool = True
    render: bool = False
    seed: int = 0
    dtw: str = 'fast'
    chunk_normalised: bool = False
    chunk_min: tuple = (0.0, -45.0, 0.0)
    chunk_max: tuple = (0.75, 45.0, 1.0)

    def __post_init__(self):
        if self.controller_version not in ('v1', 'v2'):
            raise ValueError('controller_version must be v1 or v2')
        if self.output_format not in ('text', 'nav', 'click', 'waypoint', 'chunk'):
            raise ValueError('Unknown output format')
        if self.history_frames < 1 or self.step_cap < 1:
            raise ValueError('History length and step cap must be positive')
        if self.dtw not in ('fast', 'exact'):
            raise ValueError('dtw must be fast or exact')
        if not self.sliding or self.forward_m != .25 or self.turn_deg != 15:
            raise ValueError('VLN-CE needs sliding, 0.25 m and 15 degrees')

    def to_dict(self):
        return asdict(self)

    def constants(self):
        return {k: getattr(self, k) for k in ('rgb_px', 'hfov_deg', 'height_m')}

def load_arm(path, allow_control=False):
    data = read_json(path)
    v = data['vla']
    if v.get('control_only') and not allow_control:
        raise PermissionError('N0 is control-only; explicit authorization is required')
    if 'tokens' in v or 'codec' not in v['head']['tokens']:
        raise ValueError('Use vla.head.tokens.codec')
    arm = {'nav_text': 'nav', 'nav_click': 'click'}[v['head']['tokens']['codec']]
    ev = v.get('nav', {}).get('eval', {})
    return data, Config(output_format=arm, history_frames=v['input']['history_frames'],
                        controller_version=ev.get('controller_version', 'v2'),
                        step_cap=ev.get('step_cap', 500), success_radius=ev.get('success_radius_m', 3.0))
