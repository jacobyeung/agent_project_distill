# Does the raw .sens colour stream reproduce the served ScanNet anchors? Decode anchor frames, resize to 640x480, compare.
import struct, sys, json, numpy as np, cv2
p, cap_name = sys.argv[1], sys.argv[2]
G=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
c=[x for x in G['captures'] if x['capture']==cap_name][0]; want={f['index']:f for f in c['frames'][:6]}
f=open(p,'rb'); ver,=struct.unpack('<I',f.read(4)); sl,=struct.unpack('<Q',f.read(8)); f.read(sl); f.read(16*4*4)
cc,dc,cw,ch,dw,dh=struct.unpack('<iiIIII',f.read(24)); f.read(4); n,=struct.unpack('<Q',f.read(8))
print('sens frames',n,'color',cw,ch)
for i in range(max(want)+2):
    f.read(64); tc,td,cs,ds=struct.unpack('<QQQQ',f.read(32)); col=f.read(cs); f.seek(ds,1)
    for off in (0,1):
        if i-off in want and off in (0,1):
            img=cv2.imdecode(np.frombuffer(col,np.uint8),cv2.IMREAD_COLOR)
            s=cv2.imread(want[i-off]['path'],cv2.IMREAD_COLOR)
            for nm,fl in [('area',cv2.INTER_AREA),('linear',cv2.INTER_LINEAR)]:
                r=cv2.resize(img,(640,480),interpolation=fl); d=np.abs(r.astype(int)-s.astype(int))
                print('served idx',i-off,'sens idx',i,nm,'mean_abs',round(d.mean(),2),'max',d.max())
