from common import *
p=L/'work/tree_r1_base'
assert not p.exists()
p.symlink_to('tree_r1',target_is_directory=True)
for name in ('tree_tests','TREE_TESTS.json'):
 p=D/name
 if p.exists():
  q=L/'attic/build24m4o/initial_tests'/name;q.parent.mkdir(parents=True,exist_ok=True);p.rename(q)
print('Untouched tree C available to native comparison fixture')
