"""Observe the unchanged geodesic click policy, including each controller decision."""
from collections import Counter
import math
import numpy as np
from .click import label, lead_point, relative
from .policies import OracleClickPolicy
from .actions import Decoder
from .config import Config
from .episodes import load_split
from .io import read_json, write_json
from .lists import verify_manifest
from .paths import OUT
from .runner import Runner
from .sim import Environment

class ObservedClick(OracleClickPolicy):
    def reset(self, episode_id):
        self.observations = []

    def act(self, frames, instruction, state):
        answer = super().act(frames, instruction, state)
        distance, path = self.env.path(self.env.position, self.env.episode.goal)
        point = lead_point(path) if path else self.env.position
        _, reason = label(self.env.position, self.env.heading, point, distance, len(frames))
        obs = dict(frames=frames, instruction=instruction, **state)
        primitives, info = Decoder(self.env.config).decode(answer, obs)
        self.observations.append(dict(step=self.env.steps, position=self.env.position.tolist(),
            heading=self.env.heading, distance=distance, point=point.tolist(), answer=answer,
            reason=reason, primitives=primitives, controller=info))
        return answer

def describe(result, observations, positions):
    tail = observations[-20:]
    tail_positions = np.asarray([o['position'] for o in tail])
    tail_span = float(np.linalg.norm(tail_positions-tail_positions[-1], axis=1).max())
    states = [tuple(np.round(o['position'], 5)) + (round(o['heading'], 5),) for o in tail]
    blocked = sum(a == 'forward' and np.linalg.norm(np.asarray(positions[i+1])-positions[i]) < 1e-6
                  for i, a in enumerate(result['actions']))
    tail_actions = [o['primitives'] for o in tail]
    bearings = [o['controller'].get('bearing_deg') for o in tail]
    return dict(episode_id=result['episode_id'], termination=result['termination'], NE=result['NE'],
        SR=result['SR'], OSR=result['OSR'], decisions=result['decisions'], blocked_forward_steps=int(blocked),
        label_counts=dict(Counter(o['reason'] for o in observations)),
        tail_label_counts=dict(Counter(o['reason'] for o in tail)),
        tail_repeated_pose_heading=len(states)-len(set(states)),
        tail_span_from_last_m=tail_span,
        tail_class=('stationary' if tail_span < 1e-4 else 'moving_repeated_pose_heading'
                    if len(states) != len(set(states)) else 'no_repeated_pose_heading'),
        tail_zero_turn_nonzero_bearing=sum(b is not None and 0 < abs(b) < 7.5 for b in bearings),
        tail_empty_commands=sum(not a for a in tail_actions),
        tail_turn_only=sum(bool(a) and all(x.startswith('turn_') for x in a) for a in tail_actions),
        tail_turn_direction_changes=sum(a*b < 0 for a,b in zip(
            [o['controller'].get('bearing_deg', 0) for o in tail],
            [o['controller'].get('bearing_deg', 0) for o in tail][1:])),
        within_success_at_decision=sum(o['distance'] < 3 for o in observations),
        observations=observations)

def main():
    eps=verify_manifest(read_json(OUT/'lists/val_unseen_600_s0.json'),load_split('val_unseen'))
    prior={r['episode_id']:r for r in read_json(OUT/'tables/oracle-click_val_unseen_600_s0.json')['results']}
    env=Environment(Config(output_format='click')); policy=ObservedClick(env); runner=Runner(env)
    details=[]
    for i,e in enumerate(eps):
        r=runner.episode(e,policy)
        assert r['actions']==prior[e.episode_id]['actions'], e.episode_id
        details.append(describe(r,policy.observations,env.positions))
        if (i+1)%100==0: print('diagnosed',i+1,flush=True)
    env.close()
    capped=[d for d in details if d['termination']=='step_cap']
    summary=dict(episodes=len(details), unchanged_action_streams=len(details), step_caps=len(capped),
        capped_tail_classes=dict(Counter(d['tail_class'] for d in capped)),
        stationary_tail_all_nonzero_bearings_round_to_zero=sum(d['tail_class']=='stationary' and d['tail_zero_turn_nonzero_bearing']==20 for d in capped),
        capped_tail_entirely_turn_only=sum(d['tail_turn_only']==20 for d in capped),
        capped_with_blocked_forward=sum(d['blocked_forward_steps']>0 for d in capped),
        capped_with_tail_repeated_pose_heading=sum(d['tail_repeated_pose_heading']>0 for d in capped),
        capped_with_tail_clamp=sum(d['tail_label_counts'].get('near_point_clamp',0)>0 for d in capped),
        capped_with_tail_out_of_view=sum(d['tail_label_counts'].get('out_of_view',0)>0 for d in capped),
        capped_with_tail_zero_turn_nonzero_bearing=sum(d['tail_zero_turn_nonzero_bearing']>0 for d in capped),
        capped_with_tail_empty_commands=sum(d['tail_empty_commands']>0 for d in capped),
        capped_with_tail_turn_direction_changes=sum(d['tail_turn_direction_changes']>0 for d in capped),
        capped_with_success_at_decision=sum(d['within_success_at_decision']>0 for d in capped),
        capped_with_OSR=sum(d['OSR']>0 for d in capped), capped_final_within_success=sum(d['NE']<3 for d in capped))
    write_json(OUT/'tables/oracle_click_diagnostics.json',dict(summary=summary,episodes=details))
    print(summary,flush=True)

if __name__=='__main__': main()
