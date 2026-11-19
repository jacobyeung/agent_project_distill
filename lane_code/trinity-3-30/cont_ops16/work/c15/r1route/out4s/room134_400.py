import sys,json
sys.argv=['x'];sys.path.insert(0,'.')
import score_r5_400 as S
br,room_items,manifest,_=S.load(S.BASE/'b2/work/ret',S.BASE/'b2',0,544,'null_argmax')
b,_,_,_=S.load(S.O.parent/'out3/B10/ret',S.O/'B',0,400,'candidates_argmax')
b2,_,_,_=S.load(S.O.parent/'out3/B5/ret',S.O.parent/'out3s/B',0,200,'candidates_argmax') if False else (None,0,0,0)
keys=sorted(room_items)
r=S.compare(b,br,room_items,keys,'172456/read 0 null_argmax')
out=dict(n=len(keys),mra400=100*r['current']['score'],mra544=100*r['baseline']['score'],paired=r['paired'],calls400=r['current']['call_items'],calls544=r['baseline']['call_items'],capped544=r['baseline']['capped'],capped400=r['current']['capped'],finishes400=r['current']['finishes'])
for name,ks in manifest['sets'].items():
    rr=S.compare(b,br,room_items,ks,'');out[name]=dict(n=len(ks),mra400=100*rr['current']['score'],mra544=100*rr['baseline']['score'],calls400=rr['current']['call_items'],capped400=rr['current']['capped'],paired=rr['paired'])
print(json.dumps(out))
