import json,sys
from tests.test_r2_build9_recovery import *
from student_pilot.carrier_c1_routing import alias_of
rates=load(LANE/'work/kit07ca49df_meta/m/k/frame_rates.json')['by_scene']
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    alias=p.get('alias') or (raw['dataset']+'/'+raw['scene'] if raw.get('dataset') else alias_of(raw['canonical']))
    fps=si.get('fps') or p.get('fps_source',{}).get('value') or rates.get(alias,24.)
    frames={raw['qid']:dict(fps=fps,total_num_frames=indices[-1]+1,frames=[dict(path='/unavailable-rgb/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
    return normalize(raw,frames)
if __name__=='__main__':
    raw=json.loads(open(sys.argv[1]).readline());row=norm(raw)
    for e in row['events']: print(json.dumps(e)[:400])
    print(repr(row['target']));print(row['tool_output_spans']);print(row['answer'])
