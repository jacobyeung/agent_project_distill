from pathlib import Path
R=Path(__file__).resolve().parents[1]/'work/new'
def edit(name,old,new):
 p=R/name;s=p.read_text();assert s.count(old)==1,(name,s.count(old),old[:70]);p.write_text(s.replace(old,new))
edit('student_pilot/carrier_c1.py', '        self.model.visual.eval()\n        if self.geometry_online is not None:', '''        self.model.visual.eval()
        donor = getattr(self.auxiliary_heads, 'scale_donor', None)
        if donor is not None:
            donor.train(False)
        if self.geometry_online is not None:''')
edit('student_pilot/carrier_c1.py', "    if _gf1 and 'gf1'", """    donor = getattr(model.auxiliary_heads, 'scale_donor', None)
    if donor is not None:
        donor.assert_frozen()
    if _gf1 and 'gf1'""")
edit('student_pilot/carrier_c1_run.py', "def validate(cfg):\n", """def validate(cfg):
    if 'scale_donor' in cfg:
        from .scale_donor import validate as validate_donor
        validate_donor(cfg['scale_donor'])
        if cfg.get('depth_enabled', True) is not True or cfg.get('frame_count', 32) != 32:
            raise ValueError('Scale donor requires depth enabled and 32 frames')
""")
edit('student_pilot/carrier_c1_run.py', "'depth_fov_source', 'depth_init', 'exclusions'", "'depth_fov_source', 'depth_init', 'scale_donor', 'exclusions'")
edit('student_pilot/carrier_c1_run.py', "            or receipt.get('depth_init') != cfg.get('depth_init')):", "            or receipt.get('depth_init') != cfg.get('depth_init')\n            or receipt.get('scale_donor') != cfg.get('scale_donor')):")
edit('student_pilot/carrier_c1_run.py', "    if not evaluation:\n        from .trained_groups import capture", """    if 'scale_donor' in receipt:
        from .scale_donor import attach
        attach(model, receipt['scale_donor'])
    if not evaluation:
        from .trained_groups import capture""")
edit('student_pilot/carrier_c1_run.py', "        pin=full_ft._write_payload(directory/'heads.pt',heads)", """        from .scale_donor import export_metadata
        donor_metadata = export_metadata(model, heads)
        if donor_metadata is not None:
            heads['_scale_donor'] = donor_metadata
        pin=full_ft._write_payload(directory/'heads.pt',heads)""")
edit('student_pilot/carrier_c1_run.py', "            config_sha256=identity(cfg),base_identity=cfg['base_identity'],", "            **({'scale_donor': donor_metadata} if donor_metadata is not None else {}),\n            config_sha256=identity(cfg),base_identity=cfg['base_identity'],")
edit('student_pilot/carrier_c1_run.py', "    state=torch.load(pinned(artifact['heads']),map_location='cpu',weights_only=True)\n    readout_keys", """    state=torch.load(pinned(artifact['heads']),map_location='cpu',weights_only=True)
    from .scale_donor import verify_export
    donor_metadata = state.pop('_scale_donor', None)
    if donor_metadata != artifact.get('scale_donor'):
        raise ValueError('Scale donor artifact and heads pins differ')
    verify_export(model, state, donor_metadata)
    readout_keys""")
edit('student_pilot/carrier_c1_decode.py', "            apply_tower(self, tower_state, batch)", "            apply_tower(self, tower_state, batch, scale_donor=getattr(model.auxiliary_heads, 'scale_donor', None))")
edit('student_pilot/tower_read.py', "def apply_tower(heads, state, batch):", "def apply_tower(heads, state, batch, *, scale_donor=None):")
edit('student_pilot/tower_read.py', "        own = heads.depth_head.query(heads.depth_map, uv).double().cpu().numpy().reshape(32, 51, 51)", """        own = (heads.depth_head.query(heads.depth_map, uv).double().cpu().numpy().reshape(32, 51, 51)
               if scale_donor is None else scale_donor(batch, state).double().cpu().numpy())""")
(R.parents[1]/'STATUS.md').write_text('The 939-file base matches seal 57a1f14d. The donor implementation now copies the checkpoint point-depth head, private frame queries and V1 FoV module, or uses explicit V2 tower FoV. It shares the frozen private visual copy by reference, pins its bytes, excludes donor parameters from optimization, and binds export verification. The tower estimator and own-arm readout remain unchanged. CPU verification is in progress.\n')
