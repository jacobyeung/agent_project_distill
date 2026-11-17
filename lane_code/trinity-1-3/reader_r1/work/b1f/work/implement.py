from pathlib import Path
O=Path.cwd()/'out';P=O/'src'
def edit(n,a,b):
 p=P/n;s=p.read_text();assert a in s,(n,a);p.write_text(s.replace(a,b))
edit('b/e2e_reader/real.py','artifact components. Nothing is read from a cache.','artifact components. An opt-in process-local memo reuses only frozen perception values.')
edit('b/e2e_reader/real.py',"def __init__(self, artifact, device, dtype='bf16', depth_chunk_size=8):","def __init__(self, artifact, device, dtype='bf16', depth_chunk_size=8, memo=None):\n        self.memo = memo")
edit('b/e2e_reader/real.py','    def __call__(self, frames):\n        from student_pilot', '''    def __call__(self, frames):
        if self.memo is None:
            return self._fresh(frames)
        from .perception_memo import weight_identity, frame_indices
        identity = weight_identity(self.artifact, 'g3t', dict(device=str(self.device), dtype=self.dtype,
                                   depth_chunk_size=self.chunk, dense_frames=len(frames['native_frames'])))
        return self.memo.call('g3t', identity, frames['native_frames'], frame_indices(frames),
                              lambda: self._fresh(frames))

    def _fresh(self, frames):
        from student_pilot''')
edit('b/e2e_reader/real.py',"serve_room=False, stage1_select_rule='null_argmax'):","serve_room=False, stage1_select_rule='null_argmax', perception_memo='off', perception_memo_max_bytes=None, perception_memo_verify_reads=None):")
edit('b/e2e_reader/real.py',"    socket = stage1_factory(sam3_tower, selector_head, anchor_frames, rule=stage1_select_rule) if sam3_tower is not None else None",'''    from .perception_memo import process_memo, DEFAULT_BYTES
    memo = process_memo(dict(perception_memo=perception_memo,
                            perception_memo_max_bytes=DEFAULT_BYTES if perception_memo_max_bytes is None else perception_memo_max_bytes,
                            perception_memo_verify_reads=perception_memo_verify_reads))
    socket = stage1_factory(sam3_tower, selector_head, anchor_frames, rule=stage1_select_rule,
                            memo=memo, artifact=artifact) if sam3_tower is not None else None''')
edit('b/e2e_reader/real.py','    return Perception(TowerG3T(artifact, device), own_gravity, scale, socket, serve_room)', '''    value = Perception(TowerG3T(artifact, device, memo=memo), own_gravity, scale, socket, serve_room)
    if memo is not None:
        value.memo = memo
    return value''')
edit('b/e2e_reader/real.py',"    timings, entries = {}, dict(prefill=0, steps=0)","    memo = getattr(perception, 'memo', None)\n    if memo is not None:\n        memo.begin_read()\n    timings, entries = {}, dict(prefill=0, steps=0)")
edit('b/e2e_reader/real.py','    return dict(tokens=list(hook.ids)', '    result = dict(tokens=list(hook.ids)')
p=P/'b/e2e_reader/real.py';s=p.read_text();s += "    if memo is not None:\n        result['perception_memo'] = memo.report()\n    return result\n";p.write_text(s)
edit('b/e2e_reader/stage1.py',"def stage1_factory(sam3_tower, selector_head, anchor_frames_of, rule='null_argmax'):","def stage1_factory(sam3_tower, selector_head, anchor_frames_of, rule='null_argmax', *, memo=None, artifact=None):")
edit('b/e2e_reader/stage1.py',"                cache['features'] = sam3_tower.encode(anchor_frames_of(frames))",'''                if memo is None:
                    cache['features'] = sam3_tower.encode(anchor_frames_of(frames))
                else:
                    from .perception_memo import sam_encode
                    cache['features'] = sam_encode(memo, artifact, sam3_tower, anchor_frames_of(frames), frames)''')
edit('b/e2e_reader/parity.py',"                                             stage1_select_rule=settings.get('stage1_select_rule','null_argmax'),", "                                             stage1_select_rule=settings.get('stage1_select_rule','null_argmax'),\n                                             perception_memo=settings.get('perception_memo','off'),\n                                             perception_memo_max_bytes=settings.get('perception_memo_max_bytes'),\n                                             perception_memo_verify_reads=settings.get('perception_memo_verify_reads'),")
edit('h1eval/perception.py',"selector_head=selector_head,stage1_select_rule=stage1_select_rule)","selector_head=selector_head,stage1_select_rule=stage1_select_rule,\n                               **{k:v for k,v in kw.items() if k.startswith('perception_memo')})")
# Own-arm memo shares frozen SAM only. Each real generation begins its own read.
edit('h1eval/h10/perception_own.py',"    return BoundOwnPerception(socket, mode=mode, donor=donor, gt=gt)","    from e2e_reader.perception_memo import process_memo\n    value = BoundOwnPerception(socket, mode=mode, donor=donor, gt=gt)\n    value.memo = process_memo(settings or {})\n    return value")
edit('h1eval/h10/perception_own.py',"                                         rule=self.settings.get('stage1_select_rule', 'null_argmax'))", "                                         rule=self.settings.get('stage1_select_rule', 'null_argmax'),\n                                         memo=__import__('e2e_reader.perception_memo', fromlist=['process_memo']).process_memo(self.settings),\n                                         artifact=self.artifact)")
edit('orchard_h10/prepare.py',"        save_own_depth=config.get('save_own_depth',False))", "        save_own_depth=config.get('save_own_depth',False),\n        perception_memo=config.get('perception_memo','off'),\n        perception_memo_max_bytes=config.get('perception_memo_max_bytes',16*1024**3),\n        perception_memo_verify_reads=config.get('perception_memo_verify_reads'))")
edit('h1eval/h10/launch.py',"'artifact_manifest_sha256','stage1_select_rule'):","'artifact_manifest_sha256','stage1_select_rule','perception_memo',\n                'perception_memo_max_bytes','perception_memo_verify_reads'):")
edit('h1eval/h10/launch.py',"        settings = settings_for(getattr(args, 'settings', DEFAULT_SETTINGS), manifest['name'])", "        settings = settings_for(getattr(args, 'settings', DEFAULT_SETTINGS), manifest['name'])\n        from e2e_reader.perception_memo import settings as memo_settings\n        memo_settings(settings, required=True)\n        if settings['stage1_select_rule'] not in ('null_argmax','candidates_argmax'):\n            raise ValueError('unknown_stage1_select_rule')")
edit('h1eval/h10/launch.py',"                 save_own_depth=(settings or {}).get('save_own_depth', False))", "                 save_own_depth=(settings or {}).get('save_own_depth', False),\n                 **__import__('e2e_reader.perception_memo', fromlist=['settings']).settings(settings or {}))")
edit('orchard_h10/runner.py',"    identity_path=out/'metadata/IDENTITY.json'", "    from e2e_reader.perception_memo import settings as memo_settings\n    actual=json.loads(Path(config['settings']).read_text()) if config.get('settings') else config\n    identity.update(memo_settings(actual))\n    identity_path=out/'metadata/IDENTITY.json'")
