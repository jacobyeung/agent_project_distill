import sys,json,numpy as np; sys.path.insert(0,'code'); import r0lib
for sc in sys.argv[1:]:
  s='data_cache/scannetpp/'+sc
  P=json.load(open(s+'/iphone/pose_intrinsic_imu.json')); cm=r0lib.colmap_c2w(s); n=len(P)
  com=[i for i in sorted(cm) if i<n]
  et=[];er=[]
  for i in com:
    A=np.asarray(P['frame_%06d'%i]['aligned_pose']);C=cm[i]
    et.append(np.linalg.norm(A[:3,3]-C[:3,3])); R=A[:3,:3].T@C[:3,:3]; er.append(np.degrees(np.arccos(np.clip((np.trace(R)-1)/2,-1,1))))
  et=np.array(et);er=np.array(er)
  A=np.array([np.asarray(P['frame_%06d'%i]['aligned_pose'])[:3,3] for i in range(n)])
  print(sc,'frames',n,'colmap',len(cm),'common',len(com),'trans p50/p90/max',np.round(np.percentile(et,[50,90,100]),3),'rot p50/p90',np.round(np.percentile(er,[50,90]),2),'aligned t span',np.round(A.min(0),1),np.round(A.max(0),1))
