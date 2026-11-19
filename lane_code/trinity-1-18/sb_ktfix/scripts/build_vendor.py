from pathlib import Path
import hashlib,json,difflib,ast
ROOT=Path(__file__).resolve().parents[1]
tree=Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449')
reader=Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook')
pins={}; originals={}
for base,parts in [(tree,['student_pilot','trace_format','rk','headcall','hrp']),(reader,['e2e_reader','heads/selector/sl118'])]:
 for part in parts:
  for p in (base/part).rglob('*.py'):
   if '__pycache__' in p.parts:continue
   q=ROOT/'code/vendor'/p.relative_to(base); q.parent.mkdir(parents=True,exist_ok=True)
   b=p.read_bytes();q.write_bytes(b);pins[str(p)]=hashlib.sha256(b).hexdigest();originals[str(q.relative_to(ROOT))]=b.decode()
p=reader/'heads/selector/selector_head.py';q=ROOT/'code/vendor/heads/selector/selector_head.py';q.write_bytes(p.read_bytes());pins[str(p)]=hashlib.sha256(q.read_bytes()).hexdigest();originals[str(q.relative_to(ROOT))]=q.read_text()
def edit(rel,changes):
 p=ROOT/'code/vendor'/rel;s=p.read_text()
 for old,new in changes:
  assert old in s,(rel,old);s=s.replace(old,new)
 p.write_text(s)
edit('student_pilot/routed_candidates.py',[
 ('def lift_grid(geo):','def lift_grid(geo, n_frames=32):'),('range(1, 33)','range(1, n_frames + 1)'),
 ('grids=None, phrase=None):','grids=None, phrase=None, n_frames=32):'),('lift_grid(geo) if','lift_grid(geo, n_frames) if'),
 ('def visible_voxels(voxels, geo):','def visible_voxels(voxels, geo, n_frames=32):'),
 ('def features(candidate, geo=None):','def features(candidate, geo=None, n_frames=32):'),
 ('visible_voxels(candidate.voxels, geo)','visible_voxels(candidate.voxels, geo, n_frames)'),
 ('def scene_candidates(by_name, geo=None):','def scene_candidates(by_name, geo=None, n_frames=32):'),('features(c, geo)','features(c, geo, n_frames)')])
edit('student_pilot/routed_features.py',[('def __init__(self, source):','def __init__(self, source, n_frames=32):'),('range(1, 33) if source.has(k)','range(1, n_frames + 1) if source.has(k)')])
edit('e2e_reader/stage1.py',[('def __init__(self, detect, head, geometry):','def __init__(self, detect, head, geometry, n_frames=32):'),('self.geometry, self.exact = geometry, F.Geometry(geometry)','self.n_frames = n_frames\n        self.geometry, self.exact = geometry, F.Geometry(geometry, n_frames)'),('F.candidates.lift_grid(geometry)','F.candidates.lift_grid(geometry, n_frames)'),('grids=self.grids, phrase=name)','grids=self.grids, phrase=name, n_frames=self.n_frames)'),('F.candidates.scene_candidates(pools, self.geometry)','F.candidates.scene_candidates(pools, self.geometry, self.n_frames)')])
edit('e2e_reader/grounding.py',[('def __init__(self, propose, select, mask_shape, frames):','def __init__(self, propose, select, mask_shape, frames=32):'),('self.queries = []','if self.frames not in (32, 64):\n            raise ValueError("tower kit requires N=32 or N=64")\n        self.queries = []')])
edit('student_pilot/scene_state.py',[('rgb_sha256: tuple = ()','rgb_sha256: tuple = ()\n    n_frames: int = 32'),('len(x) != 32','len(x) != self.n_frames or self.n_frames not in (32, 64)'),('len(self.rgb_sha256) != 32','len(self.rgb_sha256) != self.n_frames'),('len(a) != 32','len(a) != self.n_frames')])
edit('student_pilot/geometry_profiles.py',[('K.shape != (32, 3, 3) or A.shape != (32, 3, 3) or C.shape != (32, 4, 4)','K.shape != (self.frame_map.n_frames, 3, 3) or A.shape != (self.frame_map.n_frames, 3, 3) or C.shape != (self.frame_map.n_frames, 4, 4)'),('self.depth_grid.shape[0] != 32','self.depth_grid.shape[0] != self.frame_map.n_frames'),('1 <= frame <= 32','1 <= frame <= self.frame_map.n_frames')])
# The reader authenticates validate's body before removing its existing gravity guard.
p=ROOT/'code/vendor/student_pilot/geometry_profiles.py';s=p.read_text();node=next(n for n in ast.walk(ast.parse(s)) if isinstance(n,ast.FunctionDef) and n.name=='validate');body='\n'.join(s.splitlines()[node.lineno-1:node.end_lineno])+'\n';sealed=hashlib.sha256(body.encode()).hexdigest()
edit('e2e_reader/geometry.py',[('05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a',sealed),('FrameMap(tuple(anchors))','FrameMap(tuple(anchors), n_frames=len(anchors))')])
# Optional all-slot depth sampling keeps the LM's anchor metadata at 32.
edit('student_pilot/tower_read.py',[
 ('points_grid: np.ndarray = None','depth_slots: np.ndarray = None\n    points_grid: np.ndarray = None'),
 ('if any(arrays[k].shape != (32, 51, 51)', 'depth_slots = slots if self.depth_slots is None else np.asarray(self.depth_slots)\n        if not (np.array_equal(depth_slots, slots) or np.array_equal(depth_slots, np.arange(len(raw)))):\n            raise TowerError("Invalid depth slots")\n        arrays["depth_slots"] = depth_slots\n        if any(arrays[k].shape != (len(depth_slots), 51, 51)'),
 ('points.shape != (32, 51, 51, 3)','points.shape != (len(depth_slots), 51, 51, 3)'),
 ("data['points_grid'] if 'points_grid' in data else None, data['grid_uv'])", "data['depth_slots'] if 'depth_slots' in data else None,\n                        data['points_grid'] if 'points_grid' in data else None, data['grid_uv'])"),
 ('def run(self, batch):','def run(self, batch, *, all_depth=False):'),
 ('for offset in range(0, 32, self.chunk):\n            selected = slots[offset:offset + self.chunk]', 'depth_slots = np.arange(len(frames)) if all_depth else slots\n        for offset in range(0, len(depth_slots), self.chunk):\n            selected = depth_slots[offset:offset + self.chunk]'),
 ('indices, slots, points)','indices, slots, depth_slots, points)')])
# CPU camera formatter uses exact AST definitions, without importing training dependencies.
s=(tree/'student_pilot/carrier_c1_routing.py').read_text();nodes=ast.parse(s).body
names={'RenderError','OwnGeometry','level_basis','r8','r2','s2','f2','vec','wrap'}
segments=[ast.get_source_segment(s,n) for n in nodes if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
(ROOT/'code/cpu_formatter.py').write_text('import math\nimport numpy as np\nfrom student_pilot.camera_targets import rotation_from_xyzw\nFLIP = np.diag([1., -1., 1.])\nSTENCIL = np.array([(dx,dy) for dx in np.linspace(-10,10,5) for dy in np.linspace(-10,10,5)])\n\n'+'\n\n'.join(segments)+'\n')
lines=[];patch=[]
for rel,old in originals.items():
 new=(ROOT/rel).read_text()
 if old==new:continue
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel+'.original',tofile=rel))
 for tag,a,b,c,d in difflib.SequenceMatcher(None,old.splitlines(),new.splitlines()).get_opcodes():
  if tag!='equal':lines.append({'file':rel,'original_lines':list(range(a+1,b+1)),'edited_lines':list(range(c+1,d+1)),'old':old.splitlines()[a:b],'new':new.splitlines()[c:d]})
(ROOT/'out/EDITED_LINES.json').write_text(json.dumps({'input_sha256':pins,'edits':lines},indent=2)+'\n')
(ROOT/'out/EDITED_LINES.patch').write_text(''.join(patch))
(ROOT/'inputs/CODE_SOURCES.json').write_text(json.dumps({'input_sha256':pins},indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 2: The lane vendors the locally mirrored reader and tree code, parameterizes lifting, visibility and geometry for 32 or 64 tower frames, and preserves the selector feature formulas and 32 language-model anchors. Exact source hashes and every edited line are recorded. The named tree path, dev-S1 routed-item source and K1 peak-memory entry are missing; no GPU work has run.\n')
print('vendored',len(pins),'edited blocks',len(lines))
