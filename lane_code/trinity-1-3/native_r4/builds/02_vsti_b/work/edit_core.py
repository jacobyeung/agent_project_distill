from pathlib import Path
b=Path.cwd();p=b/'code/policy.py';s=p.read_text();s=s.replace("# Ordinary XML thinking and answer tags are not calls.\nTAIL=re.compile(r'<(?!(?:think|answer|tool_response)\\b)([A-Za-z_][A-Za-z_0-9]*)\\b[^<>\\n]*>$')", "# The trained grammar is installed lazily after the authenticated tree.\ndef tail_pattern():\n    from reader_policy import CALL_NAMES\n    return re.compile(r'<(?:'+ '|'.join(map(re.escape,CALL_NAMES))+r')\\b[^<>\\n]*>$')")
s=s.replace('original=D.respond_state;original_tail=D.trace313.extra_tail','original=D.respond_state;original_tail=D.trace313.extra_tail;tail=tail_pattern()').replace('TAIL.search(text)','tail.search(text)');p.write_text(s)
p=b/'code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py';s=p.read_text();start=s.index('        def prepare_one():');end=s.index('        import gravity_guard',start);original=s[start:end]
helper='''def prepare_capture(raw_path,capture,row,output,prefill,diagnostics):
    """C8r capture preparation; prefill supplies the checkpoint heads and batch."""
    import numpy as np
    import torch
    from student_pilot.tower_read import TowerState
    state=TowerState.from_npz(raw_path)
    if state.frame_indices[state.anchor_slots].tolist()!=capture['anchor_indices']:
        raise ValueError('Tower capture anchors differ')
    own,batch=prefill(row)
    if own.depth_map is None or own.gravity is None:raise ValueError('Checkpoint lacks own depth/gravity')
    axis=torch.as_tensor(state.grid_uv.copy(),device=own.depth_map.device)
    yy,xx=torch.meshgrid(axis,axis,indexing='ij');uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
    with torch.no_grad():depth=own.depth_head.query(own.depth_map,uv).double().cpu().numpy().reshape(32,51,51)
    with np.load(raw_path,allow_pickle=False) as z:
        hw=z['source_hw'];diagnostics['tower_gravity']=z['gravity_up'].tolist()
    value=convert(state,depth,own.gravity,hw,output,diagnostics=diagnostics)
    return dict(value,conditioning_question_id=row['qid'],prefill_sha256=digest(batch['input_ids'].cpu().tolist()))

'''
s=s[:start]+'''        def prepared(row):
            batch=move_batch(runtime.prompt_batch(processor,row,cfg,'routed'),args.device)
            return prefill(model,processor,batch,max_new_tokens=16384).heads,batch
        def prepare_one():
            return prepare_capture(p,c,row,output,prepared,diagnostics)
'''+s[end:];s=s.replace('def prepare(args):',helper+'def prepare(args):');p.write_text(s)
p=b/'code/engine.py';s=p.read_text();start=s.index('    def prefill(self,state,row):');end=s.index('    def generate',start)
s=s[:start]+'''    def prefill(self,row):
        import torch
        from student_pilot.carrier_c1_decode import _prepare_decode
        from student_pilot.ground_context import closed_adapters
        batch=self.batch(row)
        return closed_adapters(torch.no_grad()(_prepare_decode))(self.model,self.processor,batch,max_new_tokens=16384).heads,batch
'''+s[end:]
s=s.replace("            state=TowerState.from_npz(p)","            if not boundary.synthetic:\n                return G.prepare_capture(p,c,row,output,boundary.prefill,diagnostics)\n            state=TowerState.from_npz(p)").replace('depth,up=boundary.prefill(state) if boundary.synthetic else boundary.prefill(state,row)','depth,up=boundary.prefill(state)');p.write_text(s)
p=b/'tests/test_read.py';s=p.read_text().replace("names=['ground','depth_at','box_3d','gap','surface_pair','extent_ends','dist','closest','cam_dist','angle','area','mystery']","from reader_policy import CALL_NAMES\n        names=[n for n in CALL_NAMES if n not in policy.SERVED]")
s=s.replace('    def test_camera_dispatch(self):', '''    def test_text_tags_remain_text(self):
        for tag in ('<frame 5>','<obj>','<mystery x=1>'):
            decoded=drive('<think>'+tag+'</think>A',self.geo)
            self.assertEqual(decoded['calls'],[])
            self.assertIn(tag,decoded['text'])
            self.assertEqual(scorer.final_text(decoded),'A')
    def test_camera_dispatch(self):''');p.write_text(s)
# Forward the fixture flag instead of accidentally running the real CPU tower.
p=b/'out/rehearsal/run_rehearsal.py';s=p.read_text().replace("    result=subprocess.run(args,", "    if a.fixture_tower:args.append('--fixture-tower')\n    result=subprocess.run(args,").replace('value=inner(dest);','value=inner(dest,a.fixture_tower);');p.write_text(s)
