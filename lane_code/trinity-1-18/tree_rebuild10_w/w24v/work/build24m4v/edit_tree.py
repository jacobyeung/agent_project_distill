from pathlib import Path
import json, difflib
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1c';D=L/'work/build24m4v'
changes={
'student_pilot/extent_receipt.py':[
('def __init__(self, pin):', '''def __init__(self, pin, pool_sources=None):
        if pool_sources is not None and (not isinstance(pool_sources, list)
                or any(not isinstance(name, str) or not name for name in pool_sources)):
            raise ValueError('EXTENT_POOL_SOURCES_INVALID')
        self.pool_sources = frozenset(pool_sources or ())
        self.exempted = 0'''),
('    def check(self, row, stream):\n', '''    def exempt(self, row, stream):
        # The native pool builder writes this field from its pinned selection;
        # callers authenticate database bytes or sealed row membership first.
        source = row.get('s1_source')
        return bool(self.pool_sources and stream == 'routing'
                    and not str(row.get('qid', '')).startswith('a0_')
                    and not row.get('r1_source') and isinstance(source, dict)
                    and source.get('name') in self.pool_sources)

    def check(self, row, stream):
        if self.exempt(row, stream):
            self.exempted += 1
            return
''')],
'student_pilot/carrier_c1_run.py':[
("'r2_sampling', 'extent_receipt',", "'r2_sampling', 'extent_receipt', 'extent_pool_sources',"),
("self.extents = Extents(receipt.get('extent_receipt'))", "self.extents = Extents(receipt.get('extent_receipt'), receipt.get('extent_pool_sources'))")],
'student_pilot/r1_routing.py':[
("extent_receipt=cfg.get('extent_receipt'),\n", "extent_receipt=cfg.get('extent_receipt'),\n                       extent_pool_sources=cfg.get('extent_pool_sources'),\n"),
("per_source=dict(counts), refused=dict(refused), intake_evidence=evidence)","per_source=dict(counts), refused=dict(refused), intake_evidence=evidence,\n        extent_exempted=reader.extents.exempted)")],
'student_pilot/r2_intake.py':[
("extents = Extents(manifest.get('extent_receipt'))", "extents = Extents(manifest.get('extent_receipt'), manifest.get('extent_pool_sources'))"),
("slice_limit=limit, population_count=manifest['count'])", "slice_limit=limit, population_count=manifest['count'], extent_exempted=extents.exempted)")]
}
diff=[]
for name,replacements in changes.items():
 p=T/name;old=p.read_text();new=old
 for a,b in replacements:
  assert new.count(a)==1,(name,a,new.count(a));new=new.replace(a,b)
 q=L/'attic/build24m4v/work/tree_r1c'/name;q.parent.mkdir(parents=True,exist_ok=True);p.rename(q);p.write_text(new);p.chmod(q.stat().st_mode&511)
 diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(L/'out/TREE_CHANGE_24M4V.patch').write_text(''.join(diff))
print('Tree patch:',list(changes))
