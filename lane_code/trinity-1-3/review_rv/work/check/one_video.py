import json,sys
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/review_rv/work/fresh')
for d in ('reader','reader/evaluator','cohort'):sys.path.insert(0,str(K/d))
import frame_plan, media
src='/data2/jjyeung/agent_project_data/external_benchmarks/revsi/32_frame/41069021.mp4'
v=frame_plan.one(src)
idx=json.loads((K/'inputs/revsi_indices.json').read_text())['41069021']['32-frame']
t=frame_plan.source_timing(v,idx)
print('total',v['total_frames'],'fps',v['fps'],'packets==decode',v['packet_equals_decode'],'anchors==range32',v['anchor_indices']==list(range(32)))
print('model_fps',t['model_fps'],'model_total',t['model_total_frames'],'first ts',t['model_timestamps'][:4],'last',t['model_timestamps'][-1],'clip last ts',v['timestamps'][-1])
rows=json.loads((K/'inputs/revsi999_rows_t32.json').read_text());row=[r for r in rows if r['scene']=='41069021'][0]
task=dict(row,example_id=row['qid'],source_frame_indices=idx,revsi_tier=32,video_path=src,video_sha256=json.loads((K/'inputs/revsi999_videos_t32.json').read_text())['files']['41069021']['sha256'])
arr,audit=media.decode(task,'duplicate')
print('arrays',arr.shape,'meta',{k:audit['metadata'][k] for k in ('fps','total_num_frames','height','width')},'frames_indices==model_dup',audit['metadata']['frames_indices']==t['model_duplicate_indices'],'fps eq',audit['metadata']['fps']==t['model_fps'])
