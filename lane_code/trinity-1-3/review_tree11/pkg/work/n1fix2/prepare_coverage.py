from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
text=(B/'coverage.py').read_text()
text=text.replace('import sys\n','import sys\nimport tarfile\n')
text=text.replace("hits={};accepted=[];excluded=[]", """baseline=tarfile.open(L/'out/tree_rebuild_b9_eca323a0.tar')
old_files=json.loads((B/'INHERITED_TREE_SEAL.json').read_text())['files']
def old_text(name):
    if name not in old_files:return []
    raw=baseline.extractfile('work/tree_r1/'+name).read()
    assert hashlib.sha256(raw).hexdigest()==old_files[name]
    return raw.decode().splitlines()
hits={};accepted=[];excluded=[]""")
text=text.replace("tree=L/'work/tree_r1';base=L/'work/base/tree_b01ce449'", "tree=L/'work/tree_r1';base=L/'work/base/tree_b01ce449';B=L/'work/n1fix2'")
text=text.replace("prior=(base/name).read_text().splitlines() if (base/name).is_file() else []", "prior=old_text(name)")
text=text.replace("if not reached:\n            if name", """if not reached:
            if name=='student_pilot/r1_loader.py' and fn=='production_audit':
                category='frame-host';reason='Full scene-admitted stores and indices are missing; local full-store execution is forbidden.'
            elif name=='launch_r1/entry.py' and fn in ('frame_host','admit'):
                category='frame-host';reason='Missing full source closure, processor values, evidence registry, native preparation, host receipt and independent review.'
            elif name""")
text=text.replace('relative to untouched base','relative to the authenticated Build-9 package')
text=text.replace('CHANGED_COVERAGE.json','N1_CHANGED_COVERAGE.json').replace('GAPS.json','N1_GAPS.json')
(B/'coverage_n1.py').write_text(text)
