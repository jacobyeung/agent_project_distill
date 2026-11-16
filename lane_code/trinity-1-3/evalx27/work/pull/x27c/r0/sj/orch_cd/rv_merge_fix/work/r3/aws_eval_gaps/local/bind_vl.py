"""Bind native model/layout cells locally; this command never contacts AWS."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import secrets
import sys
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ROOT,AWS,archive,pin,save,sha

sys.path.insert(0,str(ROOT/'evaluator'))
from evalpath.items import MEMBERSHIP_SHA256
from evalpath.kit_inputs import GEN_SHA,SCO_SHA
from cells import frame_count, validate_token_budget

DATA=AWS+'/ap/distill/orch/data2root/jjyeung/agent_project_data'
PAPER=DATA+'/student_diagnostic_pilot_20260918/eval_instructed_provisional_e3e9ffb/artifacts/paper_eval'
PRESETS={
    'pointing_video_base': [('base','duplicate',['pointing_video'])],
    'erosion': [],
    'E11c': [('base',l,['vsi500','vstiv3']) for l in ('spread','duplicate')],
    'P4': [('base',l,['vsi500','vstiv3']) for l in ('duplicate','P0.5','P0.2')],
    'references':[(m,'spread',['vsi500','revsi']) for m in ('base','f17')],
}


def epoch(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()


def validate_models(models,needed,build_only):
    if 'base' not in models:raise ValueError('Base snapshot must be pinned for tokenizer/config')
    if not needed<=set(models):raise ValueError('Preset model pin missing')
    for name in needed|{'base'}:
        spec=models[name]
        if spec['kind']=='snapshot':
            if not spec['path'].startswith('/'):raise ValueError('Snapshot path must be absolute')
            pin(spec['manifest']['path']+'@'+spec['manifest']['sha256'])
        elif spec['kind']=='archive':
            pin(spec['path']+'@'+spec['sha256'])
        elif spec['kind']=='c1_export':
            pin(spec['path']+'@'+spec['sha256'])
            if Path(spec['path']).name!='artifact.json':raise ValueError('Candidate must pin artifact.json')
        else:raise ValueError('Only native full weights are supported')
        if name=='base' and spec['kind']!='snapshot':raise ValueError('Base must be a snapshot')
        if not build_only and '0'*64 in json.dumps(spec):raise ValueError('Unbound model checksum')


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', choices=['vllm','native_routed'], default='vllm')
    p.add_argument('--direct-request', action='append', default=[], help='BENCHMARK=REQUEST.json@sha256; authenticate legacy direct journal checkpoint/layout')
    p.add_argument('--direct-answers', action='append', default=[], help='BENCHMARK=journal.jsonl@sha256; reuse same-checkpoint direct answers')
    p.add_argument('--route-table', help='Frozen dev route table absolute-path@sha256; required for native_routed')
    p.add_argument('--preset',choices=list(PRESETS)+['custom'],required=True)
    p.add_argument('--models',type=Path,required=True,help='Model pin JSON; see inputs/MODELS.example.json')
    p.add_argument('--cells',type=Path,help='Custom list of {model,layout,benchmarks}')
    p.add_argument('--include-ft-x',action='store_true')
    p.add_argument('--candidate',action='append',default=[],metavar='NAME=ARTIFACT_PATH@SHA256')
    p.add_argument('--pointing-items',type=Path,default=Path('/scratch/jjyeung/orch_cd/toolprog/work/orchard/in/ITEMS.jsonl'))
    p.add_argument('--pointing-scenes',type=Path,default=Path('/scratch/jjyeung/orch_cd/toolprog/work/orchard/in/SCENES.json'))
    p.add_argument('--pointing-gt-root',type=Path,default=Path('/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet'))
    p.add_argument('--pointing-kit',type=Path,default=Path('/scratch/jjyeung/orch_cd/toolprog/work/aws/kit/a.py'))
    p.add_argument('--pointing-programs',type=Path,default=Path('/scratch/jjyeung/orch_cd/toolprog/work/tp/programs.py'))
    p.add_argument('--pointing-membership',help='Reuse a fixed membership absolute-path@sha256; skips GT scan')
    p.add_argument('--allow-gt-scan',action='store_true',help='Explicit user approval for heavy local GT I/O')
    p.add_argument('--pointing-video-root',default=DATA+'/vsibench_videos')
    p.add_argument('--gpus',type=int,default=8)
    p.add_argument('--gpu-cap',type=int,required=True)
    p.add_argument('--other-gpus',type=int,default=0)
    p.add_argument('--remote-root',default=AWS+'/ap/'+secrets.token_hex(4))
    p.add_argument('--output',help='Reuse a previous opaque AWS output path to resume identical bindings')
    p.add_argument('--video-root',default=DATA+'/vsibench_videos')
    p.add_argument('--data2-root',default=AWS+'/ap/distill/orch/data2root')
    p.add_argument('--revsi-video-root',default=AWS+'/ap/'+hashlib.sha256(b'revsi32').hexdigest()[:8]+'/f')
    p.add_argument('--revsi-set',choices=('cap452','official999'),default='cap452',help='ReVSI item set: the 452 cap71 rows or the official 999')
    p.add_argument('--revsi-tier',type=int,choices=(32,64),default=32,help='ReVSI frame tier (official999 only for 64); the video root must hold that tier')
    p.add_argument('--revsi-sidecar',help='Original 32-frame sidecar absolute-path@sha256 (66e0175d...)')
    p.add_argument('--vsi-rows',type=Path,default=Path('/data2/jjyeung/agent_project_data/answerable500_gt_canonical_20260902/answerable500_gt_canonical.json'))
    p.add_argument('--vsi-membership',type=Path,default=Path('/data2/jjyeung/agent_project_data/answerable500_membership_20260824/MEMBERSHIP_ANSWERABLE_500.json'))
    p.add_argument('--official-rows',type=Path,default=Path('/scratch/jjyeung/orch_cd/aws_32/a_build/eval/orchard_bin/cp4tk_eval/official/meta_5130.jsonl'))
    p.add_argument('--vsti-generation',default=PAPER+'/vstibench_repr450_v3/prepared/generation/manifest.json')
    p.add_argument('--vsti-scoring',default=PAPER+'/vstibench_repr450_v3/prepared/scoring/manifest.json')
    p.add_argument('--vsti-full-rows', type=Path, default=ROOT/'inputs/vstibench_test.json')
    p.add_argument('--vsti-erratum', type=Path, default=ROOT/'inputs/vstibench_erratum_dropped_items.json')
    p.add_argument('--vsti-videos',type=Path,default=ROOT/'inputs/vsti_videos.json')
    p.add_argument('--vsti-video-root', default=DATA+'/../raw_datasets/vstibench_hf/extracted/ScanNet/videos/val')
    p.add_argument('--dev-rows',type=Path,default=ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl',help='CP1 dev rows JSONL (meta_5130 schema, ScanNet val scenes)')
    p.add_argument('--slice',type=int)
    p.add_argument('--seed',type=int,default=17)
    p.add_argument('--smoke-items',type=int,default=0)
    p.add_argument('--max-seqs',type=int,default=128)
    p.add_argument('--inflight',type=int,default=64)
    p.add_argument('--max-model-len',type=int,default=49152)
    p.add_argument('--until',help='UTC deadline, no more than four hours away')
    p.add_argument('--build-only',action='store_true')
    p.add_argument('--artifact-dir',type=Path,help='Separate local binding stage under this workspace')
    return p


def bind(a):
    artifact=Path(a.artifact_dir).resolve() if a.artifact_dir else ROOT
    if not (artifact.is_relative_to(ROOT.resolve()) or artifact.is_relative_to((ROOT.parent/'tmp').resolve())):raise ValueError('Artifact directory must stay in workspace')
    if artifact!=ROOT:
        (artifact/'kit/b').mkdir(parents=True,exist_ok=True)
        (artifact/'kit/b/1.py').write_bytes((ROOT/'kit/b/1.py').read_bytes())
    if not 1<=a.gpus<=8 or not 1<=a.gpu_cap<=64 or a.other_gpus<0 or a.gpus+a.other_gpus>a.gpu_cap:
        raise ValueError('GPU allocation exceeds bind-time cap')
    if not re.fullmatch(re.escape(AWS)+r'/ap/[0-9a-f]{8}',a.remote_root):raise ValueError('Require opaque AWS root')
    if a.output and not re.fullmatch(re.escape(AWS)+r'/ap/[0-9a-f]{8}/o/[0-9a-f]{24}',a.output):raise ValueError('Require opaque output path')
    if a.slice is not None and not 1<=a.slice<=5130:raise ValueError('Invalid official slice')
    if a.smoke_items and a.smoke_items<16:raise ValueError('Smoke needs at least 16 parity items')
    if a.inflight<1 or a.max_seqs<1 or a.max_model_len<32768:raise ValueError('Invalid engine limits')
    if a.build_only:a.until='2000-01-01T00:00:00Z'
    elif not a.until or not 300<epoch(a.until)-time.time()<=14400:raise ValueError('Require live deadline within four hours')
    models=json.loads(a.models.read_text())
    candidates=[]
    for value in a.candidate:
        name, sep, value=value.partition('=')
        if not sep or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',name) or name in models:
            raise ValueError('Candidate name must be unique and cannot replace base')
        models[name]=dict(kind='c1_export',**pin(value));candidates.append(name)
    if a.candidate and a.preset not in ('erosion','custom'):raise ValueError('Candidates require the erosion or custom preset')
    if a.preset=='custom':
        if not a.cells:raise ValueError('Custom preset requires cells')
        cells=json.loads(a.cells.read_text())
    elif a.preset=='erosion':
        if not candidates:raise ValueError('Erosion requires at least one --candidate')
        if a.slice is not None or a.seed!=17:raise ValueError('Erosion fixes VSI slice at 100 items, seed 17')
        cells=[dict(model=m,layout='spread',benchmarks=['vsi500_slice','pointing']) for m in ['base']+candidates]
    else:
        cells=[dict(model=m,layout=l,benchmarks=b) for m,l,b in PRESETS[a.preset]]
    if a.include_ft_x:
        if a.preset!='references' or 'FT-X' not in models:raise ValueError('FT-X references require its model pin')
        cells.append(dict(model='FT-X',layout='spread',benchmarks=['vsi500','revsi']))
    if not cells:raise ValueError('Empty cells')
    for c in cells:
        frame_count(c)
        validate_token_budget(c, context_limit=a.max_model_len)
        if 'pointing_video' in c['benchmarks']:
            if c['layout']!='duplicate' or c.get('decoding','greedy')!='greedy':
                raise ValueError('Pointing video requires duplicate layout and greedy decoding')
        if c.get('decoding','greedy') not in ('greedy','qwen_sampling'):raise ValueError('Unknown decoding')
        if c['layout'] not in ('spread','duplicate','P0.5','P0.2') or not c['benchmarks']:
            raise ValueError('Invalid cell')
        if len(set(c['benchmarks']))!=len(c['benchmarks']):raise ValueError('Repeated benchmark')
        if 'revsi' in c['benchmarks'] and c['layout'].startswith('P'):
            raise ValueError('ReVSI paired layouts require separately pinned source recordings')
    validate_models(models,{c['model'] for c in cells},a.build_only)
    selected={b for c in cells for b in c['benchmarks']}
    source_pins=json.loads((ROOT/'inputs/SOURCE_PINS.json').read_text())
    print(json.dumps({'dev_overlap':source_pins['dev_overlap']}),flush=True)
    if 'devrows' in selected and sha(a.dev_rows)!=source_pins['DEV_ITEMS_noReVSI.jsonl']['sha256']:
        raise ValueError('Frame and route dev cells require pinned DEV_ITEMS_noReVSI.jsonl')
    if not selected<={'vsi500','vsi500_slice','pointing','pointing_video','vstiv3','vstifull','official5130','revsi','devrows'}:raise ValueError('Unknown benchmark')
    if 'pointing' in selected and any(c['layout']!='spread' for c in cells if 'pointing' in c['benchmarks']):
        raise ValueError('Pointing requires spread layout')
    blobs={};datasets=[]
    def embed(path):
        path=Path(path)
        if path.stat().st_size>8*1024*1024:raise ValueError('Metadata read bound exceeded')
        raw=path.read_bytes();name=str(len(blobs)+1)+path.suffix
        blobs[name]=raw
        return dict(path='$Q/'+name,sha256=hashlib.sha256(raw).hexdigest())
    if selected & {'vsi500','vsi500_slice'}:
        membership=embed(a.vsi_membership)
        if membership['sha256']!=MEMBERSHIP_SHA256:raise ValueError('VSI membership pin differs')
        rows=embed(a.vsi_rows)
        if 'vsi500' in selected:datasets.append(dict(benchmark='vsi500',membership=membership,rows=rows))
        if 'vsi500_slice' in selected:
            from erosion_bind import vsi_membership
            datasets.append(dict(benchmark='vsi500_slice',membership=membership,rows=rows,
                slice_membership=embed(vsi_membership(a.vsi_rows,a.vsi_membership))))
    if selected & {'pointing','pointing_video'}:
        from erosion_bind import pointing_membership,bounded_json,validate_pointing
        if a.pointing_membership:
            p=pin(a.pointing_membership);path=Path(p['path'])
            if sha(path)!=p['sha256']:raise ValueError('Pointing membership pin differs')
        else:
            if not a.allow_gt_scan:raise ValueError('GT scan requires --allow-gt-scan after user approval, or --pointing-membership')
            path=pointing_membership(a.pointing_items,a.pointing_scenes,a.pointing_gt_root,a.pointing_kit,a.pointing_programs)
        validate_pointing(bounded_json(path),review=a.build_only)
        member=embed(path)
        if 'pointing' in selected:datasets.append(dict(benchmark='pointing',membership=member))
        if 'pointing_video' in selected:
            datasets.append(dict(benchmark='pointing_video',membership=member,variants=['A','B','C']))
    if 'vstifull' in selected:
        from evalpath.items import load_items
        d = dict(benchmark='vstifull', rows=embed(a.vsti_full_rows), erratum=embed(a.vsti_erratum), videos=embed(a.vsti_videos))
        load_items({**d, 'rows':{**d['rows'], 'path':str(a.vsti_full_rows)},
                    'erratum':{**d['erratum'], 'path':str(a.vsti_erratum)},
                    'videos':{**d['videos'], 'path':str(a.vsti_videos)}},
                   {'video_root':a.vsti_video_root})
        datasets.append(d)
    if 'vstiv3' in selected:
        datasets.append(dict(benchmark='vstiv3',version='v3',
            generation_manifest=dict(path=a.vsti_generation,sha256=GEN_SHA),
            scoring_manifest=dict(path=a.vsti_scoring,sha256=SCO_SHA)))
    if 'official5130' in selected:
        rows=embed(a.official_rows)
        if not rows['sha256'].startswith('d69dfb86'):raise ValueError('Official metadata pin differs')
        datasets.append(dict(benchmark='official5130',rows=rows,slice=a.slice,seed=a.seed))
    elif a.slice is not None:raise ValueError('Slice requires official5130')
    if 'devrows' in selected:
        if not a.dev_rows:raise ValueError('devrows requires --dev-rows')
        datasets.append(dict(benchmark='devrows',rows=embed(a.dev_rows)))
    if 'revsi' in selected:
        if a.revsi_tier!=32 and a.revsi_set!='official999':raise ValueError('ReVSI tier 64 requires --revsi-set official999')
        for c in cells:
            if 'revsi' in c['benchmarks'] and c.get('frames',32)!=a.revsi_tier:
                raise ValueError('ReVSI cells must read exactly the bound tier frame count')
        if a.revsi_set=='official999':
            if a.revsi_sidecar:raise ValueError('official999 GT is the official parquet; no sidecar')
            d=dict(benchmark='revsi',set='official999',tier=a.revsi_tier,rows=embed(ROOT/f'inputs/revsi999_rows_t{a.revsi_tier}.json'),
                   membership=embed(ROOT/'inputs/revsi999_membership.json'),indices=embed(ROOT/'inputs/revsi_indices.json'),
                   videos=embed(ROOT/f'inputs/revsi999_videos_t{a.revsi_tier}.json'))
        else:
            d=dict(benchmark='revsi',rows=embed(ROOT/'inputs/revsi_rows.json'),
               membership=embed(ROOT/'inputs/revsi_membership.json'),indices=embed(ROOT/'inputs/revsi_indices.json'))
        if a.revsi_sidecar:
            d['sidecar']=pin(a.revsi_sidecar)
            if not d['sidecar']['sha256'].startswith('66e0175d'):raise ValueError('Require original 32-frame sidecar')
        datasets.append(d)
    route_config = None
    if a.engine == 'native_routed':
        from routing import validate_table, verify_freeze, route_report, reuse_direct, CP1_SHA
        dev_collection = all(c['benchmarks']==['devrows'] and c.get('route_mode') in ('direct','routed') for c in cells)
        if not a.route_table:
            if not dev_collection:
                raise ValueError('native_routed requires --route-table absolute-path@sha256')
            from routing import DEV_SHA, PROTOCOL
            path = artifact/'inputs/DEV_COLLECTION_ONLY.json'
            save(path,dict(schema='dev-route-table-v1', dev_sha256=DEV_SHA, checkpoint_sha256=CP1_SHA,
                protocol=PROTOCOL, default='direct', selection='scene-bootstrap-lower95-positive',
                routes={}, dev_only=True))
            a.route_table = str(path)+'@'+sha(path)
        route_pin = pin(a.route_table)
        if sha(route_pin['path']) != route_pin['sha256']:
            raise ValueError('Route table SHA differs')
        table = validate_table(json.loads(Path(route_pin['path']).read_text()), review=a.build_only, dev=dev_collection)
        if not dev_collection:
            dev=ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl'
            verify_freeze(table,dict(path=str(dev),sha256=sha(dev)),review=a.build_only)
        for c in cells:
            if c['benchmarks']!=['devrows'] and (len(c['benchmarks'])!=1 or c['benchmarks'][0] not in ('official5130','revsi')):
                raise ValueError('Official routes require one VSI or ReVSI benchmark per cell; VSTI has no routed types')
            if c['model'] != 'cp1m200' or models[c['model']].get('sha256') != CP1_SHA:
                raise ValueError('Frozen routes require CP1 m200')
            if c.get('frames',32) != 32 or c['layout'] != 'duplicate' or c.get('frame_set'):
                raise ValueError('Native routed cells use standard 32 decoded anchors')
            if c.get('route_mode','policy') not in ('policy','direct','routed'):raise ValueError('Unknown route mode')
            if c.get('route_mode','policy') != 'policy' and c['benchmarks'] != ['devrows']:
                raise ValueError('Forced direct/routed arms are dev-only')
        route_config = dict(table=embed(route_pin['path']), cfg=json.loads((ROOT/'inputs/cp1_config.json').read_text()),
                            trainer_sha256=sha(ROOT/'inputs/cp1_trainer.tar'))
        from data import tasks_for
        all_tasks=[]
        for spec in datasets:
            local_spec={**spec}
            for key,value in spec.items():
                if isinstance(value,dict) and value.get('path','').startswith('$Q/'):
                    # Read the already pinned binder inputs without touching media.
                    path=artifact/'bind_inputs'/Path(value['path']).name
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blobs[Path(value['path']).name])
                    local_spec[key]={**value,'path':str(path)}
            all_tasks.extend(tasks_for(local_spec,dict(video_root=a.video_root,revsi_video_root=a.revsi_video_root)))
        report=route_report(table,all_tasks)
        print(json.dumps(report,sort_keys=True),flush=True)
        route_config.update(report)
        direct_answers={};direct_requests={}
        for argument in a.direct_request:
            benchmark,sep,value=argument.partition('=')
            if not sep or benchmark not in selected or benchmark in direct_requests:raise ValueError('Invalid direct request benchmark')
            direct_requests[benchmark]=pin(value)
            if sha(direct_requests[benchmark]['path'])!=direct_requests[benchmark]['sha256']:raise ValueError('Direct request SHA differs')
        if a.direct_answers and dev_collection:raise ValueError('Direct reuse is for official policy cells')
        for argument in a.direct_answers:
            benchmark,sep,value=argument.partition('=')
            if not sep or benchmark not in selected or benchmark in direct_answers:
                raise ValueError('Direct answers require one pin per selected benchmark')
            source=pin(value)
            reuse_direct([t for t in all_tasks if t['benchmark']==benchmark],source,table,direct_requests.get(benchmark))
            # Keep the journal bytes authenticated in the shipping bundle.
            raw=Path(source['path']).read_bytes()
            if len(raw)>64*1024*1024:raise ValueError('Direct journal exceeds 64 MiB; provide a compact scored journal')
            name=str(len(blobs)+1)+'.jsonl';blobs[name]=raw
            direct_answers[benchmark]=dict(path='$Q/'+name,sha256=source['sha256'])
        if set(direct_requests)-set(direct_answers):raise ValueError('Direct request requires its answer journal')
        route_config['direct_answers']=direct_answers
        route_config['direct_requests']={b:embed(p['path']) for b,p in direct_requests.items()}
    elif a.route_table or a.direct_answers or a.direct_request:
        raise ValueError('Route tables require the native_routed engine')
    code={}
    for directory in (ROOT/'evaluator',ROOT/'evaluator/evalpath',ROOT/'evaluator/trainer'):
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix in ('.py','.json'):
                code[str(path.relative_to(ROOT/'evaluator'))]=path.read_bytes()
    for i,path in enumerate(sorted((ROOT/'inputs/trainer_sources').iterdir())):
        code['audit/'+str(i)+'.py']=path.read_bytes()
    code['audit/0.json']=(ROOT/'inputs/SOURCE_PINS.json').read_bytes()
    if route_config:
        import tarfile
        sources = {}
        with tarfile.open(ROOT/'inputs/cp1_trainer.tar') as tf:
            for member in tf.getmembers():
                if not member.isfile(): continue
                if member.name.startswith('/') or '..' in Path(member.name).parts:
                    raise ValueError('Unsafe trainer archive')
                raw = tf.extractfile(member).read()
                code[member.name] = raw
                if member.name.startswith('student_pilot/'):
                    sources[member.name[len('student_pilot/'):]] = hashlib.sha256(raw).hexdigest()
        route_config['trainer'] = dict(commit='e6456bcecb8d4a8f4f68158eb68275f8befff128', sources=sources)
    archive(artifact/'kit/k/0.tar',code)
    request=dict(models=models,cells=cells,datasets=datasets,gpus=a.gpus,build_only=a.build_only,
        roots=dict(vsti_video_root=a.vsti_video_root,video_root=a.video_root,data2_root=a.data2_root,revsi_video_root=a.revsi_video_root,
                   pointing_video_root=a.pointing_video_root),
        max_tokens=16384,temperature=0,thinking=True,max_model_len=a.max_model_len,max_seqs=a.max_seqs,
        inflight=a.inflight,smoke_items=a.smoke_items,engine_version='0.32.0',source_sha256=sha(artifact/'kit/k/0.tar'))
    if selected=={'pointing_video'}:request.update(max_tokens=64,temperature=0,thinking=False)
    if a.preset=='erosion':request['parity_per_benchmark']=True
    if route_config: request.update(engine='native_routed', routing=route_config)
    binding=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
    request.update(binding=binding,output=a.output or a.remote_root+'/o/'+binding[:24],until=a.until)
    blobs['0.json']=(json.dumps(request,sort_keys=True)+'\n').encode()
    archive(artifact/'kit/k/1.tar',blobs)
    save(artifact/'inputs/REQUEST.json',request)
    auth=dict(gpus=a.gpus,gpu_cap=a.gpu_cap,other_gpus=a.other_gpus,until=a.until,
              build_only=a.build_only,root=a.remote_root,request_sha256=sha(artifact/'kit/k/1.tar'))
    save(artifact/'kit/k/2.json',auth)
    name='a15_cot_ap'+secrets.token_hex(4)
    script='''#!/bin/bash
#SBATCH --job-name=NAME
#SBATCH --nodes=1
#SBATCH --gres=gpu:COUNT
#SBATCH --mem=MEMG
#SBATCH --cpus-per-task=32
#SBATCH --partition=batch
#SBATCH --qos=normal
#SBATCH --time=04:00:00
#SBATCH --chdir=REMOTE
#SBATCH --output=REMOTE/o/%j.out
#SBATCH --error=REMOTE/o/%j.err
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
R=REMOTE
J=/tmp/OPAQUE/${SLURM_JOB_ID:?}
mkdir -p "$J" "$J/cache" "$J/tmp"
# Keep the tails of the node-local logs after the job ends (opaque names).
trap 'for n in 0 1; do [ -f "$J/$n.log" ] && tail -c 20000 "$J/$n.log" > "$R/o/${SLURM_JOB_ID}.t$n" || true; done' EXIT
for key in $(compgen -e); do
    case "$key" in *_API_KEY|*_SECRET*|*_TOKEN|*_CREDENTIAL*) unset "$key" ;; esac
done
source /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/1742c666/b/c2.sh > "$J/0.log" 2>&1
export HOME="$J" TMPDIR="$J/tmp" XDG_CACHE_HOME="$J/cache"
export HF_HOME="$J/cache/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1 VLLM_USE_FLASHINFER_SAMPLER=0 PYTHONDONTWRITEBYTECODE=1
cd "$J"
/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin/python -B "$R/b/1.py" "$R" "$J" > "$J/1.log" 2>&1
'''
    for old,new in [('NAME',name),('COUNT',str(a.gpus)),('MEM',str(a.gpus*80)),('REMOTE',a.remote_root),('OPAQUE',a.remote_root.rsplit('/',1)[-1])]:
        script=script.replace(old,new)
    (artifact/'kit/b/0.sh').write_text(script)
    save(artifact/'DESTINATIONS.json',{'root':a.remote_root,'output':request['output']})
    save(artifact/'JOBS.json',{'name':name,'script':'b/0.sh','gpus':a.gpus})
    print(json.dumps(dict(cells=len(cells),gpus=a.gpus,root=a.remote_root,build_only=a.build_only,binding=binding)))
    return request


if __name__=='__main__':bind(parser().parse_args())
