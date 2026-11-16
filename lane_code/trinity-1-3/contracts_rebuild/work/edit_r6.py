from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[1]
for name in ('src','tests'):
    shutil.copytree(L/f'work/{name}_r5',L/f'work/{name}_r6')
for name in ('row_families','real_replay'):
    dst=L/f'work/{name}_r6';dst.mkdir()
    for p in (L/f'work/{name}_r5').glob('*.py'):
        (dst/p.name).write_text(p.read_text().replace('r5','r6').replace('R5','R6'))
(L/'work/test_artifacts_r6').mkdir()
for p in (L/'work/tests_r6').glob('*.py'):
    s=p.read_text().replace('test_artifacts_r5','test_artifacts_r6')
    # Existing baseline evidence stays read-only; strict comparison uses this round.
    if p.name=='test_confirmation_r5.py':s=s.replace('row_families_r5/heading_compare.py','row_families_r6/heading_compare.py')
    p.write_text(s)
D=L/'work/review_c5_inputs';D.mkdir()
for name in ('h2_frozen_basis.py','h1_live_ambient.py','h2_mixed.py','m1_binding.py','r5_probe.py','bare_gap.py'):
    p=Path('/scratch/jjyeung/orch_n30/review_c5/work/mytests')/name
    (D/name).write_text(p.read_text().replace('/scratch/jjyeung/orch_n30/review_c5/work/tests_r5',str(L/'work/tests_r6')))
S=L/'work/src_r6'
p=S/'student_pilot/carrier_c1_routing.py';s=p.read_text()
a=s.index('        from trace_format.contracts import new_contracts\n',s.index('class OwnGeometry:'))
b=s.index('\n    def camera(self, k):',a)
block=s[a:b].replace('self.to_l1 =','basis =').replace('basis = private_metric_basis','private = private_metric_basis').replace('if basis is not None:\n                    basis = basis.T','if private is not None:\n                    basis = private.T').replace('        self._poses = {}','        return basis')
s=s[:a]+'''        self._bases = {}
        self._poses = {}
        self.to_l1  # Preserve construction-time validation in the active context.

    @property
    def to_l1(self):
        from trace_format.contracts import new_contracts, heading_plane_min
        key = (new_contracts(), heading_plane_min())
        if key not in self._bases:
            self._bases[key] = self._basis()
        return self._bases[key]

    def _basis(self):
'''+block+s[b:]
s=s.replace('''        if k not in self._poses:
''','''        from trace_format.contracts import new_contracts, heading_plane_min
        key = (new_contracts(), heading_plane_min(), k)
        if key not in self._poses:
''').replace('self._poses[k]','self._poses[key]')
a=s.index("                if name != 'depth_at' and not recorded and")
b=s.index("                    lines = []",a)
s=s[:a]+"                if name == 'depth_at':\n"+s[b:]
p.write_text(s)
p=S/'student_pilot/live_trace313.py';s=p.read_text();a=s.index('        super().__init__(lifting');b=s.index('        self.owner=backend',a)
s=s[:a]+'''        self.contract_epoch = getattr(backend, 'contract_epoch', new_contracts())
        self.heading_plane_min = heading_plane_min(getattr(backend, 'heading_plane_min', heading_plane_min()))
        with contract_epoch(self.contract_epoch, heading_plane_min=self.heading_plane_min):
            super().__init__(lifting,backend.geometry,None,instances=lambda name:(),
                             program_version=program_version, multi_instance=program_version=='3.14',
                             geometry_mode=geometry_mode)
'''+s[b:];p.write_text(s)
p=S/'generator/derivgen_v7/derivgen/calculator.py';s=p.read_text().replace("        import sys\n        contracts = sys.modules.get('trace_format.contracts')", "        try:\n            from trace_format import contracts\n        except ImportError:\n            contracts = None") ;p.write_text(s)
p=S/'student_pilot/phrases.py';s=p.read_text().replace("entry.get('phrases', [])", "entry.get('phrases')")
s=s.replace('    import copy\n    cache = copy.deepcopy(cache)\n', '')
s=s.replace("    if len(keys) > 1:\n        import json", "    if len(keys) > 1:\n        cache = {**cache, 'frames': {k: dict(v) for k, v in cache.get('frames', {}).items()}}\n        import json")
p.write_text(s)
p=L/'work/row_families_r6/heading_compare.py';s=p.read_text();a=s.index('def row_texts_valid(')
s=s[:a]+'''def row_texts_valid(old,new):
    """Reject structural or scalar changes; allow only exact heading text substitutions."""
    if type(old) is not type(new):return False
    if isinstance(old,str):return old==new or heading_text(old,new)
    if isinstance(old,dict):
        return old.keys()==new.keys() and all(row_texts_valid(old[k],new[k]) for k in old)
    if isinstance(old,list):
        return len(old)==len(new) and all(row_texts_valid(a,b) for a,b in zip(old,new))
    return old==new
''';p.write_text(s)
# Comparison validates derived counters and private fields separately, before normalizing them for the strict walk.
p=L/'work/row_families_r6/compare.py';s=p.read_text().replace("    current_texts_valid = valid(b) and valid(n) and row_texts_valid(b['row'],n['row'])",'''    current_texts_valid = False
    if valid(b) and valid(n):
        checked = copy.deepcopy(n['row'])
        current_texts_valid = True
        for path, old, new in diffs(b['row'], n['row']):
            if isinstance(old, str) and isinstance(new, str):continue
            reason = mapping(family, variant, path, old, new)
            if reason is not None:
                parts = path.lstrip('/').split('/')
                dest = checked
                for part in parts[:-1]:dest = dest[int(part)] if isinstance(dest, list) else dest[part]
                leaf = int(parts[-1]) if isinstance(dest, list) else parts[-1]
                if leaf in dest if isinstance(dest, dict) else 0 <= leaf < len(dest):dest[leaf] = old
        current_texts_valid = row_texts_valid(b['row'], checked)''');p.write_text(s)
# New harnesses, with old baseline inputs intentionally retained.
for name in ('build_packet','run_tests','real_audit','regenerate','replay_close'):
    s=(L/f'work/{name}_r5.py').read_text().replace('r5','r6').replace('R5','R6')
    (L/f'work/{name}_r6.py').write_text(s)
