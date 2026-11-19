import sys,json
sys.argv=['x'];sys.path.insert(0,'.')
import score_r5 as S
br,room_items,manifest,_=S.load(S.BASE/'b2/work/ret',S.BASE/'b2',0,544,'null_argmax')
b,_,_,_=S.load(S.O.parent/'out3/B5/ret',S.O/'B',0,200,'candidates_argmax')
keys=sorted(room_items)
r=S.compare(b,br,room_items,keys,'172456/read 0 null_argmax')
print(json.dumps(dict(n=len(keys),mra200=100*r['current']['score'],mra544=100*r['baseline']['score'],paired=r['paired'],calls200=r['current']['call_items'],calls544=r['baseline']['call_items'],capped544=r['baseline']['capped'],capped200=r['current']['capped'])))
