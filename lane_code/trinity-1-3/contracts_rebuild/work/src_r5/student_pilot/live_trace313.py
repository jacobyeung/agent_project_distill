"""Bind the response session to production selection, verification and replay masks."""
from copy import deepcopy
import re
import numpy as np
from trace_format.ground_v313 import Session
from trace_format import box_v313, room_v314
from . import ground_lifting as lifting
from .ground_replay import restore_geometry
from .p3_printed_calculator import PrintedPointRegistry
from trace_format.contracts import RUNTIME_STATUSES, response_status, new_contracts, contract_epoch, heading_plane_min, contract_identity, HEADING_PLANE_MIN_DEFAULT


class LiveSession(Session):
    def __init__(self, backend, *, program_version=None, multi_instance=None, geometry_mode=None):
        # Calls share their ground opener: the model's trace version must be
        # known before the first response, not inferred from a later gap.
        from .trace_version import require
        require(program_version)
        if multi_instance is not None and multi_instance != (program_version == '3.14'):
            raise ValueError('program_version_instance_mode_mismatch')
        if geometry_mode is None:
            sensor = (getattr(backend.geometry, 'kind', None) == 'gt' or
                      getattr(getattr(backend.geometry, 'contract', None), 'ground_truth_substitution', False))
            geometry_mode = 'sensor' if sensor or program_version != '3.14' else 'predicted'
        super().__init__(lifting,backend.geometry,None,instances=lambda name:(),
                         program_version=program_version, multi_instance=program_version=='3.14',
                         geometry_mode=geometry_mode)
        self.contract_epoch = getattr(backend, 'contract_epoch', new_contracts())
        self.heading_plane_min = heading_plane_min(getattr(backend, 'heading_plane_min', heading_plane_min()))
        self.owner=backend
        self.queries=[]
        self.memory_hits=[]

    def execute(self, call):
        with contract_epoch(self.contract_epoch, heading_plane_min=self.heading_plane_min):
            return super().execute(call)

    def _room(self):
        from .live_instances314 import ExactFrames
        from .ground_replay import pack_array
        geometry = self.geometry
        try:
            self.geometry = ExactFrames(geometry)
            body = super()._room()
        finally:
            self.geometry = geometry
        inputs = self.room_inputs
        self.queries.append(dict(kind='room', geometry_mode=self.geometry_mode, **contract_identity(),
            frames=inputs['frames'], gravity_source=inputs['gravity_source'],
            points=[pack_array(p) for p in inputs['points']]))
        self.memory_hits.append(False)
        return body

    def bind_state(self,state):
        self.state=state
        state.live_trace_session=self
        if self.owner.geometry is None and getattr(self.owner, 'allow_own_geometry_fallback', False):
            if state.geometry is None or state.geometry_error:
                raise ValueError('same_checkpoint_geometry_unavailable')
            self.geometry = lifting.OwnGeometryAdapter(state.geometry)
            self.owner.geometry = self.geometry
            self.owner.geometry_error = None
            self.owner.geometry_source = 'same_checkpoint_own'

    def _instances(self,name):
        if self.spec_version == '3.14':
            from .live_instances314 import query_instances
            query = query_instances(self.owner, name, self.state)
            query.update(geometry_mode=self.geometry_mode, box_provider_id=self.box_provider_id, **contract_identity())
            self.queries.append(query)
            self.memory_hits.append(query['memory_hit'])
            return entries(query)
        # Selection/verify may allocate a legacy print point. Use a private registry;
        # only the v3.13 session allocates labels in the public response stream.
        from .scene_state import normalize_name
        self.memory_hits.append(self.owner._memory_entry(normalize_name(name)) is not None)
        state=self.state;context=state.tool_context
        context.registry=PrintedPointRegistry()
        context.mdg_states=state.heads.mdg_states
        context.fallback=lambda n:self.owner.ground(n,context.registry)
        if state.verify_session is not None:
            _,info=state.verify_session.ground(name,context)
            if info.get('verify_error'):raise ValueError('live_verification_error')
            source=state.verify_session.queries
        else:
            self.owner.ground(name,context.registry)
            source=self.owner.queries
        if not source or source[-1]['name']!=name:raise ValueError('live_ground_missing_audit')
        query=deepcopy(source[-1])
        query.update(geometry_mode=self.geometry_mode, box_provider_id=self.box_provider_id, **contract_identity())
        self.queries.append(query)
        return entries(query)


def entries(query):
    if query.get('state') in ('invalid_geometry','INVALID_GEOMETRY'):
        raise ValueError('live_ground_invalid_geometry')
    if 'instances' in query:
        result = []
        seen = set()
        for item in query['instances']:
            iid = str(item['instance_id'])
            if iid in seen:raise ValueError('duplicate_native_instance')
            seen.add(iid)
            obj = deepcopy(item['result'])
            if obj.get('seen'):
                result.append(dict(obj, instance_id=iid, first=min(obj['frames'])))
        return sorted(result, key=lambda r:(r['first'],r['instance_id']))
    result=deepcopy(query['result'])
    if query.get('state','').lower()=='unresolved':return [dict(seen=False),dict(seen=False)]
    if not result.get('seen'):return []
    return [dict(result,instance_id='selected',first=min(result['frames']))]


class AuditSession(Session):
    def __init__(self,queries,program_version='3.13'):
        epochs = {q.get('contract_epoch', False) for q in queries}
        if len(epochs) > 1:
            raise ValueError('replay_contract_epoch_mismatch')
        self.contract_epoch = next(iter(epochs), False)
        thresholds = {heading_plane_min(q.get('heading_plane_min', HEADING_PLANE_MIN_DEFAULT)) for q in queries}
        if len(thresholds) > 1:
            raise ValueError('replay_heading_plane_min_mismatch')
        self.heading_plane_min = next(iter(thresholds), heading_plane_min())
        modes = {query.get('geometry_mode', 'sensor') for query in queries}
        if len(modes) > 1:
            raise ValueError('replay_geometry_mode_mismatch')
        with contract_epoch(self.contract_epoch, heading_plane_min=self.heading_plane_min):
            super().__init__(lifting,None,None,instances=lambda name:(),
                             program_version=program_version,multi_instance=program_version=='3.14',
                             geometry_mode=next(iter(modes), 'sensor'))
        if any(query.get('box_provider_id', self.box_provider_id) != self.box_provider_id for query in queries):
            raise ValueError('replay_box_provider_mismatch')
        self.pending=list(queries)

    def execute(self, call):
        with contract_epoch(self.contract_epoch, heading_plane_min=self.heading_plane_min):
            return super().execute(call)

    def _room(self):
        from .ground_replay import unpack_array
        if not self.pending or self.pending[0].get('kind') != 'room':
            raise ValueError('replay_missing_room_geometry')
        query = self.pending.pop(0)
        result = room_v314.from_points([unpack_array(p) for p in query['points']],
            query['frames'], query['geometry_mode'], gravity_source=query['gravity_source'])
        body = room_v314.format_result(result)
        from trace_format.ground_v312 import wrap
        self.events.append(dict(call=room_v314.CALL, response=wrap(body), audit=dict(room=result)))
        return body

    def _instances(self,name):
        if not self.pending:raise ValueError('replay_missing_ground_audit')
        q=self.pending.pop(0)
        if q['name']!=name:raise ValueError('replay_ground_order')
        from .live_instances314 import restore_recorded_geometry
        self.geometry=restore_recorded_geometry(q.get('geometry'))
        if 'instances' in q:
            from .live_instances314 import relift_instances, ExactFrames
            self.geometry=ExactFrames(self.geometry,q['exact_frames'])
            return entries(dict(q,instances=relift_instances(q,self.geometry)))
        mask=np.unpackbits(np.asarray(q['mask_bits'],np.uint8),count=int(np.prod(q['mask_shape']))).astype(bool).reshape(q['mask_shape'])
        # The response comes from re-lifting recorded masks, never recorded text.
        result=lifting.lift_object(name,mask,q['prob'],self.geometry,tau=q['tau']) if mask.any() else dict(name=name,seen=False)
        return entries(dict(q,result=result))


def parse_response(call,body,program_version=None):
    if program_version=='3.13' and re.search(r': [2-9][0-9]* instances\n',body):
        from trace_format.program_errors import ProgramRefusal
        raise ProgramRefusal('form_requires_v3.14')
    """Validate the public grammar used by the four acceptance families."""
    if body.startswith('error:'):raise ValueError('response_error')
    if call == room_v314.CALL:
        if program_version == '3.13':
            from trace_format.program_errors import ProgramRefusal
            raise ProgramRefusal('form_requires_v3.14')
        return room_v314.parse_response(body)
    if 'heading unavailable' in body and call.startswith('<ground'):
        # Check the full existing grammar with only withheld components restored as placeholders.
        normalized = body.replace('heading unavailable', '0.00')
        normalized = normalized.replace('yaw 0.00', 'yaw 0 deg (0 = +x; positive +x toward -z about +y)')
        if not body.startswith(re.search(r'obj="([^"]+)"',call)[1]+': heading unavailable'):
            return parse_response(call, normalized, program_version)
    if call.startswith('<ground'):
        name=re.search(r'obj="([^"]+)"',call)[1]
        if body in [name+': '+s for s in RUNTIME_STATUSES]:return
        if body.startswith(name+': heading unavailable\n') and all(
                line == 'size unavailable' or re.fullmatch(r'size [0-9]+\.[0-9]{2} x [0-9]+\.[0-9]{2} x [0-9]+\.[0-9]{2} m', line) for line in body.splitlines()[1:]):return
        if 'mode="box"' in call:
            blocks=box_v313.split_instances(body)
            if len(blocks)>box_v313.MAX_INSTANCES:raise ValueError('too_many_instances')
            parsed=[box_v313.parse(b) for b in blocks]
            if any(b['name']!=name for b in parsed):raise ValueError('response_name')
            if len({b['label'] for b in parsed})!=len(parsed):raise ValueError('duplicate_box_label')
            return
        if 'mode="instances"' in call:
            if re.fullmatch(re.escape(name)+r': (0|[1-9][0-9]*) found\nheading unavailable', body):return
            lines=body.splitlines()
            m=re.fullmatch(re.escape(name)+r': (0|[1-9][0-9]*) found',lines[0])
            if not m or len(lines)!=1+int(m[1]):raise ValueError('malformed_instance_response')
            f=r'-?(?:0|[1-9][0-9]*)\.[0-9]{2}'
            xyz=r'\('+f+', '+f+', '+f+r'\)'
            labels=[]
            for i,line in enumerate(lines[1:],1):
                pat=(r'(P[1-9][0-9]*): '+re.escape(name)+f' instance {i} '+
                     r'cam[1-9][0-9]* '+xyz+r' m; f1 '+xyz+r' m; first [1-9][0-9]*')
                match=re.fullmatch(pat,line)
                if not match:raise ValueError('malformed_instance_line')
                labels.append(match[1])
            if len(labels)!=len(set(labels)):raise ValueError('duplicate_point_label')
            return
        f=r'-?(?:0|[1-9][0-9]*)\.[0-9]{2}' 
        triple=r'\('+f+', '+f+', '+f+r'\)'
        pattern=(re.escape(name)+r': frames [1-9][0-9]*(?:,[1-9][0-9]*)* \(best [1-9][0-9]*\)\n'
            r'P[1-9][0-9]*: cam[1-9][0-9]* '+triple+r' m; f1 '+triple+r' m; spread '+f+r'\n'
            r'(?:size '+f+' x '+f+' x '+f+r' m|size unavailable)')
        if not re.fullmatch(pattern,body):raise ValueError('malformed_ground_response')
    elif call.startswith('<gap'):
        if body in RUNTIME_STATUSES:return
        if body=='frame unavailable' and box_v313.CAMGAP.fullmatch(call):return
        f=r'(?:0|[1-9][0-9]*)\.[0-9]{2}'
        if body.startswith('distance '):
            if not re.fullmatch('distance '+f+' m',body):raise ValueError('malformed_gap_response')
        else:
            lines=body.splitlines();names=re.findall(r' b="([^"]+)"',call)
            if len(lines)!=len(names)+1:raise ValueError('malformed_relative_gap_response')
            for name,line in zip(names,lines):
                if not re.fullmatch(re.escape(name)+': '+f+' m',line):raise ValueError('malformed_relative_gap_line')
            if not re.fullmatch(r'min "[^"\n]+"(?:,"[^"\n]+")* '+f+' m',lines[-1]):raise ValueError('malformed_gap_min')
    elif call.startswith('<angle'):
        # Calculator syntax is checked exactly against its registry by replay().
        if not body.strip() or '<' in body or '>' in body:raise ValueError('malformed_calculator_response')
    else:raise ValueError('unsupported_acceptance_call')


def replay(record):
    version=record['heads'].get('trace_program_version','3.13')
    session=AuditSession(record['heads']['ground_queries'],version);mismatches=0
    for call in record['calls']:
        parse_response(call['call'],call['response'],version)
        text=session.execute(call['call'])
        mismatches+=text!=call['response']
    from collections import Counter
    statuses = Counter(response_status(call['response']) for call in record['calls'])
    metrics = dict(response_statuses=dict(statuses), ok_responses=statuses['ok']) if session.contract_epoch else {}
    return dict(**metrics, calls=len(record['calls']),mismatches=mismatches,byte_equal=not mismatches and not session.pending,
                response_format='3.13 revision 5' if version=='3.13' else '3.14',replay_source='recorded masks, geometry and selection state')


def check_record(record,reference=None):
    if record['errors'] or record['finish']!='eos':raise AssertionError('Requires zero errors and free EOS')
    if not record['calls']:raise AssertionError('No routed calls')
    if reference is not None:
        calls=[s['call'] for s in reference['segments']]
        if [c['call'] for c in record['calls'][:len(calls)]]!=calls:raise AssertionError('Scripted calls missing')
        if not record.get('scripted',{}).get('free_answer_eos'):raise AssertionError('Free answer did not reach EOS')
    result=replay(record)
    if not result['byte_equal']:raise AssertionError('Response replay differs')
    return result
