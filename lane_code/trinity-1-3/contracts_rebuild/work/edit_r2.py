from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[1]
S=L/'work/src_r2'
def edit(rel,old,new):
    p=S/rel;s=p.read_text();assert old in s,(rel,old[:80]);p.write_text(s.replace(old,new))
def put(rel,text):
    (S/rel).write_text(text)

edit('trace_format/contracts.py','import re','import re\nimport math')
edit('trace_format/contracts.py',"_epoch = ContextVar('contract_epoch', default=True)","""_epoch = ContextVar('contract_epoch', default=True)
HEADING_PLANE_MIN_DEFAULT = 0.3
_heading_plane_min = ContextVar('heading_plane_min', default=HEADING_PLANE_MIN_DEFAULT)


def heading_plane_min(value=None):
    \"\"\"Read or validate the configuration-bound heading threshold.\"\"\"
    value = _heading_plane_min.get() if value is None else value
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value < 1:
        raise ValueError('heading_plane_min_must_be_finite_in_open_interval_0_1')
    return float(value)


def contract_identity():
    return dict(contract_epoch=True, heading_plane_min=heading_plane_min()) if new_contracts() else {}
""")
edit('trace_format/contracts.py','def contract_epoch(enabled=True):','def contract_epoch(enabled=True, *, heading_plane_min=None):')
edit('trace_format/contracts.py','    token = _epoch.set(enabled)','    threshold = globals()[\'heading_plane_min\'](heading_plane_min)\n    heading_token = _heading_plane_min.set(threshold)\n    token = _epoch.set(enabled)')
edit('trace_format/contracts.py','        _epoch.reset(token)','        _epoch.reset(token)\n        _heading_plane_min.reset(heading_token)')
p=S/'trace_format/contracts.py';s=p.read_text();s=s[:s.index('def heading_available(')]+'''def heading_available(geometry, frame=1):
    if not new_contracts():
        return True
    import numpy as np
    threshold = heading_plane_min()
    if getattr(geometry, 'down', None) is not None:
        down = np.asarray(geometry.down, float)
        down = down / np.linalg.norm(down)
        rotation = np.eye(3) if frame == 1 else geometry.camera(frame)[0]
        return bool(np.linalg.norm((np.asarray(rotation).T @ down)[:2]) >= threshold)
    if geometry is None or not hasattr(geometry, 'cam'):
        return True
    return bool(np.linalg.norm(np.asarray(geometry.cam(frame)[0])[2, :2]) >= threshold)


def partial_f1(values, number):
    """The public level frame has y up; only its horizontal components need heading."""
    return '(heading unavailable, '+number(values[1])+', heading unavailable)'
''';p.write_text(s)
for rel,old,new in [
 ('student_pilot/s1_grounding.py','contract_epoch, new_contracts','contract_epoch, new_contracts'),
 ('student_pilot/s1_grounding.py',"with contract_epoch(settings.get('contract_epoch', new_contracts())):","with contract_epoch(settings.get('contract_epoch', new_contracts()), heading_plane_min=settings.get('heading_plane_min')):"),
 ('student_pilot/s1_grounding.py','"allow_own_fallback", "contract_epoch"','"allow_own_fallback", "contract_epoch", "heading_plane_min"'),
 ('student_pilot/s1_routing.py','from trace_format.contracts import new_contracts','from trace_format.contracts import new_contracts, contract_identity'),
 ('student_pilot/s1_routing.py',"with contract_epoch(cfg.get('contract_epoch', new_contracts())):","with contract_epoch(cfg.get('contract_epoch', new_contracts()), heading_plane_min=cfg.get('heading_plane_min')):"),
 ('student_pilot/s1_routing.py',"**({'contract_epoch': True} if new_contracts() else {})","**contract_identity()"),
 ('student_pilot/ground_v3.py','from trace_format.contracts import new_contracts','from trace_format.contracts import new_contracts, heading_plane_min'),
 ('student_pilot/ground_v3.py','self.contract_epoch = new_contracts()','self.contract_epoch = new_contracts()\n        self.heading_plane_min = heading_plane_min()'),
 ('student_pilot/ground_v3.py',"self.config['contract_epoch'] = True","self.config['contract_epoch'] = True\n            self.config['heading_plane_min'] = self.heading_plane_min"),
 ('student_pilot/live_trace313.py','new_contracts, contract_epoch','new_contracts, contract_epoch, heading_plane_min, contract_identity'),
 ('student_pilot/live_trace313.py',"self.contract_epoch = getattr(backend, 'contract_epoch', new_contracts())","self.contract_epoch = getattr(backend, 'contract_epoch', new_contracts())\n        self.heading_plane_min = heading_plane_min(getattr(backend, 'heading_plane_min', None))"),
 ('student_pilot/live_trace313.py','with contract_epoch(self.contract_epoch):','with contract_epoch(self.contract_epoch, heading_plane_min=self.heading_plane_min):'),
 ('student_pilot/live_trace313.py',"**({'contract_epoch': True} if self.contract_epoch else {})","**contract_identity()"),
 ('student_pilot/live_trace313.py',"self.contract_epoch = next(iter(epochs), False)","self.contract_epoch = next(iter(epochs), False)\n        thresholds = {heading_plane_min(q.get('heading_plane_min', 0.3)) for q in queries}\n        if len(thresholds) > 1:\n            raise ValueError('replay_heading_plane_min_mismatch')\n        self.heading_plane_min = next(iter(thresholds), heading_plane_min())"),
 ('student_pilot/carrier_c1_decode.py',"with contract_epoch(getattr(session, 'contract_epoch', new_contracts())):","with contract_epoch(getattr(session, 'contract_epoch', new_contracts()),\n                        heading_plane_min=getattr(session, 'heading_plane_min', None)):"),
]:edit(rel,old,new)
# Effective defaults participate in the ON run identity; OFF preserves the sealed digest.
edit('student_pilot/carrier_c1_run.py',"    if 'readout' in value:","    if value.get('contract_epoch', True):\n        from trace_format.contracts import heading_plane_min\n        value['heading_plane_min'] = heading_plane_min(value.get('heading_plane_min', 0.3))\n    if 'readout' in value:")

# The head dispatcher never substitutes a ProfileGeometry for the actual head readout.
p=S/'student_pilot/carrier_c1_decode.py';s=p.read_text();a=s.index('        from trace_format.contracts import heading_available, status_text');b=s.index("        if call_text.startswith('<gap'):",a);s=s[:a]+s[b:];a=s.index('    from trace_format.contracts import heading_available',s.index('def _respond_state'));b=s.index('    heads=state.heads',a);s=s[:a]+s[b:];s=s.replace("actual_frame=call['frame'])['line']","actual_frame=call['frame'],\n                                               heading_defined=heading_available(geometry))['line']");s=s.replace("        call = parse_head(call_text)\n", "        from trace_format.contracts import heading_available\n        call = parse_head(call_text)\n");p.write_text(s)

# Separate camera transforms from level headings: depth and a destination centre never need yaw.
edit('student_pilot/carrier_c1_routing.py','        self.to_l1 = FLIP @ level_basis(np.eye(3), self.down).T', '''        from trace_format.contracts import new_contracts
        try:
            self.to_l1 = FLIP @ level_basis(np.eye(3), self.down).T
        except RenderError:
            if not new_contracts():
                raise
            # Private metric coordinates only. No horizontal component of this basis is published.
            right = np.array([1., 0., 0.])
            right -= (right @ self.down) * self.down
            right /= np.linalg.norm(right)
            self.to_l1 = np.stack((right, -self.down, np.cross(right, self.down)))''')
edit('student_pilot/carrier_c1_routing.py',"    def pose(self, k):",'''    def camera_pose(self, k):
        rotation, centre = self.camera(k)
        return dict(camera_R_L1=r8(self.to_l1 @ rotation), camera_t_L1=r8(self.to_l1 @ centre))

    def pose(self, k):''')
# click alone uses no level basis of the clicked frame.
p=S/'student_pilot/carrier_c1_routing.py';s=p.read_text();a=s.index('    def click(self,');b=s.index('\n\nclass RecordedGeometry',a);part=s[a:b].replace('pose = self.pose(k)','pose = self.camera_pose(k)');s=s[:a]+part+s[b:];p.write_text(s)
edit('student_pilot/carrier_c1_routing.py',"        p = self.pose(k)\n        return f\"f1 centre",'''        from trace_format.contracts import heading_available, partial_f1
        if not heading_available(self):
            p = self.camera_pose(k)
            return 'f1 centre '+partial_f1(p['camera_t_L1'], f2)+' m, yaw heading unavailable'
        if not heading_available(self, k):
            return f"f1 centre {vec(self.camera_pose(k)['camera_t_L1'])} m, yaw heading unavailable (frame {k})"
        p = self.pose(k)
        return f"f1 centre''')
edit('student_pilot/carrier_c1_routing.py',"        pi, pj = self.pose(i), self.pose(j)",'''        from trace_format.contracts import heading_available
        if not heading_available(self, i):
            delta = self.camera(j)[1] - self.camera(i)[1]
            return (f'dx = heading unavailable (frame {i}), dy = {s2(-self.down @ delta)} m, '
                    f'dz = heading unavailable (frame {i}), distance = {f2(np.linalg.norm(delta))} m')
        pi, pj = self.pose(i), self.camera_pose(j)''')
edit('student_pilot/carrier_c1_routing.py',"        a, b = (self.pose(k)['level_R_L1'][[0, 2], 2] for k in (i, j))",'''        from trace_format.contracts import heading_available
        missing = [k for k in dict.fromkeys((i, j)) if not heading_available(self, k)]
        if missing:
            return 'turn = heading unavailable (frames '+','.join(map(str, missing))+')'
        a, b = (self.pose(k)['level_R_L1'][[0, 2], 2] for k in (i, j))''')
edit('student_pilot/carrier_c1_routing.py',"if not recorded and not heading_available(geometry):","if not recorded and (not heading_available(geometry) or\n                        any(not heading_available(geometry, k) for k in (call['arguments'].get('frame', 1),\n                            call['arguments'].get('from', 1), call['arguments'].get('to', 1)))):")

# Calculators retain private metric operands; only text is injected into the language model.
# Both deployed import paths use precisely the same implementation.
edit('trace_format/calculator.py','actual_frame=None, label=None):','actual_frame=None, label=None, heading_defined=True):')
edit('trace_format/calculator.py','        line = (f"{expected}: cam', '''        from .contracts import partial_f1
        public_f1 = _vec_text(point) if heading_defined else partial_f1(point, lambda x: f'{x:.2f}')
        line = (f"{expected}: cam''')
edit('trace_format/calculator.py','f1 {_vec_text(point)} m;','f1 {public_f1} m;')
edit('trace_format/calculator.py','        published = _json(point)','        if not heading_defined:\n            point["heading_defined"] = False\n        published = _json(point)')
edit('trace_format/calculator.py','        return _json({"api_version": API_VERSION,', '''        if op in ('angle', 'turn') and any(not points[p].get('heading_defined', True) for p in refs):
            text = 'u heading unavailable; v heading unavailable; '+text.split('; dot ', 1)[1].join(['dot ', ''])
        return _json({"api_version": API_VERSION,''')
put('student_pilot/p3_printed_calculator.py','"""Shared deployed calculator; geometry operands stay private, only response text is injected."""\nfrom trace_format.calculator import *\n')

# Keep per-camera and vertical observations when the reference heading is undefined.
edit('student_pilot/ground_lifting.py','def public_centres(geometry, frame, centre):','def public_centres(geometry, frame, centre, *, metric_only=False):')
edit('student_pilot/ground_lifting.py','    if not heading_available(geometry):\n        raise ValueError', '    if not metric_only and not heading_available(geometry):\n        raise ValueError')
edit('student_pilot/ground_lifting.py',"    if np.linalg.norm(heading) < 1e-6:\n        raise ValueError('Undefined level basis')", "    if np.linalg.norm(heading) < 1e-6:\n        if not metric_only:\n            raise ValueError('Undefined level basis')\n        camera = (R.T @ (centre - t)) * [1, -1, 1]\n        return camera, (centre - t1)[[0, 2, 1]]")
edit('student_pilot/ground_lifting.py',"            R, t = geometry.cam(best)\n            camera = (np.asarray(R).T @ (centre-t)) * [1, -1, 1]\n            f1 = None", "            camera, f1 = public_centres(geometry, best, centre, metric_only=True)")
edit('student_pilot/ground_lifting.py',"    if result.get('heading_unavailable'):\n        size = 'size unavailable' if result['size'] is None else 'size ' + ' x '.join(number(x) for x in result['size']) + ' m'\n        return status_text('heading unavailable', result['name']) + '\\n' + size\n",'')
edit('student_pilot/ground_lifting.py',"spread=float(number(result['spread'])), requested_frame=result['best'])", "spread=float(number(result['spread'])), requested_frame=result['best'],\n                              heading_defined=not result.get('heading_unavailable', False))")
edit('student_pilot/ground_lifting.py',"p = self.geometry.pose(frame)","p = self.geometry.camera_pose(frame)")
edit('trace_format/ground_v313.py','camera, f1 = backend.public_centres(geometry, frame, np.asarray(position, float))',"camera, f1 = backend.public_centres(geometry, frame, np.asarray(position, float),\n                                        **({'metric_only': True} if not heading_available(geometry) else {}))")
edit('trace_format/ground_v313.py','spread=0., requested_frame=int(frame))','spread=0., requested_frame=int(frame),\n                              heading_defined=heading_available(geometry))')
edit('trace_format/ground_v313.py','if not self.witness_points or not heading_available(self.geometry):','if not self.witness_points:')
edit('trace_format/ground_v313.py',"        if not heading_available(self.geometry):\n            return status_text('heading unavailable')\n",'')
edit('trace_format/ground_v313.py',"            if not heading_available(self.geometry):\n                body += '\\n'+status_text('heading unavailable')\n",'')
edit('trace_format/ground_v313.py','enumerate(entries if heading_available(self.geometry) else [], 1)','enumerate(entries, 1)')

# Box observations keep labels, support, lengths, and height. Private boxes still drive gaps.
edit('trace_format/box_v313.py',"            sizes = []\n            for value in values:","            partial = []\n            from .contracts import partial_f1\n            for obj, value, meta, label in zip(entries, values, metadata, session.box_registry.bindings[name]):")
edit('trace_format/box_v313.py',"                sizes.append('size '+' x '.join(number(v,2) for v in value['lengths'][order])+' m')\n            return status_text('heading unavailable',name)+'\\n'+'\\n'.join(sizes)","""                height = value['centre'][2] - session.geometry.cam(1)[1][2]
                partial.append('\\n'.join([
                    f'{name}: frames '+','.join(map(str,meta['frames']))+f\" (best {meta['best']})\",
                    f'{label}: f1 centre '+partial_f1([0, height, 0], lambda x: number(x,2))+' m',
                    'size '+' x '.join(number(v,2) for v in value['lengths'][order])+' m',
                    'yaw heading unavailable']))
            return partial[0] if len(partial)==1 else '\\n'.join([f'{name}: {len(partial)} instances', *partial])""")
# Mixed-field statuses remain recognizable for training admission and private audit replay.
edit('trace_format/contracts.py',"            if line == status or line.endswith(': '+status) or line.endswith(' '+status):", "            if (line == status or line.endswith(': '+status) or line.endswith(' '+status)\n                    or (status == 'heading unavailable' and status in line)):")
# Grammar accepts a partial coordinate only in a coordinate position, never arbitrary text.
edit('student_pilot/live_trace313.py',"    if call.startswith('<ground'):","""    if 'heading unavailable' in body and call.startswith('<ground'):
        # Check the full existing grammar with only withheld components restored as placeholders.
        normalized = body.replace('heading unavailable', '0.00')
        normalized = normalized.replace('yaw 0.00', 'yaw 0 deg (0 = +x; positive +x toward -z about +y)')
        if not body.startswith(re.search(r'obj=\"([^\"]+)\"',call)[1]+': heading unavailable'):
            return parse_response(call, normalized, program_version)
    if call.startswith('<ground'):""")
