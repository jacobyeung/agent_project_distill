from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1'
changed=[]
def edit(name,old,new):
 p=T/name;text=p.read_text();assert old in text,(name,old)
 base=B/'base'/name;base.parent.mkdir(parents=True,exist_ok=True)
 if not base.exists():base.write_text(text)
 p.write_text(text.replace(old,new));changed.append(name)
(T/'student_pilot/r1_coverage.py').write_text((B/'candidate/r1_coverage.py').read_text())
edit('student_pilot/r1_population.py',"        for kind, source in self.sources.items():\n            if kind not in SLICE_CELLS:","        from .r1_coverage import PINS, source_names\n        source_names(self.sources)\n        for kind, source in self.sources.items():\n            if kind not in (*SLICE_CELLS,*PINS):")
edit('student_pilot/r1_population.py',"        return kind\n\n\ndef produce", "        return 'coverage' if kind in ('coverage_units','coverage_distance') else kind\n\n\ndef produce")
edit('student_pilot/r1_routing.py',"    if set(sources) != set(SLICE_CELLS):", "    from .r1_coverage import source_names\n    if set(sources) != set(source_names(sources)):")
edit('student_pilot/r1_routing.py',"    sources = {k:specs[k]['source'] for k in SLICE_CELLS}","    from .r1_coverage import source_names, validate_binding\n    validate_binding(cfg)\n    names = source_names(specs)\n    sources = {k:specs[k]['source'] for k in names}")
edit('student_pilot/r1_routing.py',"        for kind in SLICE_CELLS:","        for kind in names:")
edit('launch_r1/build.py',"    cfg['r1_training']['row_slice_inputs']={k:row_sources[k]['source'] for k in SLICE_CELLS}","    from student_pilot.r1_coverage import source_names\n    cfg['r1_training']['row_slice_inputs']={k:row_sources[k]['source'] for k in source_names(row_sources)}")
edit('student_pilot/r1_training.py',"    value = cfg['r1_training']\n    if value.get('schema')", "    value = cfg['r1_training']\n    from .r1_coverage import validate_binding\n    validate_binding(cfg)\n    if value.get('schema')")
edit('student_pilot/carrier_c1_run.py',"        self.r1_training = receipt.get('r1_training')", "        self.r1_training = receipt.get('r1_training')\n        from .r1_coverage import validate_binding\n        self.wording_exclusion = validate_binding(receipt)")
edit('student_pilot/carrier_c1_run.py',"        value = json.loads(row[0])\n        from .row_text_audit", "        value = json.loads(row[0])\n        if getattr(self, 'wording_exclusion', None) is not None:\n            self.wording_exclusion.check(value)\n        from .row_text_audit")
edit('student_pilot/r1_rooms.py',"    for kind in ('recovery','units','absolute_distance'):","    from .r1_coverage import source_names\n    for kind in source_names(sources):")
edit('student_pilot/r1_rooms.py',"        if (pin.get('sha256') != V7_K1_LIST or hashes.count(V7_K1_LIST) != 1", "        from .r1_coverage import verify_union\n        union = verify_union(value, cfg['remove_files'], V7_K1_LIST, N_LIST)\n        if ((not union and pin.get('sha256') != V7_K1_LIST) or hashes.count(V7_K1_LIST) != 1")
edit('student_pilot/r1_rooms.py',"    reports, hits = {}, []", "    from .r1_coverage import validate_binding\n    wording = validate_binding(cfg)\n    reports, hits = {}, []")
edit('student_pilot/r1_rooms.py',"                row = json.loads(line)\n                status", "                row = json.loads(line)\n                if wording is not None:wording.check(row)\n                status")
edit('student_pilot/r1_rooms.py',"scene=row['dataset']+'/'+row['scene'],canonical=canonical", "scene=row.get('dataset','')+'/'+row.get('scene',''),canonical=canonical")
edit('student_pilot/r1_rooms.py',"            row = json.loads(raw); status, canonical, how = rooms.status(row)", "            row = json.loads(raw)\n            if wording is not None:wording.check(row)\n            status, canonical, how = rooms.status(row)")
edit('student_pilot/r1_rooms.py',"certifies='All three pinned slices", "certifies='All bound pinned slices")
(B/'V2H_CHANGES.json').write_text(json.dumps(sorted(set(changed)),indent=2))
print(json.dumps(sorted(set(changed))))
