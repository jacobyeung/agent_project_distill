"""Servers the call hook dispatches to, bound per read. Formatting is the tree's sealed v3.14
formatter (fixed math: transforms, norms, rounding); values come from this read's tensors."""
from copy import deepcopy

from .geometry import camera_geometry, no_guard

ERROR_SUFFIX = '; answer directly from the video'


class ReadServers:
    """camera/head calls -> tree carrier_c1_decode.respond on the read's geometry;
    ground/gap/room -> a v3.14 Session whose instances come from the grounding socket."""

    def __init__(self, geometry, session=None, *, serve_room=False):
        from student_pilot.p3_printed_calculator import PrintedPointRegistry
        self.geometry = geometry
        self.own, self.pose9, self.up, self.depth_queries = camera_geometry(geometry)
        self.registry = PrintedPointRegistry()
        self.session = session
        self.serve_room = serve_room

    def head(self, call):
        from student_pilot.carrier_c1_decode import respond
        return respond(call, self.registry, self.own)

    def session_call(self, call):
        session = self.session
        session.registry = self.registry
        try:
            with no_guard():
                text = session.execute(call)
        except ValueError as exc:
            return ('error: ' + str(exc) + ERROR_SUFFIX,
                    dict(kind='error', code=str(exc), spec_version=session.spec_version, direct_answer_fallback=True))
        self.registry._points = session.registry._points
        session.registry = self.registry
        kind = 'gap' if call.startswith('<gap') else 'ground' if call.startswith('<ground') else 'keypoint'
        return text, dict(kind=kind, spec_version=session.spec_version, spec_revision=1,
                          audit=deepcopy(session.events[-1].get('audit', {})))

    def mapping(self):
        m = dict(move=self.head, turn=self.head, pose=self.head, depth_at=self.head, other=self.head)
        if self.session is not None:
            m.update(ground=self.session_call, gap=self.session_call)
            if self.serve_room:
                m['room'] = self.session_call
        return m
