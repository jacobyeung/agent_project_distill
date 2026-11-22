# Decode a VSI mp4 with k6 wd.py's exact rule (cv2.VideoCapture grab, mode same, INTER_AREA to 640x480, PNG level 3)
# and compare every served anchor (FRAMES_GTC.json) by file sha256 and by pixels. Also report fps, frame count, dims.
import json, sys, hashlib
import numpy as np, cv2
cv2.setNumThreads(1)
mp4, cap_name = sys.argv[1], sys.argv[2]
G=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
c=[x for x in G['captures'] if x['capture']==cap_name][0]
want={f['index']:f for f in c['frames']}
cap=cv2.VideoCapture(mp4)
fps=cap.get(cv2.CAP_PROP_FPS); meta_n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
j=0; sha_eq=px1=0; worst=0; dims=None
while True:
    if not cap.grab(): break
    if j in want:
        ok,img=cap.retrieve(); dims=(img.shape[1],img.shape[0])
        if dims!=(640,480): img=cv2.resize(img,(640,480),interpolation=cv2.INTER_AREA)
        ok,enc=cv2.imencode('.png',img,[cv2.IMWRITE_PNG_COMPRESSION,3])
        f=want[j]; sha_eq+=hashlib.sha256(enc.tobytes()).hexdigest()==f['sha256']
        s=cv2.imread(f['path'],cv2.IMREAD_COLOR); d=int(np.abs(s.astype(int)-img.astype(int)).max()); worst=max(worst,d); px1+=d<=1
    j+=1
print(json.dumps(dict(capture=cap_name,cv2=cv2.__version__,fps=fps,meta_n=meta_n,decoded=j,src_wh=dims,anchors=len(want),sha256_equal=sha_eq,pixels_within_1=px1,max_abs=worst)))
