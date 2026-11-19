import os
root='/project/community/jjyeung/okh7/ae71c903';total=0
for base,dirs,files in os.walk(root,followlinks=False):
 for name in files:
  p=os.path.join(base,name)
  if os.path.islink(p):raise ValueError('Unexpected pool symlink')
  total+=os.stat(p).st_size
  if total>75000000:raise ValueError('Return pool exceeds 75 MB')
print(total)
