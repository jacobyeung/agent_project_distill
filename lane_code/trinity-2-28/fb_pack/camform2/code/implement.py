from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];tree=ROOT/'work/new'
p=tree/'student_pilot/r1_coverage.py';s=p.read_text();needle="    if value['routing_slices'] != 'deferred_first_boundary':\n        raise ValueError('R1_ROUTING_SLICES_INVALID')\n";assert s.count(needle)==1;s=s.replace(needle,needle+"    if 'camera_trace_form' in value:\n        raise ValueError('R1_CAMERA_TRACE_FORM_REQUIRES_COMPOSITION')\n");p.write_text(s)
p=tree/'student_pilot/r1_training.py';s=p.read_text();needle="def validate(cfg):\n    value = cfg['r1_training']\n";assert s.count(needle)==1;s=s.replace(needle,needle+"    if 'camera_trace_form' in value:\n        from .r1_coverage import deferred\n        deferred(cfg)\n");p.write_text(s)
p=tree/'student_pilot/r1_camera_trace_form.py';s=p.read_text();s=s.replace("TYPES =", "POLICY_SHA256 = '169c439a1ac1bf11d66ee7b725277ef8ee07a706807324bed2696b9d99efaace'\n\nTYPES =");s=s.replace("        if load(pinned(pin)) != POLICY:", "        policy = load(pinned(pin))\n        if pin['sha256'] != POLICY_SHA256 or policy != POLICY:")
s=s.replace("        self.rules = dict.fromkeys(POLICY['rule_ids'], 0)", "        self.rules = dict.fromkeys(POLICY['rule_ids'], 0)\n        self.lines = dict.fromkeys(TYPES, 0)\n        self.rule_lines = dict.fromkeys(POLICY['rule_ids'], 0)")
s=s.replace("    def record(self, row, ids):\n", "    def record(self, row, ids):\n        \"\"\"Count an admitted source row and changed physical prose lines.\"\"\"\n")
s=s.replace("        for rule in ids:\n            self.rules[rule] += 1", """        for rule in set(ids):
            self.rules[rule] += 1
        if kind in TYPES and ids:
            for event in row['routing']['events']:
                if event['kind'] not in ('plan', 'canonical_text'):
                    continue
                before = event['text']
                after, event_ids = rewrite_text(before)
                for old, new in zip(before.splitlines(), after.splitlines(), strict=True):
                    if old == new:
                        continue
                    self.lines[kind] += 1
                    if 'CAM-ROT-WORDS-v1' in event_ids and ROT_OLD in old:
                        self.rule_lines['CAM-ROT-WORDS-v1'] += 1
                    if 'CAM-DIR-SYMBOL-v1' in event_ids and NEG.search(old):
                        self.rule_lines['CAM-DIR-SYMBOL-v1'] += 1""")
s=s.replace("                    rewritten_base_rows_by_rule=self.rules)", "                    rewritten_base_rows_by_rule=self.rules,\n                    changed_base_lines=sum(self.lines.values()),\n                    changed_base_lines_by_type=self.lines,\n                    changed_base_lines_by_rule=self.rule_lines)")
p.write_text(s)
p=tree/'student_pilot/r1_routing.py';s=p.read_text();s=s.replace("        camera_rules = []", "        camera_source = row\n        camera_rules = []");s=s.replace("camera_form.record(row, camera_rules)","camera_form.record(camera_source, camera_rules)");p.write_text(s)
p=tree/'tests/test_r1_camera_trace_form.py';s=p.read_text();s=s.replace("    def test_exact_rewrites_preserve_other_fields_and_offsets(self):", """    def policy_pin(self):
        source=Path(__file__).parents[1]/'configs/r1_camera_trace_form_v1.json'
        p=self.root/'policy.json';p.write_bytes(source.read_bytes());return file_pin(p)

    def declaration(self):
        from student_pilot.r1_coverage import ROUTING_FAMILIES
        return self.write('decl.json',dict(schema='r1-routing-slices-v1',bound=[],
            deferred={k:'unit fixture: omitted' for k in ROUTING_FAMILIES}))

    def test_exact_rewrites_preserve_other_fields_and_offsets(self):""")
s=s.replace("self.write('policy.json',POLICY)","self.policy_pin()")
s=s.replace("routing_slices='deferred_first_boundary',camera_trace_form=", "routing_slice_declaration=self.declaration(),camera_trace_form=")
p.write_text(s)
(ROOT/'STATUS.md').write_text('Stage 2: The overlay rejects camera_trace_form in deferred mode before config or pin work, authenticates the exact policy bytes, and records changed physical lines per type and rule alongside admitted row counts. Unit composition fixtures use declaration mode. Fail-before and pass-after regressions cover all three review findings.\n')
