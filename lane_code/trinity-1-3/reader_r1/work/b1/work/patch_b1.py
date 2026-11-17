from pathlib import Path
P=Path('work/p')
def edit(name,a,b):
 p=P/name;s=p.read_text();assert a in s,(name,a);p.write_text(s.replace(a,b))
edit('b/e2e_reader/stage1.py','def __init__(self, detect, head, geometry):','def __init__(self, detect, head, geometry, rule="null_argmax"):\n        if rule not in ("null_argmax", "candidates_argmax"):\n            raise ValueError("unknown_stage1_select_rule")\n        self.rule = rule\n        self.diagnostics = {}')
edit('b/e2e_reader/stage1.py','proposals, _ = F.candidates.lift','proposals, rejected = F.candidates.lift')
edit('b/e2e_reader/stage1.py','        return accepted, x','''        self.diagnostics[name] = proposal_diagnostics(
            self.rule, name, self.raw[name], proposals, rejected, accepted, x)
        return accepted, x''')
edit('b/e2e_reader/stage1.py',"        slots = self.head.with_null(inputs['x'], None, inputs['name'])\n        k = int(torch.argmax(slots))\n        return -1 if k == len(slots) - 1 else k",'''        if self.rule == 'candidates_argmax' and len(inputs['x']) == 0:
            return -1
        slots = self.head.with_null(inputs['x'], None, inputs['name'])
        k = int(torch.argmax(slots))
        choice = -1 if k == len(slots) - 1 else k
        if self.rule == 'candidates_argmax':
            choice = int(torch.argmax(slots[:len(inputs['x'])]))
        if inputs['name'] in self.diagnostics:
            record = self.diagnostics[inputs['name']]
            for candidate, logit in zip(record['candidates'], slots):
                candidate['logit'] = float(logit)
            record.update(null_logit=float(slots[-1]), chosen_index=choice,
                          null_would_win=k == len(slots) - 1)
        return choice''')
edit('b/e2e_reader/stage1.py','def stage1_factory(sam3_tower, selector_head, anchor_frames_of):','''def proposal_diagnostics(rule, name, raw, proposals, rejected, accepted, vectors):
    """Observe producers without changing any candidate, feature or response."""
    from collections import Counter
    flat = [entry for frame in raw for entry in frame]
    return dict(rule=rule, name_key=name_key(name), sam3=dict(
        kept_per_frame=[len(frame) for frame in raw],
        max_score=max((float(e['score']) for e in flat), default=None),
        max_presence=max((float(e['presence']) for e in flat), default=None),
        max_joint=max((float(e['score'])*float(e['presence']) for e in flat), default=None)),
        lift_entering=len(proposals)+len(rejected), lifted=len(proposals),
        rejections=dict(Counter(entry['reason'] for entry in rejected)),
        linked_candidates=len(accepted), candidates=[dict(
            id=a['candidate_id'], frames=list(a['masks']), peak=float(a['features']['peak']),
            logit=None, inputs=np.asarray(x, dtype=np.float32).tolist())
            for a, x in list(zip(accepted, vectors))[:K1_CONTRACT['cap']]],
        null_logit=None, chosen_index=-1, null_would_win=None)


def stage1_factory(sam3_tower, selector_head, anchor_frames_of, rule='null_argmax'):''')
edit('b/e2e_reader/stage1.py','s = StageOne(detect, selector_head, geometry)','s = StageOne(detect, selector_head, geometry, rule=rule)')
edit('b/e2e_reader/grounding.py',"        self.queries = []","        self.queries = []\n        self.stage1 = getattr(getattr(propose, '__self__', None), 'diagnostics', {})")
edit('b/e2e_reader/servers.py',"        return text, dict(kind=kind, spec_version=session.spec_version, spec_revision=1,\n                          audit=deepcopy(session.events[-1].get('audit', {})))",'''        info = dict(kind=kind, spec_version=session.spec_version, spec_revision=1,
                    audit=deepcopy(session.events[-1].get('audit', {})))
        socket = getattr(session, 'socket', None)
        if socket is not None:
            from trace_format import box_v313 as boxes
            if kind == 'ground' and (match := boxes.GROUND.fullmatch(call)):
                info['stage1'] = deepcopy(socket.stage1.get(match[1], {}))
            elif kind == 'gap':
                import re
                names = re.findall(r'"([^"]*)"', call)
                info['stage1'] = dict(operands=[dict(name_key=name,
                    state=session.box_registry.states.get(name),
                    stage1=deepcopy(socket.stage1.get(name, {}))) for name in names
                    if name in session.box_registry.states or name in socket.stage1])
        return text, info''')
edit('h1eval/h10/perception_own.py','self.socket = stage1_factory(*cached, anchor_frames)',"self.socket = stage1_factory(*cached, anchor_frames,\n                                         rule=self.settings.get('stage1_select_rule', 'null_argmax'))")
edit('h1eval/h10/launch.py',"                 r0_pin=manifest['r0_check']['pin'])","                 r0_pin=manifest['r0_check']['pin'],\n                 stage1_select_rule=(settings or {}).get('stage1_select_rule', 'null_argmax'),\n                 save_own_depth=(settings or {}).get('save_own_depth', True))")
edit('h1eval/h10/launch.py',"                            row=dict(id=item['id'],room_key=item['room_key'],type=item['question_type'],",'''                            if arm=='own' and bound and binding['save_own_depth']:
                                from .depth_snapshot import save
                                snapshot=save(out, item['id'], key, bound[-1].last)
                                if snapshot is not None:output={**output, 'own_depth':snapshot}
                            row=dict(id=item['id'],room_key=item['room_key'],type=item['question_type'],''')
# Retain the already queried arrays; dumping never re-queries a depth head.
edit('h1eval/perception.py',"                built.update(servers=servers,geometry=geometry)","                built.update(servers=servers,geometry=geometry)")
(P/'h1eval/h10/depth_snapshot.py').write_text('''"""Persist own geometry after generation, outside the reader's audited decision path."""
import hashlib
from pathlib import Path
import numpy as np


def save(output, item_id, mode, state):
    geometry = state.get('geometry')
    if geometry is None:
        return None
    heads = state['heads']
    key = hashlib.sha256((item_id + '\\0' + mode).encode()).hexdigest()
    path = Path(output) / 'own_depth' / (key + '.npz')
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, depth_grid=np.asarray(geometry.depth_grid, dtype=np.float16),
             grid_uv=np.asarray(geometry.grid_uv), pose9=np.asarray(heads.pose9),
             gravity=np.asarray(heads.gravity), K=geometry.contract.K,
             canvas_to_source=geometry.contract.canvas_to_source,
             camera_to_world=geometry.contract.camera_to_world,
             anchor_frame_indices=geometry.contract.frame_map.indices)
    return dict(path=str(path.relative_to(output)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                dtype='float16', shape=list(geometry.depth_grid.shape))
''')
