"""T1-like row plans and audited training-action replay."""
import math
from collections import Counter
import numpy as np
from .episodes import PRIMITIVES, training_gt, load_split
from .audit import split_audit
from .click import label, lead_point, controller
from .prompts import history_indices, prompt, TEMPLATE_ID, TEMPLATE_SHA256
from .vendor import nav_text as NT
from .sim import Environment
from .config import Config
from .io import read_json, write_json

ROW_FIELDS = ['id', 'episode_id', 'trajectory_id', 'scene_id', 'split', 'output_format', 'decision_step',
              'history_indices', 'frames', 'instruction', 'executed', 'prompt', 'answer',
              'template_id', 'template_sha256', 'gt_source', 'render_status']

def encode_nav(actions):
    """Greedy runs of <=3 primitives per token, <=3 tokens per answer, STOP only last."""
    i = 0
    while i < len(actions):
        start, tokens, consumed = i, [], []
        while i < len(actions) and len(tokens) < 3:
            name = PRIMITIVES[actions[i]] if isinstance(actions[i], int) else actions[i]
            if name == 'stop':
                tokens.append('stop');consumed.append(name);i += 1
                break
            n = 1
            while i+n < len(actions) and n < 3 and actions[i+n] == actions[i]:
                n += 1
            tokens.append(f'{name} {n*.25:.2f}' if name == 'forward' else f'{name} {n*15}')
            consumed += [name]*n
            i += n
        answer = NT.nav_text(tokens)
        assert NT.primitives(NT.parse(answer, 'nav')) == consumed
        yield start, answer, consumed

def reference_track(env, episode):
    """Reconstruct missing GT using a greedy follower through reference waypoints (0.5 m)."""
    env.reset(episode)
    follower = env.follower(.5)
    actions, locations = [], [env.position.tolist()]
    targets = episode.reference_path[1:] or [episode.goal]
    for target in targets:
        while env.steps < env.config.step_cap-1:
            action = follower.next_action_along(np.array(target, np.float32))
            if action == 'stop':
                break
            actions.append(PRIMITIVES.index(action))
            env.step(action)
            if action == 'forward':
                locations.append(env.position.tolist())
    actions.append(0)
    return dict(actions=actions, locations=locations, forward_steps=actions.count(1),
                source='reconstructed_reference_follower', cap_reached=env.steps >= env.config.step_cap-1)

def prepare_tracks(train, cache):
    tracks = training_gt(train)
    if cache.exists() and len(tracks) != len(train):
        data = read_json(cache)
        if set(data) != {e.episode_id for e in train}:
            raise ValueError('GT cache ids differ')
        # Supplied tracks always replace cached reconstructions or older sources.
        data.update(tracks)
        tracks = data
    env = Environment()
    generated = {}
    missing = [e for e in train if e.episode_id not in tracks]
    for i, e in enumerate(sorted(missing, key=lambda e: (e.scene, e.trajectory_id))):
        key = (e.scene, e.trajectory_id)
        if key not in generated:
            generated[key] = reference_track(env, e)
        tracks[e.episode_id] = generated[key]
        if (i+1) % 300 == 0:
            print('reconstructed missing episode', i+1, '/', len(missing), flush=True)
    env.close()
    write_json(cache, tracks)
    return tracks

def replay_check(train, tracks):
    counts, rows, states, errors = Counter(), 0, 0, []
    for e in train:
        track = tracks[e.episode_id]
        restored = []
        for _, answer, _ in encode_nav(track['actions']):
            restored.extend(PRIMITIVES.index(a) for a in NT.primitives(NT.parse(answer, 'nav')))
            rows += 1
        if restored != track['actions']:
            errors.append(e.episode_id)
        counts[track['source']] += 1
        states += len(track['actions'])
    return dict(episodes=len(train), source_counts=dict(counts), nav_rows=rows, primitive_states=states,
                exact_action_replays=len(train)-len(errors), mismatched_ids=errors,
                original_gt_complete=all(t['source'].startswith('supplied') for t in tracks.values()))

def location_replay_check(train, tracks, subsets=None, tolerance=2e-6):
    """Compare the start and every forward endpoint against official locations."""
    env = Environment(Config(step_cap=max(500, max(len(t['actions']) for t in tracks.values()))))
    results = []
    for i, e in enumerate(sorted(train, key=lambda e: (e.scene, e.episode_id))):
        track = tracks[e.episode_id]
        env.reset(e)
        locations = [env.position]
        for action in track['actions']:
            env.step(PRIMITIVES[action])
            if action == 1:
                locations.append(env.position)
        errors = np.linalg.norm(np.asarray(locations)-np.asarray(track['locations']), axis=1)
        results.append(dict(episode_id=e.episode_id, endpoint_error_m=float(errors[-1]),
                            max_path_error_m=float(errors.max())))
        if (i+1)%2000 == 0: print('location replay', i+1, '/', len(train), flush=True)
    env.close()
    def summary(records):
        return dict(episodes=len(records), endpoints_within_tolerance=sum(r['endpoint_error_m']<=tolerance for r in records),
                    paths_within_tolerance=sum(r['max_path_error_m']<=tolerance for r in records),
                    max_endpoint_error_m=max(r['endpoint_error_m'] for r in records),
                    max_path_error_m=max(r['max_path_error_m'] for r in records),
                    deviating_ids=[r['episode_id'] for r in records if r['max_path_error_m']>tolerance])
    return dict(tolerance_m=tolerance, full=summary(results),
                subsets={name:summary([r for r in results if r['episode_id'] in ids]) for name,ids in (subsets or {}).items()},
                results=results)

def trace(env, episode, actions):
    env.reset(episode)
    positions, headings = [], []
    for a in actions:
        positions.append(env.position.tolist()); headings.append(env.heading)
        env.step(PRIMITIVES[a])
    return positions, headings

def waypoint_decisions(actions):
    i = 0
    while i < len(actions):
        start, turn, forward = i, 0, 0
        while i < len(actions) and actions[i] in (2, 3) and abs(turn + (15 if actions[i] == 2 else -15)) <= 180:
            turn += 15 if actions[i] == 2 else -15;i += 1
        while i < len(actions) and actions[i] == 1 and forward < 8:
            forward += 1;i += 1
        stop = i < len(actions) and actions[i] == 0
        # A separate STOP row keeps the local controller from discarding movement.
        if i == start and stop:
            i += 1
        elif i == start:
            raise ValueError('Invalid waypoint action stream')
        yield start, dict(heading_deg=float(turn), distance_m=forward*.25, stop=stop and i == start+1 and actions[start] == 0), i-start

def row(episode, fmt, t, answer, actions, source, history=32):
    indices = history_indices(t, history)
    executed = [PRIMITIVES[a] for a in actions[:t]]
    return dict(id=f'{episode.episode_id}:{fmt}:{t}', episode_id=episode.episode_id,
                trajectory_id=episode.trajectory_id, scene_id=episode.scene_id, split='train',
                output_format=fmt, decision_step=t, history_indices=indices,
                frames=[f'frames/{episode.scene}/{episode.episode_id}/{i:05d}.png' for i in indices],
                instruction=episode.instruction, executed=executed,
                prompt=prompt(episode.instruction, executed, fmt, history), answer=answer,
                template_id=TEMPLATE_ID, template_sha256=TEMPLATE_SHA256,
                gt_source=source, render_status='planned_not_rendered')

def episode_rows(episode, track, env, history=32):
    actions, source = track['actions'], track['source']
    for t, answer, _ in encode_nav(actions):
        yield row(episode, 'nav', t, answer, actions, source, history)
    for t, a in enumerate(actions):
        yield row(episode, 'text', t, PRIMITIVES[a], actions, source, history)
        chunk = [[.25 if a == 1 else 0., 15. if a == 2 else -15. if a == 3 else 0., float(a == 0)]]
        yield row(episode, 'chunk', t, chunk, actions, source, history)
    for t, answer, _ in waypoint_decisions(actions):
        yield row(episode, 'waypoint', t, answer, actions, source, history)
    positions, headings = trace(env, episode, actions)
    t = 0
    while t < len(actions):
        goal_distance = env.distance(positions[t], episode.goal)
        point = lead_point(positions[t:])
        answer, reason = label(positions[t], headings[t], point, goal_distance, history)
        r = row(episode, 'click', t, answer, actions, source, history)
        r['label_reason'] = reason
        yield r
        decision = NT.parse(answer, 'click', history)
        if isinstance(decision, NT.Click):
            from .click import floor_plane, bearing_range, travel
            beta, rng = bearing_range(*floor_plane(decision.x, decision.y))
            advance = len(controller(beta, travel(rng)))
        else:
            advance = len(NT.primitives(decision))
        if answer == 'stop' or t == len(actions)-1:
            break
        t = min(len(actions)-1, t + max(1, advance))

def build_rows(episodes, tracks, output, train, unseen, test, history=32, nested_ids=()):
    """Audit before creating output; one render plan supports both nested subsets."""
    import gzip, json
    audit = split_audit(train, unseen, test)
    output.mkdir(parents=True, exist_ok=True)
    env = Environment(Config(step_cap=max(500, max(len(tracks[e.episode_id]['actions']) for e in episodes))))
    summaries, totals, reasons = [], Counter(), Counter()
    nested_ids, nested_totals, nested_reasons = set(nested_ids), Counter(), Counter()
    with gzip.open(output/'rows.jsonl.gz', 'wt') as f, gzip.open(output/'subset_1pct_rows.jsonl.gz', 'wt') as small:
        for i, e in enumerate(sorted(episodes, key=lambda e: (e.scene, e.episode_id))):
            count = Counter(); local_reasons = Counter()
            for r in episode_rows(e, tracks[e.episode_id], env, history):
                line = json.dumps(r, separators=(',', ':'))+'\n'
                f.write(line)
                if e.episode_id in nested_ids:
                    small.write(line)
                count[r['output_format']] += 1
                if 'label_reason' in r:
                    local_reasons[r['label_reason']] += 1
            summaries.append(dict(episode_id=e.episode_id, scene=e.scene, states=len(tracks[e.episode_id]['actions']),
                                  decisions=dict(count), click_reasons=dict(local_reasons), source=tracks[e.episode_id]['source']))
            totals.update(count);reasons.update(local_reasons)
            if e.episode_id in nested_ids:
                nested_totals.update(count);nested_reasons.update(local_reasons)
            if (i+1) % 200 == 0:
                print('row plans', i+1, '/', len(episodes), flush=True)
    env.close()
    result = dict(episodes=len(episodes), row_counts=dict(totals), click_reasons=dict(reasons),
                  decisions_per_episode={k:v/len(episodes) for k,v in totals.items()}, per_episode=summaries,
                  subset_1pct=dict(episodes=len(nested_ids), row_counts=dict(nested_totals), click_reasons=dict(nested_reasons),
                                   decisions_per_episode={k:v/len(nested_ids) for k,v in nested_totals.items()}),
                  fields=ROW_FIELDS, audit=audit, frame_status='BLOCKED_RENDERING', public_contract='BLOCKED_UNAVAILABLE',
                  click_stride='Advance by predicted controller primitive count along the supplied/reference GT state sequence; minimum 1; stop at first within-1m decision',
                  chunk_layout='K=1 physical [forward_metres, left_degrees, stop_probability]')
    write_json(output/'plan.json', result)
    return result
