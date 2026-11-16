from pathlib import Path
import ast
import difflib
import hashlib
import json
import shutil

L = Path(__file__).resolve().parents[1]
BASE = L/'work/base/work/base/tree_b01ce449'
SRC = L/'work/src'
groups = {}

def put(group, name, text):
    path = SRC/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    groups.setdefault(group, []).append(name)

def edit(group, name, pairs):
    text = (BASE/name).read_text()
    for old, new in pairs:
        assert old in text, (name, old[:100])
        text = text.replace(old, new)
    put(group, name, text)

put('geometry', 'trace_format/contracts.py', '''"""Epoch selection and public failure grammar shared by serving and row rendering."""
from contextlib import contextmanager
from contextvars import ContextVar
import re

_epoch = ContextVar('contract_epoch', default=True)
RUNTIME_STATUSES = ('unresolved', 'not seen', 'box unavailable', 'heading unavailable',
                    'frame unavailable', 'size unavailable', 'unavailable')


def new_contracts():
    return _epoch.get()


@contextmanager
def contract_epoch(enabled=True):
    if type(enabled) is not bool:
        raise ValueError('contract_epoch_must_be_boolean')
    token = _epoch.set(enabled)
    try:
        yield
    finally:
        _epoch.reset(token)


def geometry_mode(session):
    mode = getattr(session, 'geometry_mode', 'sensor')
    if mode not in ('sensor', 'predicted'):
        raise ValueError('unknown_geometry_mode')
    return mode


def response_status(text):
    if not isinstance(text, str) or not text.strip():
        return 'missing response'
    text = text.strip().removeprefix('<tool_response>').removesuffix('</tool_response>').strip()
    for line in text.splitlines():
        line = line.strip()
        if 'error:' in line.lower():
            return 'error'
        for status in RUNTIME_STATUSES:
            if line == status or line.endswith(': '+status) or line.endswith(' '+status):
                return status
    return 'ok'


def status_text(status, name=None):
    if status not in RUNTIME_STATUSES:
        raise ValueError('unknown_runtime_status')
    return (name + ': ' if name else '') + status


def heading_available(geometry):
    if not new_contracts():
        return True
    import numpy as np
    from student_pilot.geometry_profiles import UP_PLANE_MIN
    if getattr(geometry, 'down', None) is not None:
        return bool(np.linalg.norm(np.asarray(geometry.down)[:2]) >= UP_PLANE_MIN)
    if geometry is None or not hasattr(geometry, 'cam'):
        return True
    return bool(np.linalg.norm(np.asarray(geometry.cam(1)[0])[2, :2]) >= UP_PLANE_MIN)
''')

ref = (L/'work/ref/gravity_guard_a62e3975_recovered.py').read_text()
fn = next(n for n in ast.parse(ref).body if isinstance(n, ast.FunctionDef) and n.name == 'validate_up_convention')
guard = ast.get_source_segment(ref, fn)
edit('geometry', 'student_pilot/geometry_profiles.py', [
    ('from .scene_state import FrameMap, digest', 'from .scene_state import FrameMap, digest\nfrom trace_format.contracts import new_contracts'),
    ('PROFILES = {', 'UP_PLANE_MIN = .3\n\n\n'+guard+'\n\n\nPROFILES = {'),
    ("        if -R[0, 2, 1] <= 0:\n", "        if new_contracts():\n            validate_up_convention(R)\n        elif -R[0, 2, 1] <= 0:\n"),
])
edit('geometry', 'student_pilot/ground_lifting.py', [
    ('import math\n', 'import math\nfrom trace_format.contracts import heading_available, status_text\n'),
    ('    R, t = (np.asarray(x, dtype=np.float64) for x in geometry.cam(frame))', "    if not heading_available(geometry):\n        raise ValueError('heading unavailable')\n    R, t = (np.asarray(x, dtype=np.float64) for x in geometry.cam(frame))"),
    ('        camera, f1 = public_centres(geometry, best, centre)', "        if heading_available(geometry):\n            camera, f1 = public_centres(geometry, best, centre)\n        else:\n            R, t = geometry.cam(best)\n            camera = (np.asarray(R).T @ (centre-t)) * [1, -1, 1]\n            f1 = None\n            result['heading_unavailable'] = True"),
    ('f1=f1.tolist(), size=size', 'f1=None if f1 is None else f1.tolist(), size=size'),
    ('    # Registry decimal arithmetic must consume exactly the displayed values.', "    if result.get('heading_unavailable'):\n        size = 'size unavailable' if result['size'] is None else 'size ' + ' x '.join(number(x) for x in result['size']) + ' m'\n        return status_text('heading unavailable', result['name']) + '\\n' + size\n    # Registry decimal arithmetic must consume exactly the displayed values."),
])

edit('geometry', 'trace_format/box_v313.py', [
    ('from . import ground_v312 as old', 'from . import ground_v312 as old\nfrom .contracts import RUNTIME_STATUSES, heading_available, status_text, response_status'),
    ("for status in ('unresolved','not seen','box unavailable'):", 'for status in RUNTIME_STATUSES:'),
    ("failure=re.fullmatch(re.escape(m[1])+r': (not seen|unresolved|box unavailable)',body)", "failure=re.fullmatch(re.escape(m[1])+r': ('+'|'.join(map(re.escape,RUNTIME_STATUSES))+')',body)"),
    ("    R,t=(np.asarray(v,float) for v in geometry.cam(1))\n", "    if not heading_available(geometry):\n        # Private metric operands stay in the existing world frame; none are printed.\n        return np.asarray(geometry.cam(k)[1],float)\n    R,t=(np.asarray(v,float) for v in geometry.cam(1))\n"),
])
# in_f1 has no k; replace its inserted camera clause with the metric box clause.
p = SRC/'trace_format/box_v313.py'
t = p.read_text().replace("def in_f1(geometry, centre, lengths, axes):\n    if not heading_available(geometry):\n        # Private metric operands stay in the existing world frame; none are printed.\n        return np.asarray(geometry.cam(k)[1],float)", "def in_f1(geometry, centre, lengths, axes):\n    if not heading_available(geometry):\n        return box(centre, lengths, np.asarray(axes).reshape(3,3))")
t = t.replace("    def audit_labels(self, name):", '''    def ingest_metric(self, name, values, gaps, metadata):
        labels = []
        for value, gap, meta in zip(values, gaps, metadata):
            label = f'B{len(self.records)+1}'
            self.records[label] = dict(name=name, label=label, value=box(**value),
                gap_value=box(**gap), **meta)
            labels.append(label)
        self.bindings[name] = labels
        self.states[name] = 'ok'

    def audit_labels(self, name):''')
t = t.replace("    blocks,values,gaps,tags,metadata=[],[],[],[],[]", "    blocks,values,gaps,tags,metadata=[],[],[],[],[]\n    metric_only = not heading_available(session.geometry)")
t = t.replace("if session.spec_version == '3.13':", "if session.spec_version == '3.13' and not metric_only:")
t = t.replace("metadata.append(dict(areas=obj['areas'], instance_id=str(obj.get('instance_id',label))))", "metadata.append(dict(areas=obj['areas'], instance_id=str(obj.get('instance_id',label)), **(dict(frames=obj['frames'], best=best, gap_operand=tag) if metric_only else {})))")
t = t.replace("blocks.append(serialize(name,label,obj['frames'],best,value));values.append(value);gaps.append(gvalue);tags.append(tag)", "blocks.append('' if metric_only else serialize(name,label,obj['frames'],best,value));values.append(value);gaps.append(gvalue);tags.append(tag)")
t = t.replace("        body=blocks[0] if len(blocks)==1", '''        if metric_only:
            session.box_registry.ingest_metric(name, values, gaps, metadata)
            sizes = []
            for value in values:
                vertical = int(np.argmax(np.abs(value['axes'][:,2])))
                order = [i for i in range(3) if i != vertical] + [vertical]
                sizes.append('size '+' x '.join(number(v,2) for v in value['lengths'][order])+' m')
            return status_text('heading unavailable',name)+'\\n'+'\\n'.join(sizes)
        body=blocks[0] if len(blocks)==1''')
# Public audit replay reconstitutes private operands without parsing nonexistent coordinates.
t = t.replace("            if failure:registry.invalidate(m[1],failure[1])", """            if response_status(body) == 'heading unavailable' and event['audit'].get('metric_only'):
                audit = event['audit']
                registry.ingest_metric(m[1], audit['metric_values'], audit['metric_gaps'], audit['metric_metadata'])
            elif failure:registry.invalidate(m[1],failure[1])""")
t = t.replace("if session.box_registry.states[name]!='ok':failure=(name,session.box_registry.states[name]);break", "if response_status(body)!='ok':failure=(name,response_status(body));break")
# The disabled camera renderer still uses the same status contract if invoked for replay.
t = t.replace("        emit(f'<ground obj=", "        body=emit(f'<ground obj=")
p.write_text(t)

edit('geometry', 'trace_format/ground_v313.py', [
    ('from .program_errors import ProgramRefusal', 'from .program_errors import ProgramRefusal\nfrom .contracts import heading_available, status_text, response_status'),
    ('        if not self.witness_points:', '        if not self.witness_points or not heading_available(self.geometry):'),
    ("        if not self.keypoint_calls:\n", "        if not heading_available(self.geometry):\n            return status_text('heading unavailable')\n        if not self.keypoint_calls:\n"),
    ('            for ordinal, obj in enumerate(entries, 1):', "            for ordinal, obj in enumerate(entries if heading_available(self.geometry) else [], 1):"),
    ("            body = f'{name}: {len(entries)} found'", "            body = f'{name}: {len(entries)} found'\n            if not heading_available(self.geometry):\n                body += '\\n'+status_text('heading unavailable')"),
    ("            policy=self.box_provider_id==boxes.POLICY_ID", """            if not heading_available(self.geometry):
                private.update(metric_only=True, metric_values=[boxes.audit_box(r['value']) for r in records],
                    metric_gaps=[boxes.audit_box(r['gap_value']) for r in records],
                    metric_metadata=[{k:r[k] for k in ('frames','best','areas','instance_id','gap_operand')} for r in records])
            policy=self.box_provider_id==boxes.POLICY_ID"""),
])

edit('geometry', 'student_pilot/live_trace313.py', [
    ('from .p3_printed_calculator import PrintedPointRegistry', 'from .p3_printed_calculator import PrintedPointRegistry\nfrom trace_format.contracts import RUNTIME_STATUSES, response_status, new_contracts, contract_epoch'),
    ('        self.owner=backend', "        self.contract_epoch = getattr(backend, 'contract_epoch', new_contracts())\n        self.owner=backend"),
    ('    def _room(self):\n', "    def execute(self, call):\n        with contract_epoch(self.contract_epoch):\n            return super().execute(call)\n\n    def _room(self):\n"),
    ("query.update(geometry_mode=self.geometry_mode, box_provider_id=self.box_provider_id)", "query.update(geometry_mode=self.geometry_mode, box_provider_id=self.box_provider_id, **({'contract_epoch': True} if self.contract_epoch else {}))"),
    ("        modes = {query.get('geometry_mode', 'sensor') for query in queries}", "        epochs = {q.get('contract_epoch', False) for q in queries}\n        if len(epochs) > 1:\n            raise ValueError('replay_contract_epoch_mismatch')\n        self.contract_epoch = next(iter(epochs), False)\n        modes = {query.get('geometry_mode', 'sensor') for query in queries}"),
    ("        if body in [name+': '+s for s in ('not seen','unresolved','box unavailable')]:return", "        if body in [name+': '+s for s in RUNTIME_STATUSES]:return\n        if body.startswith(name+': heading unavailable\\n') and all(\n                line == 'size unavailable' or re.fullmatch(r'size [0-9]+\\.[0-9]{2} x [0-9]+\\.[0-9]{2} x [0-9]+\\.[0-9]{2} m', line) for line in body.splitlines()[1:]):return"),
    ("        if 'mode=\"instances\"' in call:\n", "        if 'mode=\"instances\"' in call:\n            if re.fullmatch(re.escape(name)+r': (0|[1-9][0-9]*) found\\nheading unavailable', body):return\n"),
    ("        if body in ('not seen','unresolved','box unavailable'):return", "        if body in RUNTIME_STATUSES:return"),
    ("    return dict(calls=len(record['calls']),mismatches=mismatches,byte_equal=not mismatches and not session.pending,", "    from collections import Counter\n    statuses = Counter(response_status(call['response']) for call in record['calls'])\n    metrics = dict(response_statuses=dict(statuses), ok_responses=statuses['ok']) if session.contract_epoch else {}\n    return dict(**metrics, calls=len(record['calls']),mismatches=mismatches,byte_equal=not mismatches and not session.pending,"),
])
# Preserve per-query epoch for room-only replay too.
p = SRC/'student_pilot/live_trace313.py'
t = p.read_text().replace("self.queries.append(dict(kind='room', geometry_mode=self.geometry_mode,", "self.queries.append(dict(kind='room', geometry_mode=self.geometry_mode, **({'contract_epoch': True} if self.contract_epoch else {}),")
p.write_text(t)

edit('geometry', 'student_pilot/carrier_c1_decode.py', [
    ("    try:\n        if call_text.startswith('<gap'):", """    try:
        from trace_format.contracts import heading_available, status_text
        if (call_text.startswith(('<depth_at', '<pose', '<move', '<turn', '<angle'))
                and not heading_available(geometry)):
            text = status_text('heading unavailable')
            if call_text.startswith('<move'):
                call = parse_head(call_text)
                camera = getattr(geometry, 'camera', getattr(geometry, 'cam', None))
                if camera is not None:
                    import numpy as np
                    distance = np.linalg.norm(camera(call['j'])[1]-camera(call['i'])[1])
                    text += '\\ndistance = '+routing.f2(distance)+' m'
            return text, dict(kind='head', status='heading unavailable')
        if call_text.startswith('<gap'):"""),
    ('def respond_state(state,call_text,registry):', '''def respond_state(state,call_text,registry):
    from trace_format.contracts import contract_epoch, new_contracts
    session = getattr(state, 'live_trace_session', None)
    with contract_epoch(getattr(session, 'contract_epoch', new_contracts())):
        return _respond_state(state,call_text,registry)


def _respond_state(state,call_text,registry):'''),
    ('    if formatted is not None:return formatted\n    heads=state.heads', '''    if formatted is not None:return formatted
    from trace_format.contracts import heading_available
    session = getattr(state, 'live_trace_session', None)
    if (session is not None and not heading_available(session.geometry)
            and call_text.startswith(('<depth_at', '<pose', '<move', '<turn', '<angle'))):
        return respond(call_text, registry, session.geometry)
    heads=state.heads'''),
])

edit('geometry', 'student_pilot/carrier_c1_routing.py', [
    ("                if name == 'depth_at':\n", "                from trace_format.contracts import heading_available\n                if not recorded and not heading_available(geometry):\n                    from .carrier_c1_decode import respond\n                    text, _ = respond(call['token'], registry, geometry)\n                elif name == 'depth_at':\n"),
])

# Generators execute the runtime formatter rather than maintaining another geometry implementation.
for module in ('ground_v313', 'box_v313'):
    original = (BASE/f'generator/derivgen_v7/derivgen/{module}.py').read_text()
    original = original.replace("for status in ('unresolved','not seen','box unavailable'):", 'for status in RUNTIME_STATUSES:')
    original = original.replace("r': (not seen|unresolved|box unavailable)'", "r': ('+'|'.join(map(re.escape,RUNTIME_STATUSES))+')'")
    original = original.replace("        emit(f'<ground obj=", "        body=emit(f'<ground obj=")
    original = original.replace("if session.box_registry.states[name]!='ok':failure=(name,session.box_registry.states[name]);break", "if response_status(body)!='ok':failure=(name,response_status(body));break")
    # Keep generator-only rendering and helpers; bind session/provider entry points at module end.
    exports = ('Session, point_line, witness_pair, surface_support, GTInstances' if module=='ground_v313' else
        'BoxRegistry, ground, replay_audit, cam_gap_body, camera_centre_f1, in_f1, FittedBoxProvider, FusedBoxProvider')
    footer = '''
# Training executes the deployed formatter; epoch OFF retains sealed replay.
from trace_format.contracts import RUNTIME_STATUSES, response_status, new_contracts
from trace_format import MODULE as _runtime

def _epoch_dispatch(sealed, current):
    def call(*args, **kwargs):
        return (current if new_contracts() else sealed)(*args, **kwargs)
    return call

'''.replace('MODULE',module)
    for export in exports.split(', '):
        footer += f'{export} = _epoch_dispatch({export}, _runtime.{export})\n'
    put('geometry', f'generator/derivgen_v7/derivgen/{module}.py', original + footer)

# Candidate contract.
put('candidates', 'student_pilot/phrases.py', '''"""Open-vocabulary operand identity. Aliases retain their full referring phrase."""
import re
import unicodedata
from trace_format.contracts import new_contracts

SINGULAR = {'shelves':'shelf', 'bookshelves':'bookshelf', 'clothes':'clothing',
            'blinds':'window blind', 'people':'person', 'mice':'mouse'}
UNCHANGED = {'glass','grass','gas','canvas','status','stairs','pants','trousers','scissors',
             'series','species','news'}


def normalize_phrase(name):
    if not isinstance(name, str) or not name.strip() or any(
            ord(c) < 32 or ord(c) == 127 or c in '<>"' for c in name):
        raise ValueError('invalid_object_name')
    text = ' '.join(unicodedata.normalize('NFKC',name).casefold().replace('_',' ').split())
    prefix, _, word = text.rpartition(' ')
    if word in SINGULAR:
        word = SINGULAR[word]
    elif word not in UNCHANGED:
        if word.endswith('ies') and len(word) > 3:
            word = word[:-3]+'y'
        elif word.endswith(('ches','shes','xes','zes')):
            word = word[:-2]
        elif word.endswith('s') and not word.endswith(('ss','us','is')):
            word = word[:-1]
    return (prefix+' ' if prefix else '')+word


def phrase_set(names):
    return tuple(sorted({normalize_phrase(n) for n in names}))


def annotation_phrase(name):
    if new_contracts():
        return normalize_phrase(name)
    return ' '.join(unicodedata.normalize('NFKC', str(name)).casefold().split())


def annotation_labels(name, labels, sealed_match):
    if not new_contracts():
        return sealed_match(name, labels)
    return [label for label in labels if normalize_phrase(label) == normalize_phrase(name)]


def candidate_phrases(question, options=(), cache_phrases=None):
    # Cache phrases are the capture-wide competition universe, including names
    # not mentioned in this particular question. Admission checks that same set.
    if cache_phrases is not None:
        return phrase_set(cache_phrases)
    # Native MDG has no phrase cache. Parse source question operands, not labels.
    from generator.derivgen_v7.derivgen.bindings import parse_f17
    from types import SimpleNamespace
    from trace_format.ground_v312 import option_map
    kinds = ('absolute_distance_object','relative_distance_object','absolute_size_object',
             'relative_direction_object','absolute_direction_object','absolute_count','relative_count')
    for kind in kinds:
        roles = parse_f17(dict(question=question, question_type=kind, options=list(options)),
                          SimpleNamespace(option_texts=option_map))
        if roles:
            values = [v for k,v in roles.items() if k != 'parser']
            return phrase_set(n for v in values for n in (v if isinstance(v,list) else [v]) if isinstance(n,str))
    values = list(option_map(list(options)).values()) if options else []
    # Common distance wording also used by the native head's prompt.
    match = re.search(r'(?:distance between|far is) (?:the )?(.+?) (?:and|from) (?:the )?(.+?)(?:[?.]|$)', question, re.I)
    if match:
        values.extend(match.groups())
    return phrase_set(values)


def cache_key(cache, name):
    wanted = normalize_phrase(name)
    keys = [key for key in cache['phrases'] if normalize_phrase(key) == wanted]
    if len(keys) > 1:
        raise ValueError('duplicate_normalized_cache_phrase')
    return keys[0] if keys else wanted
''')

edit('candidates', 'student_pilot/scene_state.py', [
    ('def normalize_name(name):\n', "def normalize_name(name):\n    from trace_format.contracts import new_contracts\n    if new_contracts():\n        from .phrases import normalize_phrase\n        return normalize_phrase(name)\n"),
])
edit('candidates', 'student_pilot/sam3_tower.py', [
    ("    label = ' '.join(label.lower().replace('_', ' ').split())", "    from trace_format.contracts import new_contracts\n    if new_contracts():\n        from .phrases import normalize_phrase as shared_phrase\n        return shared_phrase(label)\n    label = ' '.join(label.lower().replace('_', ' ').split())"),
])
edit('candidates', 'student_pilot/ground_admission.py', [
    ("    return ' '.join(unicodedata.normalize('NFKC', name).casefold().split())", "    from trace_format.contracts import new_contracts\n    if new_contracts():\n        from .phrases import normalize_phrase\n        return normalize_phrase(name)\n    return ' '.join(unicodedata.normalize('NFKC', name).casefold().split())"),
])
edit('candidates', 'student_pilot/s1_grounding.py', [
    ('def candidate_names(question, options):', 'def candidate_names(question, options, cache_phrases=None):\n    from trace_format.contracts import new_contracts\n    if new_contracts():\n        from .phrases import candidate_phrases\n        return candidate_phrases(question, options, cache_phrases)'),
    ('def build_backend(row, batch, artifact_pin, audit_dir, settings=None):', '''def build_backend(row, batch, artifact_pin, audit_dir, settings=None):
    from trace_format.contracts import contract_epoch, new_contracts
    settings = settings or {}
    with contract_epoch(settings.get('contract_epoch', new_contracts())):
        return _build_backend(row, batch, artifact_pin, audit_dir, settings)


def _build_backend(row, batch, artifact_pin, audit_dir, settings=None):'''),
    ('"allow_own_fallback"}', '"allow_own_fallback", "contract_epoch"}'),
    ('names = candidate_names(inputs["question"], inputs.get("options") or [])', 'names = candidate_names(inputs["question"], inputs.get("options") or [],\n                            batch.get("cache_phrases", row.get("candidate_phrases")))'),
])
edit('candidates', 'student_pilot/ground_v3.py', [
    ("        self.config['candidate_universe'] = sorted(getattr(source,'names',()))", """        from trace_format.contracts import new_contracts
        from .phrases import phrase_set
        self.contract_epoch = new_contracts()
        names = getattr(source, 'cache', {}).get('phrases', getattr(source,'names',()))
        self.config['candidate_universe'] = list(phrase_set(names)) if self.contract_epoch else sorted(getattr(source,'names',()))
        if self.contract_epoch:
            self.config['contract_epoch'] = True"""),
])
edit('candidates', 'student_pilot/ground_sources.py', [
    ('from .scene_state import normalize_name', 'from .scene_state import normalize_name\nfrom .phrases import cache_key\nfrom trace_format.contracts import new_contracts\n\ndef cache_phrase(cache, name, codec):\n    return cache_key(cache, name) if new_contracts() else codec.phrase(name)\n'),
    ('phrase = codec.phrase(name)', 'phrase = cache_phrase(cache, name, codec)'),
    ("self.reader.phrase(name)", "cache_phrase(self.cache, name, self.reader)"),
    ("phrase = self.codec.phrase(name)", "phrase = normalize_name(name) if new_contracts() else self.codec.phrase(name)"),
])
edit('candidates', 'student_pilot/routed_features.py', [
    ('from . import routed_candidates as candidates', 'from . import routed_candidates as candidates\nfrom .ground_sources import cache_phrase\nfrom .scene_state import normalize_name'),
    ('codec.phrase(name)', 'cache_phrase(cache, name, codec)'),
    ('def select_instances(owner, name, exact_geometry):', 'def select_instances(owner, name, exact_geometry):\n    from trace_format.contracts import new_contracts\n    if new_contracts():\n        name = normalize_name(name)'),
])
edit('candidates', 'ofs/core.py', [
    ('    from rk.sam3mask import tower\n    phrase = tower().phrase(name)', "    from trace_format.contracts import new_contracts\n    from student_pilot.phrases import cache_key\n    if new_contracts():\n        phrase = cache_key(cache, name)\n    else:\n        from rk.sam3mask import tower\n        phrase = tower().phrase(name)"),
])
edit('candidates', 'generator/derivgen_v7/derivgen/room_rows_v314.py', [
    ('from . import ground_v312 as G, room_v314 as R', 'from . import ground_v312 as G, room_v314 as R\nfrom trace_format.contracts import geometry_mode'),
    ("if session.geometry_mode != 'sensor':", "if geometry_mode(session) != 'sensor':"),
])

# Annotation lookup in row generators uses the runtime phrase identity too;
# prose, question hashes and English plural rendering retain their own grammar.
for rel in ('generator/derivgen_v7/derivgen/ground_v312_io.py',
            'generator/derivgen_v7/derivgen/ground_v313_distance.py'):
    edit('candidates', rel, [('from .ground_v312_quality import normalized',
                            'from student_pilot.phrases import annotation_phrase as normalized')])
p = SRC/'generator/derivgen_v7/derivgen/ground_v312_io.py'
t = p.read_text().replace('from .instance_policy314 import valid_mask', 'from .instance_policy314 import valid_mask\nfrom student_pilot.phrases import annotation_labels')
t = t.replace('T.match_labels(name, geo.labels)', 'annotation_labels(name, geo.labels, T.match_labels)')
t = t.replace('self.programs.T.match_labels(name, self.geo.labels)', 'annotation_labels(name, self.geo.labels, self.programs.T.match_labels)')
p.write_text(t)

edit('candidates', 'trace_format/category_vocab.py', [
    ("    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())", "    from trace_format.contracts import new_contracts\n    if new_contracts():\n        from student_pilot.phrases import normalize_phrase\n        return normalize_phrase(str(text))\n    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())")])

put('candidates', 'student_pilot/training_contract.py', '''"""Per-row admission against the deployed operand and response contract."""
import re
from .phrases import candidate_phrases, normalize_phrase, phrase_set
from trace_format.contracts import RUNTIME_STATUSES, response_status, new_contracts

OPERATOR_FAULTS = ('requires a fixed named candidate universe', 'outside the fixed candidate universe',
    'form_requires_v3.13', 'form_requires_v3.14', 'frozen_fusion_requires_depth_cut_receipt',
    'mask_source_unavailable_for_type')


def admission_phrases(question, options, cache_phrases, operands=()):
    names = candidate_phrases(question, options, cache_phrases)
    if any(normalize_phrase(n) not in names for n in operands):
        raise ValueError('contract_operand_outside_candidates')
    return names


def call_responses(row):
    events = row.get('routing', row).get('events', [])
    pending = None
    for event in events:
        kind = event.get('kind', '')
        if 'call' in event and 'response' in event:
            if pending is not None:
                yield pending, None
                pending = None
            yield event['call'], event['response']
        elif kind.endswith('_call') or ('call' in event and 'response' not in event):
            if pending is not None:
                yield pending, None
            pending = event.get('token', event.get('command', event.get('text', event.get('call', '')))).strip()
        elif kind.endswith('_response'):
            value = event.get('text', event.get('response'))
            if isinstance(value, dict):
                value = value.get('text', value.get('injected_text'))
            yield pending, value
            pending = None
    if pending is not None:
        yield pending, None


def audit_training_contract(rows, manifest=None):
    """Return one verdict per row; callers defer failures, never abort the pool.

    After the first failed ground, permit one ground of a different listed name.
    No further call is legal, even if that retry succeeds. End in a direct answer.
    """
    verdicts = []
    for row in rows:
        reason = None
        pairs = list(call_responses(row))
        if not new_contracts() or not pairs:
            verdicts.append(None)
            continue
        entry = manifest.get(str(row.get('qid'))) if manifest is not None else row.get('candidate_phrases')
        named = any(isinstance(call,str) and re.search(r'obj="',call) for call,_ in pairs)
        if named and entry is None:
            verdicts.append('contract_manifest_missing')
            continue
        if isinstance(entry, dict):
            entry = entry.get('phrases', [])
        inputs = row.get('student_input', row)
        names = admission_phrases(inputs.get('question',''), inputs.get('options',[]), entry or [])
        failed = None
        retried = False
        for call, text in pairs:
            if not isinstance(call,str) or not isinstance(text,str) or not text.strip():
                reason = 'contract_missing_response'
                break
            if any(code in text for code in OPERATOR_FAULTS) or 'error:' in text.lower():
                reason = 'contract_operator_fault'
                break
            match = re.search(r'^<ground obj="([^"]+)"',call)
            name = normalize_phrase(match[1]) if match else None
            if name is not None and name not in names:
                reason = 'contract_operand_outside_candidates'
                break
            if failed is not None:
                if retried or name is None or name == failed:
                    reason = 'contract_call_after_failed_ground'
                    break
                retried = True
            body = text.strip().removeprefix('<tool_response>').removesuffix('</tool_response>').strip()
            status = response_status(body)
            if call.startswith(('<ground','<gap')):
                from .live_trace313 import parse_response
                try:
                    parse_response(call,body,row.get('trace_revision',row.get('routing',{}).get('trace_revision','3.14')))
                except (ValueError, IndexError, TypeError):
                    reason = 'contract_unknown_status'
                    break
            if match and status != 'ok':
                failed = failed or name
        target = row.get('target', row.get('suffix',''))
        if reason is None and failed is not None and not re.search(r'(?:<answer>.+</answer>|</think>\\s*\\S.*)$',target,re.S):
            reason = 'contract_recovery_without_answer'
        verdicts.append(reason)
    return verdicts
''')
edit('candidates', 'student_pilot/s1_routing.py', [
    ('from .p3_provenance import file_pin, load, pinned, write', 'from .p3_provenance import file_pin, load, pinned, write\nfrom .training_contract import audit_training_contract\nfrom trace_format.contracts import new_contracts'),
    ('def build(cfg, directory, division_pin, base_model, *, audit_only=False):', '''def build(cfg, directory, division_pin, base_model, *, audit_only=False):
    from trace_format.contracts import contract_epoch
    with contract_epoch(cfg.get('contract_epoch', new_contracts())):
        return _build(cfg, directory, division_pin, base_model, audit_only=audit_only)


def _build(cfg, directory, division_pin, base_model, *, audit_only=False):'''),
    ('    selection = load(pinned(selection_pin))', "    selection = load(pinned(selection_pin))\n    contract_manifest = load(pinned(spec['candidate_manifest'])) if spec.get('candidate_manifest') else None"),
    ('        spans = routing.render(row["routing"]["events"]', '''        refusal = audit_training_contract([row], contract_manifest)[0]
        if refusal:
            count(row['routing']['question_type'], 'r16_deferred' if origin == 'legacy' else 'pool_deferred', refusal)
            return
        if new_contracts() and contract_manifest is not None and str(row['qid']) in contract_manifest:
            from .phrases import phrase_set
            entry = contract_manifest[str(row['qid'])]
            row['candidate_phrases'] = list(phrase_set(entry.get('phrases', []) if isinstance(entry, dict) else entry))
        spans = routing.render(row["routing"]["events"]'''),
    ('                    changed = False', '''                    refusal = audit_training_contract([raw], contract_manifest)[0]
                    if refusal:
                        count(kind, "pool_deferred", refusal)
                        continue
                    changed = False'''),
    ('                    row["s1_source"] = dict', "                    if 'candidate_phrases' in raw:\n                        row['candidate_phrases'] = raw['candidate_phrases']\n                    row[\"s1_source\"] = dict"),
    ('        base_model=base_model,', "        base_model=base_model, **({'contract_epoch': True} if new_contracts() else {}),"),
])

edit('candidates', 'student_pilot/ground_rows.py', [
    ('    if record.get("not_seen") or record.get("gt_agrees")', '''    from trace_format.contracts import new_contracts
    recovery = new_contracts() and record.get('not_seen')
    if recovery:
        from .training_contract import audit_training_contract
        verdict = audit_training_contract([dict(row, events=record['events'])])[0]
        if verdict:
            raise ValueError(verdict)
    if (record.get("not_seen") and not recovery) or record.get("gt_agrees")'''),
])

edit('candidates', 'tests/test_e2e_open_vocabulary.py', [
    ('from student_pilot.ground_admission import LABELS, qualification', 'from student_pilot.ground_admission import LABELS, qualification, normalized_name'),
    ("self.assertTrue(unknown.queries[0]['name_outside_decoder_vocabulary'])", "self.assertEqual(unknown.queries[0]['name_outside_decoder_vocabulary'],\n                                 normalized_name(name) not in {normalized_name(label) for label in LABELS})"),
])
edit('candidates', 'tests/test_sam3_tower.py', [
    ("            self.assertEqual(normalize_phrase(label), namespace['phrase'](label))", "            from trace_format.contracts import contract_epoch\n            with contract_epoch(False):\n                self.assertEqual(normalize_phrase(label), namespace['phrase'](label))"),
])

# Box bridge is deliberately local; it cannot change cutting or fitting thresholds.
edit('box', 'student_pilot/live_instances314.py', [
    ('from .scene_state import normalize_name', 'from .scene_state import normalize_name\nfrom trace_format.contracts import new_contracts, geometry_mode'),
    ("    return [dict(item, result=lifting.lift_object(query['name'],unpack_mask(item),", "    return [dict(item, result=bridge_cut(lifting.lift_object(query['name'],unpack_mask(item),"),
    ("depth_cut=item.get('depth_cut',query.get('geometry_mode','sensor')=='predicted'))) for item in query['instances']]", "depth_cut=item.get('depth_cut',query.get('geometry_mode','sensor')=='predicted')), item, query.get('contract_epoch',False))) for item in query['instances']]"),
    ('def components(owner, name):', '''def bridge_cut(obj, entry, enabled):
    if enabled and entry.get('depth_cut_applied', False):
        obj['points_cut'] = obj['points']
    return obj


def components(owner, name):'''),
    ("getattr(session,'geometry_mode','sensor')=='predicted'", "geometry_mode(session)=='predicted'"),
    ("        if obj['seen']:lifted.append", "        bridge_cut(obj, entry, getattr(session, 'contract_epoch', new_contracts()))\n        if obj['seen']:lifted.append"),
])

(L/'work/patch_groups.json').write_text(json.dumps(groups,indent=2))
for group,names in groups.items():
    diff = []
    for name in names:
        before = (BASE/name).read_text().splitlines(True) if (BASE/name).exists() else []
        after = (SRC/name).read_text().splitlines(True)
        diff.extend(difflib.unified_diff(before,after,fromfile='a/'+name,tofile='b/'+name))
    (L/f'out/PATCH_{group}.diff').write_text(''.join(diff))
manifest = dict(base_seal='b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99',files={})
for group,names in groups.items():
    for name in names:
        manifest['files'][name] = dict(base_sha256=hashlib.sha256((BASE/name).read_bytes()).hexdigest() if (BASE/name).exists() else None,
            patched_sha256=hashlib.sha256((SRC/name).read_bytes()).hexdigest(),patch=group)
(L/'out/PATCH_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print({g:len(n) for g,n in groups.items()})
