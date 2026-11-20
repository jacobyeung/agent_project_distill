from common import *
import runpy
a=L/'attic/build24m4m/package_attempt';a.mkdir(parents=True)
v=J.load(L/'out/DELIVERY_24M4M.json')
p=L/v['package'];assert p.name=='tree_rebuild_b24m4l_a1e1ad83.tar'
failure=dict(issue='Package writer retained the prior build filename literal; archive preserved and writer corrected.',output=(D/'package.log').read_text(),archive=str(p.relative_to(L)),sha256=J.sha(p))
for p in (p,p.with_suffix('.tar.sha256'),L/'out/DELIVERY_24M4M.json',D/'PACKAGE_MANIFEST.json',D/'PACKAGE_CHECK.json',D/'STORAGE_FINAL.json',D/'package.log',D/'package_m.py'):
 p.rename(a/p.name)
v=J.load(D/'FAILURES.json');v['package_filename_correction']=failure;replace(D/'FAILURES.json',json.dumps(v,sort_keys=True,indent=2)+'\n')
runpy.run_path(str(D/'prepare_package_m.py'),run_name='__main__')
assert "name='tree_rebuild_b24m4m_'" in (D/'package_m.py').read_text()
print('Preserved first package and corrected the final package filename')
