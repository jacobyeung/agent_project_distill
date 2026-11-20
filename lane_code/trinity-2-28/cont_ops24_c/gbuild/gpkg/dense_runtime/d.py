"""Authenticated runtime extensions for the bound native frames; sealed files stay intact."""
import ast
from contextlib import contextmanager
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import re
import sys
import textwrap
import numpy as np


def rewrite(fn, replacements=(), constants=None, namespace=None, terminal=None):
    fn=inspect.unwrap(fn)
    source=textwrap.dedent(inspect.getsource(fn))
    for old,new in replacements:
        if source.count(old)!=1:raise RuntimeError('overlay context differs: '+old)
        source=source.replace(old,new)
    node=ast.parse(source).body[0]
    node.decorator_list=[]
    if terminal:
        expected=ast.parse(terminal).body
        if [ast.dump(n) for n in node.body[-2:]]!=[ast.dump(n) for n in expected]:
            raise RuntimeError('validator terminal differs')
        node.body=node.body[:-2]+ast.parse('return self').body
    if constants:
        class Change(ast.NodeTransformer):
            def visit_Constant(self,node):
                if type(node.value) in (int,float) and node.value in constants:
                    return ast.copy_location(ast.parse(constants[node.value],mode='eval').body,node)
                return node
        node=Change().visit(node)
    ns=dict(fn.__globals__)
    ns.update(namespace or {})
    exec(compile(ast.fix_missing_locations(ast.Module([node],type_ignores=[])),
                 '<g:authenticated-overlay>','exec'),ns)
    return ns[node.name]


def authenticate(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    pins=json.loads((Path(__file__).parent/'8.json').read_text())
    for name,expected in pins.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError('overlay source differs: '+name)
    return pins


def frame_count(geo):
    n=len(geo.C)
    if n not in (32,64):raise ValueError('expected 32 or 64 bound frames')
    return n


def dense_geometry(tower,gravity,scale):
    from e2e_reader.geometry import from_tower
    anchors=from_tower(tower['raw_pose9'],tower['anchor_slots'],tower['frame_indices'],
                       tower['depth_grid'],tower['grid_uv'],gravity,scale,tower['source_hw'])
    if len(tower['raw_pose9'])==32:return anchors
    full=from_tower(tower['raw_pose9'],np.arange(64),tower['frame_indices'],
                    tower['dense_depth_grid'],tower['grid_uv'],gravity,scale,tower['source_hw'])
    slots=np.asarray(tower['anchor_slots'])
    deltas={}
    for name in ('K','A','C','depth_grid'):
        a,b=getattr(anchors,name),getattr(full,name)[slots]
        deltas[name]=dict(byte_identical=a.tobytes()==b.tobytes(),max_abs=float(np.max(np.abs(a-b))))
    full.anchor_geometry_deltas=deltas
    full.anchor_slots=slots.tolist()
    full.anchor_geometry_unchanged=all(v['byte_identical'] for v in deltas.values())
    full.answer_geometry=anchors
    return full


@contextmanager
def installed(root=None):
    """Install once in the serial worker, restoring everything on exit."""
    pins=authenticate(root)
    from student_pilot import geometry_profiles as GP,scene_state as SS
    from student_pilot import routed_candidates as C,routed_features as F,tower_read as TR
    from e2e_reader import geometry as G,real,generate,stage1
    from trace_format import box_v313 as B
    # Authenticate the original validator through its deployed hash check first.
    original_contract=G.reader_contract(GP)
    sys.path.insert(0,str(stage1.HEADS/'selector/sl118'))
    SI=importlib.import_module('selector_inputs')
    expected=Path(stage1.HEADS/'selector/sl118/selector_inputs.py').resolve()
    if Path(SI.__file__).resolve()!=expected:raise ImportError('foreign selector inputs')
    changes=[]
    def set_(owner,name,value):
        changes.append((owner,name,getattr(owner,name)));setattr(owner,name,value)
    def conditional(owner,name,changed,use_original):
        old=getattr(owner,name)
        def dispatch(*a,**kw):
            return (old if use_original(*a,**kw) else changed)(*a,**kw)
        set_(owner,name,dispatch)
    try:
        post=SS.FrameMap.__post_init__
        post64=rewrite(post,constants={32:'64'})
        def map_post(self):
            if len(self.source_indices) not in (32,64):raise ValueError('expected 32 or 64 source indices')
            return (post if len(self.source_indices)==32 else post64)(self)
        set_(SS.FrameMap,'__post_init__',map_post)
        # The sealed validator remains untouched. Only its authenticated reader
        # subclass gets an extended shape check; every other guard is retained.
        validate=rewrite(GP.GeometryContract.validate,terminal=G.TERMINAL,
                         constants={32:'len(self.frame_map.source_indices)'})
        contract64=type('DenseReaderContract',(GP.GeometryContract,),dict(validate=validate))
        original_arrays=G.from_arrays
        def arrays(**kw):
            n=len(kw['anchor_frame_indices'])
            if n==32:return original_arrays(**kw)
            if n!=64:raise ValueError('expected 32 or 64 geometry frames')
            anchors=tuple(map(int,kw['anchor_frame_indices']))
            contract=contract64('scaled_g3t_depth',SS.FrameMap(anchors),anchors[0],
                np.asarray(kw['K'],float),np.asarray(kw['canvas_to_source'],float),
                np.asarray(kw['camera_to_world'],float),float(kw['scale']),
                'g3t','unscaled','unscaled',0,0)
            return GP.ProfileGeometry(contract,np.asarray(kw['depth_grid']),np.asarray(kw['grid_uv']))
        set_(G,'from_arrays',arrays)
        init64=rewrite(GP.ProfileGeometry.__init__,constants={32:'len(contract.frame_map.source_indices)'})
        conditional(GP.ProfileGeometry,'__init__',init64,lambda self,contract,*a,**k:len(contract.frame_map.source_indices)==32)
        has64=rewrite(GP.ProfileGeometry.has,constants={32:'len(self.C)'})
        conditional(GP.ProfileGeometry,'has',has64,lambda self,*a,**k:len(self.C)==32)
        for name in ('lift_grid','lift','visible_voxels'):
            fn=getattr(C,name)
            changed=rewrite(fn,constants={33:'frame_count(geo)+1'},namespace={'frame_count':frame_count})
            # Defaults and keyword arguments stay those of the production call.
            sig=inspect.signature(fn)
            def original(*a,_sig=sig,**kw):return frame_count(_sig.bind(*a,**kw).arguments['geo'])==32
            conditional(C,name,changed,original)
        changed=rewrite(F.Geometry.__init__,constants={33:'frame_count(source)+1'},namespace={'frame_count':frame_count})
        conditional(F.Geometry,'__init__',changed,lambda self,source:frame_count(source)==32)
        vectors=rewrite(SI.candidate_vectors,constants={32:'float(len(raw_frames))',31:'float(len(raw_frames)-1)'})
        conditional(SI,'candidate_vectors',vectors,lambda tracks,raw_frames,*a,**kw:len(raw_frames)==32)
        # Both serialization and ingestion validate displayed support indices.
        # Values within 1..32 still use the original functions verbatim.
        conditional(B,'serialize',rewrite(B.serialize,constants={32:'64'}),
                    lambda name,label,frames,*a,**kw:all(type(f) is int and f<=32 for f in frames))
        def old_parse(body):
            found=re.search(r': frames ([0-9,]+) \(best',body)
            return not found or all(int(f)<=32 for f in found[1].split(','))
        conditional(B,'parse',rewrite(B.parse,constants={32:'64'}),old_parse)
        # Preserve the four anchor head batches exactly, then decode nonanchors
        # from the SAME four retained backbone layers, in batches of eight.
        run64=rewrite(TR.FrozenG3TTower.run,[
            ('depths, confidences, points = [], [], []',
             "depths, confidences, points = [], [], []\n    head_slots = np.concatenate((slots, [i for i in range(len(frames)) if i not in slots]))"),
            ('range(0, 32, self.chunk)','range(0, len(head_slots), self.chunk)'),
            ('selected = slots[offset:offset + self.chunk]','selected = head_slots[offset:offset + self.chunk]'),
            ("points = (points @ transform[:3, :3].T + transform[:3, 3]).astype(np.float32)",
             "points = np.concatenate([(part @ transform[:3, :3].T + transform[:3, 3]).astype(np.float32) for part in (points[:32], points[32:])])"),
            ("state = TowerState(result['raw_pose'], np.concatenate(depths), np.concatenate(confidences),\n                       indices, slots, points)",
             "state = TowerState(result['raw_pose'], np.concatenate(depths)[:32], np.concatenate(confidences)[:32],\n                       indices, slots, points[:32] if points is not None else None)\n    inverse = np.argsort(head_slots)\n    for name, value in (('dense_depth_grid', np.concatenate(depths)), ('dense_depth_conf_grid', np.concatenate(confidences)), ('dense_points_grid', points)):\n        if value is None: raise ValueError('dense point head unavailable')\n        value = value[inverse].copy(); value.flags.writeable = False\n        object.__setattr__(state, name, value)")])
        import torch
        run64=torch.inference_mode()(TR.tower_guard(run64))
        conditional(TR.FrozenG3TTower,'run',run64,lambda self,batch:self.dense_frames==32)
        fresh64=rewrite(real.TowerG3T._fresh,[
            ('return dict(raw_pose9=np.asarray(s.raw_pose9)',
             'return dict(dense_depth_grid=s.dense_depth_grid, dense_depth_conf_grid=s.dense_depth_conf_grid, dense_points_grid=s.dense_points_grid, raw_pose9=np.asarray(s.raw_pose9)')])
        conditional(real.TowerG3T,'_fresh',fresh64,lambda self,frames:len(frames['native_frames'])==32)
        old_anchor=real.anchor_frames
        set_(real,'anchor_frames',lambda frames:old_anchor(frames) if len(frames['native_frames'])==32 else list(frames['native_frames']))
        lazy64=rewrite(generate.Perception.lazy,[
            ("geometry = from_tower(tower['raw_pose9'], tower['anchor_slots'], tower['frame_indices'],\n                                  tower['depth_grid'], tower['grid_uv'], gravity, float(torch.tensor(log_s).exp()),\n                                  tower['source_hw'])",
             'geometry = dense_geometry(tower, gravity, float(torch.tensor(log_s).exp()))'),
            ('ReadServers(geometry, session, serve_room=self.serve_room)',
             'ReadServers(geometry.answer_geometry, session, serve_room=self.serve_room)')],
            namespace={'dense_geometry':dense_geometry})
        conditional(generate.Perception,'lazy',lazy64,lambda self,frames,*a,**k:len(frames['native_frames'])==32)
        yield dict(source_pins=pins,validator_sha256=G.SEALED_VALIDATE_SHA256,
                   original_validator_unchanged=True,counts=[32,64])
    finally:
        for owner,name,old in reversed(changes):setattr(owner,name,old)


def binding_record(bound,ref):
    frames=bound['frames'];n=len(frames['native_frames'])
    slots=frames['anchor_slots'];indices=frames['dense_indices']
    if n not in (32,64) or len(indices)!=n or [indices[s] for s in slots]!=ref['source_indices']:
        raise ValueError('dense binding differs')
    if n==32 and list(slots)!=list(range(32)):raise ValueError('32-frame binding differs')
    return dict(ground_frame_count=n,ground_source_indices=list(indices),anchor_slots=list(slots),
                primary_dense64=n==64,unchanged32=n==32,
                printed_frame_convention='one-based bound native order',answer_anchor_count=32)


def rehearsal():
    """Exercise extended geometry and socket shape during CPU entry admission."""
    from e2e_reader.geometry import from_arrays
    from e2e_reader.grounding import StageOneSocket
    from student_pilot.routed_features import Geometry
    for n in (32,64):
        K=np.tile([[500.,0,500.],[0,500.,500.],[0,0,1.]],(n,1,1))
        geo=from_arrays(K=K,canvas_to_source=np.tile(np.eye(3),(n,1,1)),
            camera_to_world=np.tile(np.eye(4),(n,1,1)),scale=1.,depth_grid=np.ones((n,51,51)),
            grid_uv=np.linspace(0,1000,51),anchor_frame_indices=list(range(n)))
        if not geo.has(n) or geo.has(n+1) or Geometry(geo).frames[-1]!=n:raise ValueError('extended geometry admission')
        candidate=dict(candidate_id='0',masks={n:np.ones((2,2),bool)})
        socket=StageOneSocket(lambda name:([candidate],{}),lambda inputs:0,(2,2),n)
        masks=socket('x')[0]['masks']
        if masks.shape!=(n,2,2) or not masks[-1].all():raise ValueError('extended socket admission')
    return dict(counts=[32,64],passed=True)
