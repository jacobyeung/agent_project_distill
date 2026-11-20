from common import *
p=W/'work/rcj24m4j4/x.py'
assert J.sha(p)=='16be8a2186f03fdb02c1ec1f25140c2e00c1db345f6d7eb8eda0734874cb1c4e'
replace(L/'out/rcj/x.py',p.read_bytes())
replace(L/'out/rcj/rcj.sh',(p.parent/'rcj.sh').read_bytes())
(L/'out/rcj/rcj.sh').chmod(0o755)
p=W/'work/sel24/orchard/rdiff.py';h=J.sha(p);assert h.startswith('bc2db774'),h
J.write(D/'RDIFF_PIN.json',dict(sha256=h,path='/project/community/jjyeung/okh7/x_22c714e1/rdiff.py'))
(D/'rdiff.py').write_bytes(p.read_bytes())
print('verified launcher',J.sha(L/'out/rcj/x.py'),'rdiff',h)
