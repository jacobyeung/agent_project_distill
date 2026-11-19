"""CPU camera-routing templates over exact 32-frame metric pose clips.

Normalized clip: recording_id, dataset, scene, frames[{path,sha256,source_index}],
fps, total_num_frames, gt_pose9[32,9], gt_up[3], and rgb_manifest{path,sha256}.
Codes are E_k=inv(C_k) C_1: metric t, quaternion xyzw, vertical/horizontal FoV
in radians. gt_up is gravity-up in frame 1's OpenCV camera. Frame slots are 1..32.

from_pose_row accepts recording_pose.build_row output. Legacy 16-anchor rows
require its load_poses result as poses=; they cannot supply 32 exact cameras.
from_gt_scene reads the canonical toolprog GT adapter already owned by GTScene.
Adapters accept manifest_dir to retain a small RGB identity manifest; no images
are read or copied. Existing manifest pins can be passed instead. camera_rows
does no IO except reading that pinned manifest, unless manifest_dir is supplied.

per_type is an integer or {family: integer}. distribution is {family: spec}:
spec is None for natural sampling, {content: {answer: weight}} for exact answer
shares, or {bins: [{label,min,max,weight}]} for half-open numeric bins. Missing
families use natural sampling. Numeric support cannot be invented or relabelled;
unfilled largest-remainder quotas are returned as distribution_shortage refusals.
questions= preserves supplied source questions/options/pairs instead of sampling.
heldout contains recording ids (not sample qids); exclusion precedes all IO.
"""
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import re

import numpy as np

from .camera_policy import direction_margins, motion_reason
from .canon_render import render
from .common import Refusal, digest, encoded, rounded
from .plan_contract import opening_text
from .provenance import rung1_alias

TYPES = ('camera_displacement', 'camera_movement_direction', 'camera_rotation')
OPTIONS = ['A. left', 'B. right', 'C. forward', 'D. backward']
FORM = 'spec-v3.8-calculator-v2'
NATIVE = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes',
          'scannet': 'scannet', 'scannetpp': 'scannetppv2',
          'scannetppv2': 'scannetppv2', 'arkitscenes': 'arkitscenes'}
ALIASES = {'scannet': 'd1', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}


def _require(ok, reason):
    if not ok:
        raise Refusal(reason)


def _r2(x):
    return round(float(x), 2) + 0.0


def _wrap(x):
    return (x + 180) % 360 - 180 if (x + 180) % 360 else 180


def _rotation(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def _quaternion(m):
    # Symmetric eigensystem avoids a near-180-degree trace division.
    a = np.array([[m[0,0]-m[1,1]-m[2,2], m[1,0]+m[0,1], m[2,0]+m[0,2], m[2,1]-m[1,2]],
                  [m[1,0]+m[0,1], m[1,1]-m[0,0]-m[2,2], m[2,1]+m[1,2], m[0,2]-m[2,0]],
                  [m[2,0]+m[0,2], m[2,1]+m[1,2], m[2,2]-m[0,0]-m[1,1], m[1,0]-m[0,1]],
                  [m[2,1]-m[1,2], m[0,2]-m[2,0], m[1,0]-m[0,1], np.trace(m)]]) / 3
    q = np.linalg.eigh(a)[1][:, -1]
    return -q if q[3] < 0 else q


def _encode(c2w, intrinsics, raster_hw, world_up):
    c = np.asarray(c2w, dtype=float)
    k = np.broadcast_to(np.asarray(intrinsics, dtype=float), (32, 3, 3))
    hw = np.broadcast_to(np.asarray(raster_hw, dtype=float), (32, 2))
    _require(c.shape == (32,4,4) and np.isfinite(c).all(), 'invalid_c2w')
    _require(np.allclose(c[:,3,:], [0,0,0,1], atol=1e-6), 'nonrigid_c2w')
    r = c[:,:3,:3]
    _require(np.allclose(r.transpose(0,2,1) @ r, np.eye(3), atol=1e-4)
             and np.allclose(np.linalg.det(r), 1, atol=1e-4), 'nonrigid_c2w')
    _require(np.isfinite(k).all() and np.isfinite(hw).all() and (hw > 0).all()
             and (k[:,[0,1],[0,1]] > 0).all(), 'invalid_intrinsics')
    up = np.asarray(world_up, dtype=float)
    _require(up.shape == (3,) and np.isfinite(up).all() and np.linalg.norm(up) > 1e-6, 'invalid_world_up')
    up = r[0].T @ (up / np.linalg.norm(up))
    codes = []
    for i in range(32):
        rel = r[i].T @ r[0]
        codes.append([*(r[i].T @ (c[0,:3,3]-c[i,:3,3])), *_quaternion(rel),
                      2*math.atan(hw[i,0]/(2*k[i,1,1])), 2*math.atan(hw[i,1]/(2*k[i,0,0]))])
    codes[0][:7] = [0.,0.,0.,0.,0.,0.,1.]
    return dict(gt_pose9=codes, gt_up=up.tolist())


def _identity(clip):
    dataset, scene = clip['dataset'], clip['scene']
    canonical = clip.get('canonical', NATIVE.get(dataset, dataset) + '/' + scene)
    native = NATIVE.get(dataset)
    if 'alias' in clip:
        alias = clip['alias']
    elif dataset in ('d1','d2','d3'):
        alias = dataset + '/' + scene
    else:
        _require(native is not None, 'unknown_dataset_alias')
        alias = ALIASES[native] + '/v' + hashlib.sha256(('rung1 scene '+native+'/'+scene).encode()).hexdigest()[:12]
    return canonical, alias


def from_pose_row(row, *, poses=None, recording_id=None, rgb_manifest=None, manifest_dir=None):
    """Adapt p3 recording_pose.py:728-775; poses is load_poses output if needed.

    poses carries full-recording c2w, intrinsics, raster_hw, world_up and optional
    sparse frame_numbers. Frame indices select those exact cameras, never nearest.
    An all_frames32 pose_sample instead carries camera[32,9], camera_mask[32],
    anchors[1..32], metric=True and a supervised gravity vector.
    """
    si, sample = row['student_input'], row['pose_sample']
    indices = si['frame_indices']
    _require(len(indices) == len(si['frames']) == 32, 'requires_32_frames')
    clip = {k: row[k] for k in ('dataset','scene')}
    clip.update({k: row[k] for k in ('canonical','alias','physical_group') if k in row})
    clip.update(recording_id=recording_id or si.get('recording_id') or row.get('recording_id')
                or row['dataset']+'/'+row['scene'], source_qid=row['qid'],
                frames=[{**f, 'source_index': index} for f,index in zip(si['frames'], indices)],
                fps=si['fps'], total_num_frames=si['total_num_frames'])
    recording = sample.get('recording', {})
    _require(recording.get('raw_frame_numbers', indices) == indices, 'pose_frame_selection_mismatch')
    if poses is None:
        _require(sample.get('metric') is True and sample.get('gravity_mask') is True, 'requires_metric_gravity')
        _require(sample.get('anchors') == list(range(1,33)) and len(sample.get('camera', [])) == 32
                 and len(sample.get('camera_mask', [])) == 32 and all(sample['camera_mask']),
                 'requires_exact_per_frame_poses')
        clip.update(gt_pose9=copy.deepcopy(sample['camera']), gt_up=copy.deepcopy(sample['gravity']))
    else:
        if 'frame_numbers' in poses:
            lookup = {n:i for i,n in enumerate(poses['frame_numbers'])}
            _require(len(lookup) == len(poses['frame_numbers']) and all(i in lookup for i in indices),
                     'missing_exact_pose')
            selected = [lookup[i] for i in indices]
        else:
            selected = indices
        c = np.asarray(poses['c2w'])
        _require(all(type(i) is int and 0 <= i < len(c) for i in selected), 'missing_exact_pose')
        k = np.asarray(poses['intrinsics'])
        hw = np.asarray(poses['raster_hw'])
        clip.update(_encode(c[selected], k[selected] if k.ndim == 3 else k,
                            hw[selected] if hw.ndim == 2 else hw, poses['world_up']))
    if rgb_manifest is not None:
        clip['rgb_manifest'] = dict(rgb_manifest)
    _validate(clip)
    if manifest_dir is not None:
        clip['rgb_manifest'] = write_rgb_manifest(clip, manifest_dir)
    return clip


def from_gt_scene(scene, *, alias=None, recording_id=None, student_input=None, manifest_dir=None):
    """Use GTScene's canonical GT adapter without loading depth or RGB anew."""
    entry = scene.entry
    canonical = entry['canonical']
    dataset, name = canonical.split('/',1)
    rgb = _read_pin(entry['rgb_manifest'])
    timing = student_input or rgb
    _require(all(k in timing for k in ('fps','total_num_frames')), 'missing_gt_scene_timing')
    if student_input is not None:
        _require(timing['frame_indices'] == entry['frame_indices'] and timing['frames'] == rgb['frames'],
                 'rgb_manifest_selection_mismatch')
    _require(all(scene.gt.has(k) for k in range(1,33)), 'requires_exact_per_frame_poses')
    c = np.broadcast_to(np.eye(4), (32,4,4)).copy()
    for k in range(1,33):
        c[k-1,:3,:3], c[k-1,:3,3] = scene.gt.cam(k)
    clip = dict(recording_id=recording_id or canonical, dataset=dataset, scene=name,
                canonical=canonical, physical_group=entry['physical_group'],
                frames=copy.deepcopy(rgb['frames']), fps=timing['fps'], total_num_frames=timing['total_num_frames'],
                rgb_manifest=dict(entry['rgb_manifest']), gt_source=dict(entry['gt']),
                rgb_join=entry.get('rgb_binding','byte_verified'))
    if alias is not None:
        clip['alias'] = alias
    intrinsics = getattr(scene.gt, 'K_frames', None)
    clip.update(_encode(c, scene.gt.K if intrinsics is None else intrinsics,
                        [scene.gt.H,scene.gt.W], [0,0,1]))
    _validate(clip)
    if not all(k in rgb for k in ('fps','total_num_frames')):
        _require(manifest_dir is not None, 'missing_timed_rgb_manifest')
        clip['source_rgb_manifest'] = clip['rgb_manifest']
        clip['rgb_manifest'] = write_rgb_manifest(clip,manifest_dir)
        clip['rgb_join'] = 'identity_only'
    return clip


def _read_pin(pin):
    path = Path(pin['path'])
    _require(path.is_absolute() and str(path.resolve()).startswith('/scratch/'), 'manifest_must_be_on_scratch')
    _require(path.stat().st_size <= 128*1024, 'rgb_manifest_too_large')
    data = path.read_bytes()
    _require(hashlib.sha256(data).hexdigest() == pin['sha256'], 'rgb_manifest_hash_mismatch')
    return json.loads(data)


def write_rgb_manifest(clip, output_dir):
    """Retain a metadata-only identity manifest; never assert RGB byte verification."""
    _validate(clip)
    canonical, _ = _identity(clip)
    doc = dict(canonical=canonical, recording_id=clip['recording_id'],
               frames=clip['frames'], frame_indices=[f['source_index'] for f in clip['frames']],
               fps=clip['fps'], total_num_frames=clip['total_num_frames'],
               verified=False, binding='identity_only')
    data = (encoded(doc)+'\n').encode()
    directory = Path(output_dir).resolve()
    _require(str(directory).startswith('/scratch/'), 'manifest_must_be_on_scratch')
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ('RGB_'+hashlib.sha256(data).hexdigest()+'.json')
    if path.exists():
        _require(path.read_bytes() == data, 'manifest_collision')
    else:
        with path.open('xb') as f:
            f.write(data)
    return {'path':str(path), 'sha256':hashlib.sha256(data).hexdigest()}


def _validate(clip):
    _require(all(isinstance(clip.get(k),str) and clip[k] for k in ('recording_id','dataset','scene')), 'missing_clip_identity')
    frames = clip['frames']
    _require(isinstance(frames,list) and len(frames) == 32, 'requires_32_frames')
    total, fps = clip['total_num_frames'], clip['fps']
    _require(type(total) is int and total >= 32 and type(fps) in (int,float)
             and math.isfinite(fps) and fps > 0, 'invalid_clip_timing')
    indices = []
    for f in frames:
        _require(isinstance(f.get('path'),str) and Path(f['path']).is_absolute()
                 and re.fullmatch('[0-9a-fA-F]{64}',f.get('sha256','')) is not None, 'invalid_rgb_frame')
        i = f['source_index']
        _require(type(i) is int and 0 <= i < total, 'invalid_source_index')
        indices.append(i)
    _require(indices == sorted(set(indices)), 'frame_indices_must_increase')
    p, up = np.asarray(clip['gt_pose9'],dtype=float), np.asarray(clip['gt_up'],dtype=float)
    _require(p.shape == (32,9) and np.isfinite(p).all(), 'invalid_pose9')
    _require(np.allclose(np.linalg.norm(p[:,3:7],axis=1),1,atol=1e-4,rtol=0), 'invalid_quaternion')
    _require(np.allclose(p[0,:3],0,atol=1e-7) and np.allclose(_rotation(p[0,3:7]),np.eye(3),atol=1e-6),
             'nonidentity_reference_pose')
    _require(((p[:,7:] > 0) & (p[:,7:] < math.pi)).all(), 'invalid_fov')
    _require(up.shape == (3,) and np.isfinite(up).all()
             and abs(np.linalg.norm(up)-1) < 1e-4, 'invalid_gt_up')


class _Geometry:
    def __init__(self, clip):
        p, up = np.asarray(clip['gt_pose9']), np.asarray(clip['gt_up'])
        down = -up / np.linalg.norm(up)

        def basis(r):
            f = r[:,2].copy()
            f -= float(f @ down)*down
            _require(np.linalg.norm(f) >= 1e-6, 'vertical_camera_heading')
            f /= np.linalg.norm(f)
            return np.column_stack((np.cross(down,f), down, f))

        to_l1 = np.diag([1.,-1.,1.]) @ basis(np.eye(3)).T
        self.poses = []
        self.exact_poses = []
        for index,code in enumerate(p):
            q = code[3:7] / np.linalg.norm(code[3:7])
            r = _rotation(q).T
            centre = -r @ code[:3]
            if index == 0:
                r,centre = np.eye(3),np.zeros(3)
            self.exact_poses.append((to_l1 @ centre, to_l1 @ basis(r)))
            self.poses.append((np.array(rounded(to_l1 @ centre)), np.array(rounded(to_l1 @ basis(r)))))

    def pair(self, i, j):
        ti, ri = self.poses[i-1]
        tj, rj = self.poses[j-1]
        local = ri.T @ (tj-ti)
        distance = _r2(np.linalg.norm(local))
        local[1] *= -1
        dx,dy,dz = map(_r2,local)
        a,b = ri[[0,2],2], rj[[0,2],2]
        turn = _wrap(round(math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0],float(a@b)))))
        eti, eri = self.exact_poses[i-1]
        etj, erj = self.exact_poses[j-1]
        exact_local = eri.T @ (etj-eti)
        ea, eb = eri[[0,2],2], erj[[0,2],2]
        yaw = math.degrees(math.atan2(ea[0]*eb[1]-ea[1]*eb[0], float(ea@eb)))
        return dict(dx=dx,dy=dy,dz=dz,distance=distance,turn=turn,
                    gt_dx=float(exact_local[0]), gt_dz=float(exact_local[2]),
                    gt_distance=float(np.linalg.norm(exact_local)),
                    gt_horizontal=float(np.linalg.norm(exact_local[[0,2]])),gt_yaw=yaw)


def _movement_options(options):
    parsed = [re.fullmatch(r'([A-Z])\.\s*(left|right|forward|backward)',o.strip(),re.I) for o in options]
    _require(2 <= len(parsed) <= 4 and all(parsed), 'unsupported_movement_option')
    values = [(m[1].upper(),m[2].lower()) for m in parsed]
    _require(len({v[0] for v in values}) == len({v[1] for v in values}) == len(values), 'unsupported_movement_option')
    return values


def _label(t, v):
    if t == 'camera_displacement':
        return f"{v['distance']:.2f}"
    if t == 'camera_rotation':
        return str(v['turn'])
    scores = {'forward':v['dz'],'backward':-v['dz'],'right':v['dx'],'left':-v['dx']}
    return max(scores,key=scores.get)


def _motion_reason(t, v):
    return motion_reason(t, distance=v.get('gt_distance',v['distance']),
                         horizontal=v.get('gt_horizontal',math.hypot(v['dx'],v['dz'])),
                         yaw=v.get('gt_yaw',v['turn']))


def t2_reason(t, v, options=None):
    reason = _motion_reason(t,v)
    if reason:
        return reason
    if t == 'camera_movement_direction':
        scores = {'forward':v['dz'],'backward':_r2(-v['dz']),'right':v['dx'],'left':_r2(-v['dx'])}
        try:
            raw = {'forward':v['gt_dz'], 'backward':-v['gt_dz'],
                   'right':v['gt_dx'], 'left':-v['gt_dx']}
            direction_margins(raw[o] for _,o in _movement_options(OPTIONS if options is None else options))
            direction_margins(scores[o] for _,o in _movement_options(OPTIONS if options is None else options))
        except Refusal as exc:
            return exc.reason
    if t == 'camera_movement_direction':
        win,runner = sorted((abs(v['dx']),abs(v['dz'])), reverse=True)
        if win < .15 or win <= abs(v['dy']) or win-runner < .10:
            return 'movement_margin'
    if t == 'camera_rotation' and abs(v['turn']) >= 165:
        return 'rotation_near_180'
    return None


def _question(t, i, j):
    if t == 'camera_displacement':
        return f'Approximately how far (in meters) did the camera move between frame {i} and frame {j} of 32?'
    if t == 'camera_rotation':
        return f'What is the signed camera rotation in degrees between frame {i} and frame {j} of 32? Positive means left; use (-180, 180].'
    return (f"During the sequence between frame {i} and frame {j} of 32, what was the primary consistent direction "
            "of the camera's movement relative to its orientation at the start? The options are Left, Right, Forward and Backward.")


def _row(clip, t, i, j, v, source=None):
    source = source or {}
    si = source.get('student_input',source)
    q = si.get('question',_question(t,i,j))
    options = list(si.get('options',OPTIONS if t == TYPES[1] else []))
    binding = dict(i=i,j=j,M=32)
    events = [dict(role='assistant',kind='plan',target_loss=1,format=FORM,text=opening_text(t,binding))]

    def text(s):
        events.append(dict(role='assistant',kind='canonical_text',target_loss=1,text=s))

    def para():
        events.append(dict(role='assistant',kind='canonical_paragraph',target_loss=1))

    reason = _motion_reason(t,v)
    _require(reason is None, reason)
    margins = {}
    label = _label(t,v)
    if t == 'camera_rotation':
        name, prefix = 'turn',''
        response = f"turn = {v['turn']:+d} deg"
        values = {'c1.turn':dict(value=v['turn'],unit='degree')}
    else:
        name,prefix = 'move',' '
        text(f"The move tool gives the camera displacement from frame {i} to frame {j} in frame {i}'s level frame (x right, y up, z forward).")
        response = (f"dx = {v['dx']:+.2f} m, dy = {v['dy']:+.2f} m, dz = {v['dz']:+.2f} m, distance = {v['distance']:.2f} m")
        values = {'c1.delta':dict(value=[v[k] for k in ('dx','dy','dz')],unit='m'),
                  'c1.distance':dict(value=v['distance'],unit='m')}
    events.extend([dict(role='assistant',kind='tool_call',target_loss=1,call_id='c1',prefix=prefix,
                        name=name,arguments={'from':i,'to':j},token=f'<{name} from={i} to={j}>',object=None),
                   dict(role='tool',kind='tool_response',target_loss=0,call_id='c1',name=name,text=response,values=values)])
    if t == 'camera_movement_direction':
        opts = _movement_options(options)
        scores = {'forward':v['dz'],'backward':_r2(-v['dz']),'right':v['dx'],'left':_r2(-v['dx'])}
        expl = {'forward':'dz','backward':'-dz','right':'dx','left':'-dx'}
        ranked = sorted((o for _,o in opts),key=lambda o:-scores[o])
        margin_m, margin_rel = direction_margins(scores[o] for _,o in opts)
        raw = {'forward':v['gt_dz'], 'backward':-v['gt_dz'], 'right':v['gt_dx'], 'left':-v['gt_dx']}
        raw_m, raw_rel = direction_margins(raw[o] for _,o in opts)
        margins = dict(margin_m=margin_m,margin_rel=margin_rel,
                       unrounded_margin_m=raw_m,unrounded_margin_rel=raw_rel)
        label = ranked[0]
        para()
        text('Scoring each option by the matching component: '+'; '.join(f'{o} = {expl[o]} = {scores[o]:.2f} m' for _,o in opts)+'.')
        para()
        answer = next(letter for letter,o in opts if o == label)
        text(f'The largest is {label}. That matches option {answer}.')
        display,decision = None,dict(mode='option',result=label)
    else:
        _require(not options, 'numeric_camera_options')
        para()
        text(f"The camera rotation is {v['turn']} degrees; positive yaw means left." if t == TYPES[2] else
             f"The printed distance is {v['distance']:.2f} m, so the camera moved about {v['distance']:.2f} m.")
        answer = label
        display = dict(unit='degree' if t == TYPES[2] else 'm',decimals=0 if t == TYPES[2] else 2,factor=1.0)
        decision = dict(mode='numeric',result=answer,unit=display)
    events.append(dict(role='assistant',kind='decision',target_loss=1,family=t,binding=binding,call_ids=['c1'],**decision))
    canonical,alias = _identity(clip)
    pose_hash = digest([clip['gt_pose9'],clip['gt_up']])
    gt_hash = clip.get('gt_source',{}).get('sha256',pose_hash)
    qid = source.get('qid') or 'pose-camera-'+digest([clip['recording_id'],canonical,
            [f['source_index'] for f in clip['frames']],t,q,options])[:32]
    question = dict(question_type=t,question=q,options=options)
    provenance = dict(source=clip.get('source_qid',clip['recording_id']),line=None,
                      alias=rung1_alias(canonical, alias),source_alias=alias,
                      canonical=canonical,physical_group=clip.get('physical_group',canonical),
                      recording_id=clip['recording_id'],frame_indices=[f['source_index'] for f in clip['frames']],
                      gt_sha256=gt_hash,pose_sha256=pose_hash,rgb_manifest=dict(clip['rgb_manifest']),
                      rgb_join=clip.get('rgb_join','identity_only'),source_question_sha256=digest(question),
                      source_row_sha256=digest(dict(recording_id=clip['recording_id'],gt_sha256=gt_hash,pose_sha256=pose_hash,
                          frames=clip['frames'],question=question)),
                      score_nomination_allowed=False,training_eligibility='pending_release_gates')
    provenance.update({k:copy.deepcopy(clip[k]) for k in ('gt_source','source_rgb_manifest') if k in clip})
    return dict(schema='derivgen-row-v2',form=FORM,readout_mode='gt',answer_policy='trace_value',
                trace_revision='3.11',frame_pair_rule='frame_gap',frame_pair_turn=[],
                infrastructure_only=False,qid=qid,source_qid=qid,**question,answer=answer,gt_answer=answer,
                events=events,display=display,**margins,points={},substitutions={},head_layout='per_frame',
                gt_pose9=copy.deepcopy(clip['gt_pose9']),gt_up=list(clip['gt_up']),gt_camera_raw={},
                provenance=provenance,frame_pair_r=[],
                plan_branch=dict(family=t,frame_choices=[],substitutions={}),**render(events,answer))


def _buckets(spec, t):
    if spec is None:
        return None
    if 'bins' in spec:
        _require(t != TYPES[1], 'movement_requires_content_distribution')
        result = []
        for b in spec['bins']:
            lo,hi,w = float(b['min']),float(b['max']),float(b['weight'])
            _require(math.isfinite(lo) and math.isfinite(hi) and lo < hi, 'invalid_distribution_bin')
            result.append((str(b['label']),lo,hi,w))
        _require(all(a[2] <= b[1] for a,b in zip(sorted(result,key=lambda b:b[1]),sorted(result,key=lambda b:b[1])[1:])),
                 'overlapping_distribution_bins')
    else:
        content = spec.get('content',spec)
        result = [(str(k),None,None,float(w)) for k,w in content.items()]
        if t == TYPES[1]:
            _require(all(k in ('left','right','forward','backward') for k,_,_,_ in result), 'invalid_movement_distribution')
        else:
            _require(all(math.isfinite(float(k)) for k,_,_,_ in result), 'numeric_distribution_requires_numbers_or_bins')
            _require(len({float(k) for k,_,_,_ in result}) == len(result), 'duplicate_numeric_bucket')
    _require(result and len({b[0] for b in result}) == len(result)
             and all(math.isfinite(w) and w >= 0 for _,_,_,w in result)
             and sum(b[3] for b in result) > 0, 'invalid_distribution_weights')
    return result


def _bucket(label, buckets, t):
    for key,lo,hi,_ in buckets:
        matches = lo <= float(label) < hi if lo is not None else (
                label == key if t == TYPES[1] else float(label) == float(key))
        if matches:
            return key
    return None


def _quotas(n, buckets):
    total = sum(b[3] for b in buckets)
    raw = {k:n*w/total for k,_,_,w in buckets}
    result = {k:math.floor(v) for k,v in raw.items()}
    for k in sorted(raw,key=lambda k:(-(raw[k]-result[k]),k))[:n-sum(result.values())]:
        result[k] += 1
    return result


def camera_rows(clip, *, seed, per_type, distribution, heldout=frozenset(), questions=None, manifest_dir=None):
    """Return unique canonical rows and structured refusals, without GT substitution.

    Pair sampling is chronological over all exact per-frame slots (i<j), shuffled
    by seed and recording/selection identity. A supplied question fixes its pair,
    as in canon, and must name `between frame i and frame j of 32`.
    Refusals aggregate T2 pair rejections and explicit distribution shortages.
    questions mode preserves all given eligible questions up to per_type quotas;
    its source answers are intentionally ignored and GT computes every label.
    """
    recording = clip.get('recording_id')
    if recording in heldout:
        return [],[dict(recording_id=recording,reason='heldout_recording',count=1)]
    from .goal_exclusions import refuse_goal_scene
    canonical, alias = _identity(clip)
    try:
        refuse_goal_scene(canonical, alias, clip['scene'], clip['dataset']+'/'+clip['scene'])
    except Refusal as exc:
        return [], [dict(recording_id=recording, reason=exc.reason, count=1)]
    _validate(clip)
    _require(isinstance(distribution,dict), 'distribution_must_be_mapping')
    counts = {t:per_type if type(per_type) is int else per_type.get(t,0) for t in TYPES}
    _require(all(type(n) is int and n >= 0 for n in counts.values()), 'invalid_per_type')
    buckets = {t:_buckets(distribution.get(t),t) for t in TYPES}
    clip = dict(clip)
    if 'rgb_manifest' not in clip:
        _require(manifest_dir is not None, 'missing_rgb_manifest_pin')
        clip['rgb_manifest'] = write_rgb_manifest(clip,manifest_dir)
    manifest = _read_pin(clip['rgb_manifest'])
    _require(all(manifest.get(k) == clip[k] for k in ('frames','fps','total_num_frames')), 'rgb_manifest_selection_mismatch')
    geometry = _Geometry(clip)
    rows,refusals = [],[]

    def refuse(reason, t=None, count=1, **extra):
        refusals.append(dict(recording_id=recording,reason=reason,count=count,
                             **({'question_type':t} if t else {}),**extra))

    if questions is not None:
        seen,used = set(),dict.fromkeys(TYPES,0)
        for source in questions:
            t = source['question_type']
            _require(t in TYPES,'unsupported_camera_type')
            si = source.get('student_input',source)
            m = re.search(r'between frame (\d+) and frame (\d+) of (\d+)',si['question'],re.I)
            _require(m is not None,'missing_camera_frame_pair')
            i,j,M = map(int,m.groups())
            _require(M == 32 and 1 <= i <= 32 and 1 <= j <= 32 and i != j,'invalid_camera_frame_pair')
            key = (t,si['question'],tuple(si.get('options',[])))
            _require(key not in seen,'duplicate_camera_question')
            seen.add(key)
            v = geometry.pair(i,j)
            reason = t2_reason(t,v,si.get('options',OPTIONS if t == TYPES[1] else []))
            if reason:
                refuse(reason,t,qid=source.get('qid'),frames=[i,j])
            elif used[t] < counts[t]:
                rows.append(_row(clip,t,i,j,v,source));used[t] += 1
        return rows,refusals

    pairs = list(itertools.combinations(range(1,33),2))
    random.Random(digest([seed,recording,[f['source_index'] for f in clip['frames']]])).shuffle(pairs)
    values = {(i,j):geometry.pair(i,j) for i,j in pairs}
    for t,n in counts.items():
        if not n:
            continue
        pool, rejected = [],{}
        for i,j in pairs:
            v = values[i,j]
            reason = t2_reason(t,v)
            if reason:
                rejected[reason] = rejected.get(reason,0)+1
            else:
                pool.append((i,j,v))
        for reason,count in rejected.items():
            refuse(reason,t,count,candidate_pairs=len(pairs),eligible_pairs=len(pool))
        if buckets[t] is None:
            chosen = pool[:n]
            if len(chosen) < n:
                refuse('candidate_shortage',t,n-len(chosen),requested=n,available=len(pool))
        else:
            quotas = _quotas(n,buckets[t]);chosen=[]
            by_bucket = {k:[] for k in quotas}
            for pair in pool:
                k = _bucket(_label(t,pair[2]),buckets[t],t)
                if k is not None:
                    by_bucket[k].append(pair)
            for k,want in quotas.items():
                chosen.extend(by_bucket[k][:want])
                if len(by_bucket[k]) < want:
                    refuse('distribution_shortage',t,want-len(by_bucket[k]),bucket=k,requested=want,available=len(by_bucket[k]))
        rows.extend(_row(clip,t,i,j,v) for i,j,v in chosen)
    return rows,refusals
