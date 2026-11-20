import numpy as np,json,hashlib,tarfile,io,os,sys
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
g={'captures':{'ds/a':{'capture_sha256':'c'*64,'anchor_indices':[0],'fov_hw_rad':(np.full((32,2),1.1)).tolist()}}}
json.dump(g,open('fg.json','w'))
def npz(**a):
 b=io.BytesIO();np.savez(b,**a);return b.getvalue()
def npzc(**a):
 b=io.BytesIO();np.savez_compressed(b,**a);return b.getvalue()
rng=np.random.default_rng(0)
caps={n:{'canonical':n,'anchor_indices':[0]} for n in ('ds/a','ds/b')}
m=json.dumps({'captures':list(caps.values())}).encode()
ot=tarfile.open('ov.tar','w');i=tarfile.TarInfo('sj/m.json');i.size=len(m);ot.addfile(i,io.BytesIO(m));ot.close()
def mk(path,fov):
 t=tarfile.open(path,'w:gz')
 def add(n,raw):
  i=tarfile.TarInfo(n);i.size=len(raw);t.addfile(i,io.BytesIO(raw))
 add('COMPLETE.json',b'{}');add('native/probe/TOKENS.json',b'{}')
 for name in ('ds/a','ds/b'):
  k=digest(name)[:16];d=(rng.random((32,51,51))+1).astype(np.float32).astype(np.float64) if name=='ds/a' else np.full((32,51,51),2.)
  d=np.full((32,51,51),2.)+ (0 if name=='ds/b' else 1)
  own=npz(depth=d,gravity=np.array([0.,-1,0]));add(f'native/probe/{k}/own.npz',own)
  add(f'native/probe/{k}/PHASE_COMPLETE.json',json.dumps({'capture_sha256':digest(caps[name]),'checkpoint':{'sha256':'x'}}).encode())
  if fov:
   arr=dict(depth_V1=d*1.01,fov_B=np.full((32,2),1.0,np.float32),fov_V1=np.full((32,2),0.9,np.float32))
   if name=='ds/a':arr.update(depth_V2=d*0.99,fov_V2=np.full((32,2),1.1,np.float32))
   f=npzc(**arr);add(f'native/probe/{k}/fov.npz',f)
   add(f'native/probe/{k}/FOV_RECEIPT.json',json.dumps({'files':{'fov.npz':hashlib.sha256(f).hexdigest()},'served_depth_sha256':hashlib.sha256(np.ascontiguousarray(d).tobytes()).hexdigest(),'capture_sha256':digest(caps[name]),'checks':{'second_pass_pose_fov_bit_identical':True,'second_pass_pose_fov_max_abs':0.0},'keys':sorted(arr),'canonical':name,'missing':{},'seconds':{}}).encode())
 t.close()
mk('old.tgz',False);mk('new.tgz',True)
