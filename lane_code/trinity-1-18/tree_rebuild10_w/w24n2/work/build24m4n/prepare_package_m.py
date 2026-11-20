from common import *
s=(D/'package_l.py').read_text()
s=s.replace('tree_rebuild_b24m4l_', 'tree_rebuild_b24m4m_')
s=s.replace("source=W/'w24k/out/tree_rebuild_b24m4k_2cd5a46f.tar'", "source=W/'w24l/out/tree_rebuild_b24m4l_b601a94b.tar'")
s=s.replace('9e4d59ef5a75de02fb2ad9cc21616f833b96e677a9c57c0be7ad566cfa4ef918','80f326eece4426706ffe0078073ed01381ad689ba8c76e835271b0064cff9b85')
s=s.replace("tree_patch='out/TREE_CHANGE_24M4K.patch',tree_patch_applied=True,production_executed=False,", "tree_patch='work/build24m4n/TEST_HOST24J_FIX.patch',tree_patch_applied=True,production_executed=False,")
(D/'package_m.py').write_text(s)
print('Full-package writer prepared with input preservation and member verification')
