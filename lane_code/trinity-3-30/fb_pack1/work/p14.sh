F=/scratch/jjyeung/orch_n30/fb_pack; cd $F
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,hashlib
F='/scratch/jjyeung/orch_n30/fb_pack'
def sh(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
k=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/k/0.json'))
inv=json.load(open('/scratch/jjyeung/orch_n30/sb_fullinv/out/FULL_INVENTORY.json'))
fc=json.load(open('FRAME_COVERAGE.json')); cf=json.load(open('CAMERA_F14_CHECK.json'))
rec=dict(schema='fb-pack-frame-stage-v1', at_utc='2026-11-19T19:05Z',
 verdict='all 57,120 requested (dataset, scene, ordinal) frames resolve to PNGs already held on Orchard; 0 bytes to move',
 frame_map=dict(logical='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/frame_map.jsonl.gz', orchard='/project/community/jjyeung/okh7/x_ee227714/k/frame_map.jsonl.gz', trinity_copy=F+'/in/pk/frame_map.jsonl.gz', sha256=sh('in/pk/frame_map.jsonl.gz'), entries=290880),
 frame_plan=dict(logical='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/frame_plan.json.gz', orchard='/project/community/jjyeung/okh7/x_ee227714/k/frame_plan.json.gz', trinity_copy=F+'/in/pk/frame_plan.json.gz', sha256=sh('in/pk/frame_plan.json.gz')),
 k6tk_shards=inv['frame_host']['recorded_P_frame_archives'], k6tk_total_bytes=inv['frame_host']['recorded_P_archive_bytes'],
 k6tk_index='/project/community/jjyeung/cp4tk_fr/k6tk/INDEX.json (member layout <sha[:2]>/<sha>.png into <root>/data2root/k6tk/)',
 kr9c_bundle=dict(store='f14', orchard=k['bundle_parts']['f14'], logical=k['f14'], members_listed=cf['f14_members'], listing=F+'/in/f14_members.txt', listing_sha256=sh('in/f14_members.txt')),
 coverage=dict(per_slice=fc['per'], all_six=fc['all'], missing_in_map=len(fc['missing']), camera_unique_png=cf['camera_unique'], camera_png_in_f14=cf['camera_in_f14'], camera_refs_differing_from_k6tk_unique=len(cf['diff_unique']), camera_rows_citing_them=len(cf['rows_citing_diff'])),
 p_frame_audit=inv['frame_host']['recorded_P_frame_audits'][0]['pin'],
 inputs={p:sh(p) for p in ['FRAME_COVERAGE.json','CAMERA_F14_CHECK.json','/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/k/0.json','/scratch/jjyeung/orch_n30/sb_fullinv/out/FULL_INVENTORY.json']},
 caveat='Presence is by map/manifest and P audit, not a fresh byte check on Orchard; the frame audit in N\'s job (s1_admission.FrameAudit) is the byte test. N must stage k6tk shards and f14 at job start (P kit stores f3-f14) and map /data2/k6tk and /data2/kr9c via Q_E4.')
json.dump(rec,open('FRAME_STAGE_RECEIPT.json','w'),indent=1)
print(sh('FRAME_STAGE_RECEIPT.json'))
PY
