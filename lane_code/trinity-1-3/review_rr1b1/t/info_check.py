import sys, json
sys.argv=['x']
sys.path.insert(0,'.')
import replay_patched as RP
from e2e_reader import stage1 as S1, grounding as GR
from e2e_reader.servers import ReadServers
J=[j for j in RP.jobs() if j[1]=='hybrid'][:12]
for item_id, geo_kind, rule, names, gap_call, pose9, gravity in J:
    try:
        hw=tuple(RP.MAN[RP.ITEMS[item_id]['native']]['hw'])
        geom=RP.hybrid_geometry(item_id,pose9,gravity,hw); _,detect=RP.detections(RP.ITEMS[item_id]['native'])
        st=S1.StageOne(detect,RP.HEAD,geom,rule=rule); sock=GR.StageOneSocket(st.propose,st.select,(240,320),32)
        sv=ReadServers(geom,GR.ground_session(geom,sock))
        for n in names:
            t,i=sv.session_call('<ground obj="%s" mode="box">'%n)
            s=i.get('stage1',{}); print(rule,n,repr(t[:40]),'stage1 keys',len(s),'chosen',s.get('chosen_index'),'null_win',s.get('null_would_win'),'cands',s.get('linked_candidates'))
        if gap_call:
            t,i=sv.session_call(gap_call); print(' gap',repr(t[:50]),json.dumps(i.get('stage1')))
    except Exception as e: print('ERR',item_id,repr(e)[:100])
