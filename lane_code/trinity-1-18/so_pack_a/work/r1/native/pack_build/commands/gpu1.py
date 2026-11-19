import os
root='/project/community/jjyeung/okh7/ae71c903';total=0
if not os.path.isdir(root) or os.path.islink(root):raise ValueError('Return pool is absent or a symlink')
def fail(error):raise error
for base,dirs,files in os.walk(root,followlinks=False,onerror=fail):
 for name in dirs:
  if os.path.islink(os.path.join(base,name)):raise ValueError('Unexpected pool symlink')
 for name in files:
  p=os.path.join(base,name)
  if os.path.islink(p):raise ValueError('Unexpected pool symlink')
  total+=os.stat(p).st_size
  if total>75000000:raise ValueError('Return pool exceeds 75 MB')
print(total)
