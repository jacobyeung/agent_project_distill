from pathlib import Path
import json
K=Path(__file__).resolve().parents[1]
def edit(n,old,new):
 p=K/n;s=p.read_text();assert old in s,(n,old);p.write_text(s.replace(old,new))
# Preserve all native membership, tier and video checks before applying either filter.
edit('reader/evaluator/data.py',"    return sorted(rows, key=lambda x: x['example_id'])",'''    if 'question_types' in spec:
        kinds = spec['question_types']
        if not isinstance(kinds, list) or not kinds or any(not isinstance(k, str) for k in kinds) or kinds != sorted(set(kinds)):
            raise ValueError('Require a nonempty sorted unique question_types list')
        if not set(kinds) <= {r['question_type'] for r in rows}:
            raise ValueError('Unknown ReVSI question type')
        rows = [r for r in rows if r['question_type'] in kinds]
    if 'example_ids' in spec:
        ids = spec['example_ids']
        if not isinstance(ids, list) or any(not isinstance(k, str) for k in ids) or ids != sorted(set(ids)) or not set(ids) <= {r['example_id'] for r in rows}:
            raise ValueError('Invalid ReVSI proof IDs')
        rows = [r for r in rows if r['example_id'] in ids]
    return sorted(rows, key=lambda x: x['example_id'])''')
p=K/'reader/official_adapter.py';s=p.read_text();a=s.index("ROWS_SHA=");b=s.index('\n\n\ndef load_rows',a)
s=s[:a]+'''ROWS_SHA='511c7e8a190235bd17b87a903db569abd5f6b245f444b50dfc3785c06f9be1e9'
COUNTS={'object_counting_single':86,'object_counting_multiple':49,
        'object_rel_direction_forward_easy':20,'object_rel_direction_backward_hard':20,
        'object_rel_direction_forward_hard':15,'object_rel_direction_backward_easy':13,
        'object_rel_distance_closest':84,'object_rel_distance_farthest':56,
        'object_size_estimation':273,'route_planning':63}
CELL=dict(model='cp1m200',layout='duplicate',benchmarks=['revsi'],frames=32,
          decoding='greedy',thinking=True,max_tokens=16384,name='a0')


def dataset(rows):
    directory=Path(rows).parent
    names={'rows':'revsi999_rows_t32.json','membership':'revsi999_membership.json',
           'videos':'revsi999_videos_t32.json','indices':'revsi_indices.json'}
    spec=dict(benchmark='revsi',set='official999',tier=32,question_types=sorted(COUNTS))
    for key,name in names.items():
        path=directory/name
        spec[key]=dict(path=str(path.resolve()),sha256=sha(path))
    if not spec['indices']['sha256'].startswith('290111cf'):raise ValueError('Source indices differ')
    return spec
'''+s[b:]
s=s.replace('COHORT_OFFICIAL6.jsonl','COHORT_REVSI5.jsonl').replace('Six-task membership differs','Five-category membership differs').replace('official six-task cohort','ReVSI five-category cohort')
a=s.index("datasets=[dict(benchmark='official5130',");b=s.index('gpus=1,build_only=False',a)
s=s[:a]+"datasets=[dataset(rows)],\n        roots=dict(revsi_video_root=str(Path(video_root).resolve())),"+s[b:];p.write_text(s)
# Use the same chain and keep the dev Phase B file byte-identical.
edit('reader/chain.py','COHORT_OFFICIAL6.jsonl','COHORT_REVSI5.jsonl')
edit('reader/chain.py','allow_partial=proof or fixture))','allow_partial=proof or fixture,parent_answers=config.get("parent_answers")))')
# Neutral local media path; media root is a required, opaque Orchard path.
edit('launcher/orchard_launcher.py','pool="/project/community/jjyeung/okh7/x27ret"):', 'pool="/project/community/jjyeung/okh7/x27ret", media_root=None, phase_b=True):')
edit('launcher/orchard_launcher.py','    valid_token(token)\n    destination=Path(destination)', '''    if not isinstance(media_root,str) or not re.fullmatch(r'/project/community/jjyeung/okh7/[0-9a-f]{8,64}/?',media_root):
        raise ValueError('Require an opaque --media-root under /project/community/jjyeung/okh7/')
    valid_token(token)
    destination=Path(destination)''')
edit('launcher/orchard_launcher.py','all 288 videos','all 261 videos')
edit('launcher/orchard_launcher.py',"inputs=dict(rows=str(logical/'q0.jsonl'),video_root='/project/community/jjyeung/3e0e8a36',", "inputs=dict(rows=str(payload_root/'inputs/revsi999_rows_t32.json'),video_root=str(logical/'v0'),")
edit('launcher/orchard_launcher.py',"for directory in ('reader','cohort','parity'):","for directory in ('reader','cohort','parity','inputs'):")
edit('launcher/orchard_launcher.py',"p.name!='meta_5130.jsonl' and p.name!='FRAME_PLAN.json'", "p.name not in ('meta_5130.jsonl','COHORT_OFFICIAL6.jsonl','FRAME_PLAN.json','REVSI_PUSH_FILES.json','REVSI999_PROVENANCE.json')")
edit('launcher/orchard_launcher.py',"mode=mode,phase_b=mode=='proof',pool=pool", "mode=mode,phase_b=mode=='proof' and phase_b,media_root=media_root,pool=pool")
edit('launcher/orchard_launcher.py',"    prepare_parser.add_argument('--frame-plan')", "    prepare_parser.add_argument('--media-root',required=True)\n    prepare_parser.add_argument('--skip-phase-b',action='store_true')\n    prepare_parser.add_argument('--frame-plan')")
edit('launcher/orchard_launcher.py','prepare(args.token, args.destination, args.frame_plan, args.mode, args.pool)', 'prepare(args.token, args.destination, args.frame_plan, args.mode, args.pool, args.media_root, not args.skip_phase_b)')
p=K/'launcher/orchard_stage.py';s=p.read_text();a=s.index('    for row in rows:\n',s.index('def stage_videos'));s=s[:a]+'''    import re
    media_root=config.get('media_root','')
    if not re.fullmatch(r'/project/community/jjyeung/okh7/[0-9a-f]{8,64}/?',media_root):
        raise ValueError('Unregistered media root')
    for row in rows:
        relative(row['relative_path'])
        source=video_source(row,media_root)
        if source.stat().st_size!=row['bytes']:raise ValueError('Video byte count differs')
        target=destination/(row['sha256']+'.mp4')
        copied=copy_parts([dict(path=str(source),bytes=row['bytes'],sha256=row['sha256'])],target,
                   lambda part:Path(part['path']).open('rb'))
        verified.append(dict(relative_path=row['relative_path'],alias_path=str(source),**copied))
    return dict(videos=len(rows),verified=True,files=verified)


def video_source(row,media_root):
    root=Path(media_root).resolve();source=root/row['relative_path']
    if not source.resolve().is_relative_to(root):raise ValueError('Video escapes media root')
    return source
''';p.write_text(s)
# Production frame checks use compact clip anchors and reconstructed source timing.
edit('cohort/frame_plan.py',"p=expected['videos'][t['dataset']+'/'+t['scene_name']+'.mp4']",'''p=expected['videos'][t['scene']+'.mp4'] if t['benchmark']=='revsi' else expected['videos'][t['dataset']+'/'+t['scene_name']+'.mp4']
        if t['benchmark']=='revsi':
            if p['total_frames']!=32:raise ValueError('Require exact tier-32 clip')
            source=t['source_frame_indices'];total=source[-1]+1
            p=dict(p,duplicate_indices=[source[i] for i in p['duplicate_indices']],
                   total_frames=total,fps=p['fps']*total/32)''')
# NumPy tensor stand-in supports the unchanged official metric on CPU.
edit('proof/fakes.py',"ones_like=lambda x:tensor(np.ones_like(x))", "float64=np.float64,linspace=lambda start,end,steps,dtype:tensor(np.linspace(start,end,steps,dtype=dtype)),\n        stack=lambda xs:tensor(np.stack(xs)),ones_like=lambda x:tensor(np.ones_like(x))")
edit('proof/fakes.py','    def to(self,*a,**kw):return self','    def to(self,*a,**kw):return self.astype(a[0]).view(Tensor) if a else self\n    def nanmean(self):return tensor(np.nanmean(np.asarray(self)))')
edit('proof/fixtures.py','range(40)','range(32)')
