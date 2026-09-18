"""Admit one answer-free training row and its authenticated scene assets."""
from __future__ import annotations
import argparse, contextvars, hashlib, importlib.util, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path

DATA_ROOT = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917')
MEMBERSHIP = DATA_ROOT / 'membership/v2/train50k_scene_reuse_answer_free.jsonl'
MEMBERSHIP_SHA = 'fd5703e9d5a6474ea1c9010cc91bf76ca5644f11b5e284399db5056eebfe984c'
COORD_ROOT = Path('/data2/jjyeung/agent_project/.coord')
_ALLOWED_FIELDS = {'dataset','id','option_letters','options','question','question_type',
    'question_video_sha256','scene_name','source_question_type','source_row_1based','video'}
_ARCHIVE = contextvars.ContextVar('r1313_archive', default=None)
_SCENE = None
_CONFIG = None


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def require_data_path(path):
    path = Path(path).resolve()
    if not path.is_relative_to(DATA_ROOT):
        raise ValueError(f'training output/input outside task data root: {path}')
    return path


def scene_id(dataset, scene_name):
    from gt_scene_assets import scene_id as qualified_source_scene
    return qualified_source_scene(dataset, scene_name)


def teacher_rows():
    if sha(MEMBERSHIP) != MEMBERSHIP_SHA:
        raise ValueError('answer-free membership digest mismatch')
    with MEMBERSHIP.open() as handle:
        rows = [json.loads(line) for line in handle]
    if len(rows) != 50000 or len({r['id'] for r in rows}) != 50000:
        raise ValueError('training membership cardinality mismatch')
    for row in rows:
        if set(row) - _ALLOWED_FIELDS or not re.fullmatch(r'vsi590k_\d+', row['id']):
            raise ValueError('unexpected teacher fields or question identity')
        if not isinstance(row['question'], str) or not row['question'].strip():
            raise ValueError('empty training question')
        if row.get('options') and len(row['options']) != len(row['option_letters']):
            raise ValueError('option mapping mismatch')
    return rows


def bind_runtime_row(source, receipt):
    if (source['dataset'], source['scene_name']) != (receipt['dataset'], receipt['scene_name']):
        raise ValueError('question does not match scene receipt')
    if source.get('video') != receipt.get('source_video', source['video']):
        raise ValueError('source video identity mismatch')
    row = dict(source)
    row['source_scene_name'] = row['scene_name']
    row['scene_name'] = scene_id(row['dataset'], row['scene_name'])
    return row


def load_scene():
    global _SCENE
    if _SCENE is None:
        path = require_data_path(os.environ['R1313_SCENE_RECEIPT'])
        if sha(path) != os.environ['R1313_SCENE_RECEIPT_SHA256']:
            raise ValueError('scene receipt digest mismatch')
        from gt_scene_assets import validate_scene
        _SCENE = validate_scene(read_json(path), load_dense=True)
    return _SCENE


def require_r2_store(**_):
    return Path(load_scene()['dense']['path']).parent


def runtime_config():
    global _CONFIG
    path=require_data_path(os.environ['R1313_CONFIG_PATH'])
    if sha(path)!=os.environ['R1313_CONFIG_SHA256']:
        raise ValueError('admitted collection config drift')
    if _CONFIG is None:
        from collect import load_config
        _CONFIG=load_config(path)
    return _CONFIG


def require_effect():
    from collect import coord_guard
    config=runtime_config()
    if config['work_id']!=os.environ['R1313_WORK_ID'] or config['agent_id']!=os.environ['R1313_AGENT_ID']:
        raise RuntimeError('collection lease identity differs from admission')
    coord_guard(config)
    budget=int(os.environ['REQ73_PLANNER_OUTPUT_BUDGET'])
    if budget!=config['budget']:
        raise RuntimeError('provider budget differs from admitted collection')
    claim_path = require_data_path(os.environ['R1313_EPISODE_CLAIM'])
    if claim_path.parent!=Path(config['run_root'])/f'pool_b{budget}'/'claims':
        raise RuntimeError('provider claim is outside the admitted collection')
    claim = read_json(claim_path)
    if claim.get('schema') != 'resizable-pool-claim-v1' or claim.get('episode_id') != os.environ['R1313_EPISODE_ID'] or sha(claim_path) != os.environ['R1313_EPISODE_CLAIM_SHA256']:
        raise RuntimeError('provider call outside the exact admitted episode claim')
    heartbeat_path = claim_path.parents[1] / 'heartbeats' / (claim['worker_id'] + '.json')
    heartbeat = read_json(heartbeat_path)
    if heartbeat.get('episode_id') != claim['episode_id'] or heartbeat.get('worker_id') != claim['worker_id'] or not 0 <= time.time_ns() - heartbeat['wall_time_ns'] < 120_000_000_000:
        raise RuntimeError('episode owner heartbeat is absent, stale, or foreign')
    if not _ARCHIVE.get():
        raise RuntimeError('provider call has no durable episode archive')


def enter_episode(qid):
    if qid != os.environ['R1313_QID']:
        raise ValueError('episode question identity mismatch')
    require_effect()


def custody_effect(function, *args, **kwargs):
    require_effect()
    result = function(*args, **kwargs)
    require_effect()
    return result


def custody_stream(function, *args, **kwargs):
    require_effect()
    for item in function(*args, **kwargs):
        require_effect()
        yield item


def current_archive():
    archive = _ARCHIVE.get()
    if archive is None:
        raise RuntimeError('episode archive is unavailable')
    return archive


def bind_carrier_assets(module):
    receipt = load_scene()
    scene = scene_id(receipt['dataset'], receipt['scene_name'])
    frame_rows = [dict(row, scene=scene) for row in receipt['frames']]
    bindings = {(scene, Path(row['path']).stem): row for row in frame_rows}
    paths = {row['path']: row for row in frame_rows}
    module._FRAMES_CACHE = {scene: {'frame_names': [Path(f['path']).stem for f in frame_rows],
        'indices': [f['ordinal'] for f in frame_rows]}}
    module._R740_CONSUMPTION_REGISTRIES = {'source_videos': {scene: dict(receipt['video'],scene=scene)}, 'cutr_catalogues': {}}
    module._load_r740_frame_bindings = lambda: (bindings, paths)
    module._resolve_dataset = lambda value: receipt['dataset'] if value == scene else _unknown_scene(value)
    from gt_tool_bindings import bind_gt_tools
    bind_gt_tools(module)
    module.SAM3_ROUTER_URL = None
    # The source video endpoint is a literal; the builder changes it to this variable.
    module.SAM3_VIDEO_ROUTER_URL = None


def _unknown_scene(value):
    raise ValueError(f'unknown training scene: {value}')


def bootstrap_runner(package):
    from audit_package import verify_contract
    contract = verify_contract(os.environ['R1313_CONTRACT_PATH'], os.environ['R1313_CONTRACT_SHA256'])
    for key, value in contract['effective_environment'].items():
        if os.environ.get(key) != value:
            raise ValueError(f'collector environment differs from contract: {key}')
    budget = int(os.environ['REQ73_PLANNER_OUTPUT_BUDGET'])
    if budget not in (16384,32768): raise ValueError('invalid output budget')
    if not os.environ.get('GOOGLE_API_KEY'): raise ValueError('GOOGLE_API_KEY is required')
    config=runtime_config()
    if config['source_contract_sha256']!=os.environ['R1313_CONTRACT_SHA256'] or config['budget']!=budget:
        raise ValueError('runner source/budget differs from collection admission')
    if config['mode']=='offline_fixture' and os.environ['GOOGLE_API_KEY']!='offline-fixture-no-network':
        raise ValueError('offline fixtures refuse live credentials')
    from collect import objects
    _,queue,_=objects(config)
    item=next((item for item in queue.catalog.episodes if item.episode_id==os.environ['R1313_EPISODE_ID']),None)
    if item is None or item.payload['row']['id']!=os.environ['R1313_QID'] or item.payload['scene_receipt']['sha256']!=os.environ['R1313_SCENE_RECEIPT_SHA256']:
        raise ValueError('runner episode is outside the admitted membership/scene subset')
    if Path(os.environ['R1313_EPISODE_CLAIM'])!=queue.claim_path(item):
        raise ValueError('runner claim does not bind this question')
    expected=Path(config['run_root'])/'attempts'/os.environ['R1313_QID']/f'b{budget}'
    if require_data_path(os.environ['REQ73_RUN_OUTPUT_ROOT'])!=expected:
        raise ValueError('runner attempt path differs from its question/budget')
    load_scene()
    spec = importlib.util.spec_from_file_location('spatial_agent_r1313', package/'spatial_agent_r1313.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return contract, module


def episode_receipt(system_prompt, questions, output):
    receipt_path = Path(os.environ['R1313_SCENE_RECEIPT'])
    receipt = load_scene()
    return {'schema':'r1313-training-episode-v1','round':1313,
        'fixture_only':runtime_config()['mode']=='offline_fixture',
        'selected_frames_sha256':sha(receipt_path),'scene_receipt':{'path':str(receipt_path),'sha256':sha(receipt_path)},
        'membership_sha256':MEMBERSHIP_SHA,'prompt_sha256':hashlib.sha256(system_prompt.encode()).hexdigest(),
        'input_rows':questions,'experiment_dir':str(output),'planner_output_budget_tokens':int(os.environ['REQ73_PLANNER_OUTPUT_BUDGET']),
        'source_contract':{'path':os.environ['R1313_CONTRACT_PATH'],'sha256':os.environ['R1313_CONTRACT_SHA256']},
        'collection_config':{'path':os.environ['R1313_CONFIG_PATH'],'sha256':os.environ['R1313_CONFIG_SHA256']},
        'geometry':'official_aligned_pose_intrinsic_mesh_gt_valid_support',
        'grounding':'authenticated_scene_instances_projected_in_source_world_with_occlusion',
        'teacher_observations':'initial_text_question_and_choices; zero_inline_RGB; actual_tool_evidence_archived_per_call',
        'student_inputs':{'modality':'question_and_RGB_only','frames':receipt['frames']},
        'helper_behavior':'frame search, boxes, points and masks use fixed donor GT methods; Gemini supplies reasoning; no SAM3 service'}


def runner_main(run_one, package):
    from trace_archive import Archive, install_archive
    parser=argparse.ArgumentParser()
    parser.add_argument('--row',required=True); parser.add_argument('--output',required=True)
    args=parser.parse_args()
    source=read_json(args.row)
    matches=[row for row in teacher_rows() if row['id']==source.get('id')]
    if len(matches)!=1 or matches[0]!=source: raise ValueError('episode row differs from sealed answer-free membership')
    output=require_data_path(args.output)
    if output != require_data_path(os.environ['REQ73_RUN_OUTPUT_ROOT']):raise ValueError('output differs from admitted attempt')
    output.mkdir(parents=True,exist_ok=False)
    for name in ('tmp','matplotlib','cache'):
        (output/'runtime'/name).mkdir(parents=True,exist_ok=False)
    with (output/'EPISODE_ADMISSION.json').open('x') as handle:
        json.dump({'question_id':source['id'],'episode_id':os.environ['R1313_EPISODE_ID'],'claim':os.environ['R1313_EPISODE_CLAIM']},handle)
        handle.flush();os.fsync(handle.fileno())
    prompt=(package/'prompt_base_1313.txt').read_text()
    item=bind_runtime_row(source,load_scene())
    archive=Archive(output/'archive',{'question_id':source['id'],'budget':int(os.environ['REQ73_PLANNER_OUTPUT_BUDGET']),
        'source_question':source,'scene_receipt_path':os.environ['R1313_SCENE_RECEIPT']}, trusted_roots=(DATA_ROOT,))
    _ARCHIVE.set(archive)
    with install_archive(archive):
        archive.event('scene_input',load_scene())
        try:
            result=run_one(item,prompt,str(output),260,episode_receipt(prompt,[item],output))
            archive.event('episode_terminal',{'status':'completed','error':result.get('error')})
        except BaseException as exc:
            archive.event('episode_terminal',{'status':'error','error_type':type(exc).__name__,'message':str(exc)})
            raise
    return 0


def tool_callbacks(archive):
    from langchain_core.callbacks import BaseCallbackHandler
    class DurableToolCallbacks(BaseCallbackHandler):
        raise_error = True
        def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
            archive.event('tool_start', {'call_id':str(run_id),'tool':serialized.get('name'), 'input':input_str})
        def on_tool_end(self, output, *, run_id, **kwargs):
            archive.event('tool_terminal', {'call_id':str(run_id),'status':'ok','output':output})
        def on_tool_error(self, error, *, run_id, **kwargs):
            archive.event('tool_terminal', {'call_id':str(run_id),'status':'error','error_type':type(error).__name__,'message':str(error)})
    return [DurableToolCallbacks()]
