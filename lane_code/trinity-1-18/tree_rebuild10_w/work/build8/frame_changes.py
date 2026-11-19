"""Thread the visible frame count through locally owned readers."""
from pathlib import Path
T=Path(__file__).resolve().parents[2]/'work/tree_r1'
def edit(name,pairs):
 p=T/name;s=p.read_text()
 for a,b in pairs:
  assert a in s,(name,a)
  s=s.replace(a,b)
 p.write_text(s)
edit('student_pilot/carrier_c1_routing.py',[
 ('pose9: [32, 9]','pose9: [F, 9], F in {32, 64}'),('`fov` [32, 2]','`fov` [F, 2]'),
 ('finite [32, 9]','finite [32 or 64, 9]'),('finite [32, 2]','finite [F, 2]'),
 ('type(k) is not int or not 1 <= k <= 32','type(k) is not int or not 1 <= k <= len(self.p)'),
 ('def query_tensor(queries, k_max=None):','def query_tensor(queries, k_max=None, *, frame_count=32):'),
 ('"""[32, K, 2] stencil queries per frame plus each click\'s (frame, slot) index."""\n    per_frame, index = [[] for _ in range(32)], []',
  '"""[F, K, 2] stencil queries and each click\'s (frame, slot) index."""\n    if type(frame_count) is not int or frame_count not in (32, 64):\n        raise RenderError("unsupported_frame_count")\n    per_frame, index = [[] for _ in range(frame_count)], []'),
 ('type(frame) is not int or not 1 <= frame <= 32','type(frame) is not int or not 1 <= frame <= frame_count'),
 ('np.full((32, k, 2)','np.full((frame_count, k, 2)'),
 ('len(frames) != 32 or [f[\'source_index\']','len(frames) not in (32, 64) or [f[\'source_index\']')])
edit('student_pilot/carrier_c1_run.py',[
 ('routing.query_tensor(queries)','routing.query_tensor(queries, frame_count=batch["aux_camera_positions"].shape[1])'),
 ('uv = torch.full((32, 1, 2), 500.)','uv = torch.full((batch["aux_camera_positions"].shape[1], 1, 2), 500.)')])
edit('student_pilot/h1_faithful.py',[
 ('routing.query_tensor([])','routing.query_tensor([], frame_count=batch["aux_camera_positions"].shape[1])')])
edit('student_pilot/ground_sources.py',[
 ("    candidates = []\n    for frame in range(1, 33):", "    count = len(cache['frames'])\n    if count not in (32, 64) or set(cache['frames']) != {str(k) for k in range(count)}:\n        raise ValueError('cache_frame_count_or_order')\n    candidates = []\n    for frame in range(1, count + 1):"),
 ('if len(frames) != 32 or not identity:', 'if len(frames) not in (32, 64) or len(frame_map.source_indices) != len(frames) or not identity:'),
 ('tower_requires_32_frames_and_identity','tower_requires_32_or_64_frames_and_identity'),
 ('if len(detected) != 32:', 'if len(detected) != len(self.frames):')])
edit('student_pilot/carrier_c1_data.py',[
 ("len(inputs['frames']) != 32 or len(inputs['frame_indices']) != 32", "len(inputs['frames']) not in (32, 64) or len(inputs['frame_indices']) != len(inputs['frames'])"),
 ('C1 preservation rows require 32 pinned native frames (VQA: 64 with anchor_slots)', 'C1 preservation rows require 32 or 64 pinned native frames')])
edit('generator/derivgen_v7/derivgen/camera_rows.py',[
 ('exact 32-frame metric pose clips','32- or 64-frame metric pose clips'),
 ('gt_pose9[32,9]','gt_pose9[F,9]'),('Frame slots are 1..32.','Frame slots are 1..F.'),
 ('    k = np.broadcast_to(np.asarray(intrinsics, dtype=float), (32, 3, 3))', '    count = len(c)\n    _require(count in (32, 64), "requires_32_or_64_frames")\n    k = np.broadcast_to(np.asarray(intrinsics, dtype=float), (count, 3, 3))'),
 ('(32, 2))','(count, 2))'),('c.shape == (32,4,4)','c.shape == (count,4,4)'),('for i in range(32):','for i in range(count):'),
 ("    _require(len(indices) == len(si['frames']) == 32, 'requires_32_frames')", "    count = len(indices)\n    _require(count in (32, 64) and len(si['frames']) == count, 'requires_32_or_64_frames')"),
 ("list(range(1,33)) and len(sample.get('camera', [])) == 32", "list(range(1,count+1)) and len(sample.get('camera', [])) == count"),
 ("len(sample.get('camera_mask', [])) == 32", "len(sample.get('camera_mask', [])) == count"),
 ("    _require(all(scene.gt.has(k) for k in range(1,33))", "    count = len(rgb['frames'])\n    _require(count in (32, 64), 'requires_32_or_64_frames')\n    _require(all(scene.gt.has(k) for k in range(1,count+1))"),
 ('(32,4,4)).copy()', '(count,4,4)).copy()'),('for k in range(1,33):','for k in range(1,count+1):'),
 ("len(frames) == 32, 'requires_32_frames'", "len(frames) in (32, 64), 'requires_32_or_64_frames'"),
 ('total >= 32','total >= len(frames)'),('p.shape == (32,9)','p.shape == (len(frames),9)'),
 ('def _question(t, i, j):','def _question(t, i, j, frame_count=32):'),('of 32','of {frame_count}'),
 ('_question(t,i,j)','_question(t,i,j,len(clip["frames"]))'),('binding = dict(i=i,j=j,M=32)','binding = dict(i=i,j=j,M=len(clip["frames"]))'),
 ('M == 32 and 1 <= i <= 32 and 1 <= j <= 32','M == len(clip["frames"]) and 1 <= i <= M and 1 <= j <= M'),
 ('itertools.combinations(range(1,33),2)','itertools.combinations(range(1,len(clip["frames"])+1),2)')])
