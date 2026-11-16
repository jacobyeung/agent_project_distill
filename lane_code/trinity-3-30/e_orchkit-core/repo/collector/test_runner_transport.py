"""Real native runner/GT/lease fixtures; only Google network methods return test data."""
from __future__ import annotations
import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from google.genai import types
from google.genai.models import Models
from gt_scene_assets import DATA_ROOT, pin, read_json, sha, write_json
from collect import objects, initialize, child_env, load_config, coord_guard
from coordination import Coord, do_claim, cmd_heartbeat, cmd_complete

HERE = Path(__file__).resolve().parent
TASK = DATA_ROOT / 'runtime_control/gt_teacher_r1313'
REGISTRY = TASK / 'scene104acbf7d2_v1/registry.json'


def fixture_config(root, contract, contract_sha):
    root.mkdir(parents=True, exist_ok=False)
    owner = 'r1313-offline-fixture-' + root.name
    os.environ['AGENT_ID'] = owner
    coord = Coord(str(root / 'coord'))
    coord.ensure()
    work_id = 'fixture__r1313__' + root.name
    won, reason = do_claim(coord, work_id, {'command': 'CPU native transport fixture; no network spend'})
    if not won:
        raise RuntimeError(reason)
    if do_claim(coord, work_id, {}) != (False, 'lease-held'):
        raise AssertionError('collection lease failed exclusivity')
    cmd_heartbeat(coord, SimpleNamespace(work_id=work_id, status='running', note='offline fixture'))
    config = {'schema': 'r1313-collection-config-v1', 'mode': 'offline_fixture',
              'run_root': str(root / 'run'), 'work_id': work_id, 'agent_id': owner,
              'coord_root': coord.root, 'assets_registry': str(REGISTRY), 'assets_registry_sha256': sha(REGISTRY),
              'source_contract': str(contract), 'source_contract_sha256': contract_sha,
              'budget': 16384, 'episode_limit': 1}
    path = root / 'config.json'
    write_json(path, config)
    return load_config(path), coord


def run_fixture(args):
    root = args.output or TASK / 'transport_fixtures' / (args.mode + '_' + str(time.time_ns()))
    config, coord = fixture_config(root, args.contract, args.contract_sha256)
    target, queue, _ = objects(config)
    initialize(target, 2)
    claim = queue.claim_next('fixture0', 0)
    if claim.episode is None or queue.claim_next('fixture1', 1).episode is not None:
        raise AssertionError('real episode queue did not enforce exclusivity')
    item = claim.episode
    queue.heartbeats.publish('fixture0', state='running', episode_id=item.episode_id)
    env, output = child_env(config, item, claim)
    env['GOOGLE_API_KEY'] = 'offline-fixture-no-network'
    os.environ.clear(); os.environ.update(env)
    receipt = read_json(item.payload['scene_receipt']['path'])
    input_path = root / 'row.json'
    write_json(input_path, item.payload['row'])
    scene, label = receipt['runtime_scene_id'], receipt['rendering_proof'][0]['label']
    steps = [
        ('find_frames_with_object', {'scene_id': scene, 'object_label': label, 'num_frames': '5'}),
        ('predict_2d_bounding_box', {'scene_id': scene, 'frame_index': 1, 'object_label': label}),
        ('predict_2d_points', {'scene_id': scene, 'frame_index': 1, 'query': label}),
        ('predict_2d_segmentation_masks', {'scene_id': scene, 'frame_index': 1, 'object_label': label}),
        ('predict_2d_segmentation_masks_video', {'scene_id': scene, 'object_label': label, 'frame_indices': [1, 17]}),
        ('get_world_3d_point_from_2d', {'scene_id': scene, 'frame_index': 1, 'x_norm': .5, 'y_norm': .5}),
        ('get_camera_pose', {'scene_id': scene, 'frame_index': 1}),
        ('verify_plan_pre_execution', {'plan_text': 'Fixture only: use the returned GT primitives.', 'question': 'Synthetic fixture check.'}),
        ('execute_python_code', {'code': "import numpy\nprint(load_dense('" + scene + "')['camera_poses'].shape[0])"}),
        ('verify_plan_post_execution', {'execution_summary': 'Fixture only: loaded32 authenticated camera poses.', 'question': 'Synthetic fixture check.'}),
    ]
    requests = []
    planner_index = 0
    names = set()
    delivered_tools = set()

    def transport(kw, *, verifier=False):
        nonlocal planner_index
        coord_guard(config)
        queue.heartbeats.publish('fixture0', state='running', episode_id=item.episode_id)
        requests.append(kw)
        if kw.get('model', '').removeprefix('models/') != 'gemini-3.1-pro-preview':
            raise AssertionError('GT perception attempted a separate VLM call')
        current = kw.get('config')
        model_config = current.model_dump(mode='json', exclude_none=True) if hasattr(current, 'model_dump') else current or {}
        for entry in model_config.get('tools', []):
            for function in entry.get('function_declarations', []):
                names.add(function['name'])
        for content in kw.get('contents', []):
            value = content.model_dump(mode='json', exclude_none=True) if hasattr(content, 'model_dump') else content
            for part in value.get('parts', []):
                if part.get('function_response'):
                    delivered_tools.add(part['function_response']['name'])
        if not verifier:
            planner_index += 1
        if args.mode == 'network_error':
            raise ValueError('offline injected transport error')
        usage = types.GenerateContentResponseUsageMetadata(prompt_token_count=100, candidates_token_count=10, total_token_count=120, thoughts_token_count=10)
        finish = 'MAX_TOKENS' if args.mode in ('empty_cap', 'malformed_cap') else 'STOP'
        thoughts = types.Part(text='Synthetic exposed fixture reasoning; not a real teacher answer.', thought=True)
        if verifier:
            parts = [thoughts, types.Part(text='VERDICT: PASS\nSynthetic transport fixture only.')]
        elif args.mode == 'gt_tools' and planner_index <= len(steps):
            name, arguments = steps[planner_index - 1]
            parts = [thoughts, types.Part(function_call=types.FunctionCall(name=name, args=arguments), thought_signature=b'offline-fixture-signature')]
        elif args.mode == 'empty_cap':
            parts = []
        elif args.mode == 'malformed_cap':
            function = types.FunctionCall.model_construct(name='get_frame_image', args='{"scene_id":')
            parts = [types.Part.model_construct(function_call=function)]
        else:
            parts = [thoughts, types.Part(text='<ANSWER>7</ANSWER>')]
        return types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(role='model', parts=parts), finish_reason=finish)],
            usage_metadata=usage, model_version=kw.get('model'), response_id='fixture-' + str(len(requests)))

    def response(self, *pos, **kw):
        return transport(kw)

    def stream(self, *pos, **kw):
        yield transport(kw, verifier=True)

    opened_paths = set()
    denied_effects = []
    def access_audit(event, values):
        if event == 'socket.connect':
            denied_effects.append('network')
            raise RuntimeError('offline fixture forbids real network transport')
        if event in ('os.remove', 'os.rmdir'):
            denied_effects.append('deletion')
            raise RuntimeError('offline fixture forbids deletion')
        if event == 'open' and isinstance(values[0], (str, bytes, os.PathLike)):
            path = os.fsdecode(values[0])
            if any(name in path for name in ('offline_labels', 'train50k_scene_reuse_labels', 'ANSWER_BANK', 'vsi_590k.jsonl')):
                denied_effects.append('answer_access')
                raise RuntimeError('runtime final-answer access is forbidden')
            if path.startswith('/'):
                opened_paths.add(path)
    sys.addaudithook(access_audit)
    sys.argv = ['run_experiment_r1313.py', '--row', str(input_path), '--output', str(output)]
    from pool_harness.pool import _HeartbeatPump
    isolation = {}
    with _HeartbeatPump(queue, 'fixture0', item.episode_id, 15):
        with patch.object(Models, 'generate_content', response), patch.object(Models, 'generate_content_stream', stream):
            import run_experiment_r1313 as runner
            from training_assets import runner_main
            if runner.agent_mod.__name__ != 'spatial_agent_r1313':
                raise AssertionError('runner imports the wrong round')
            assert not output.exists(), 'carrier import reserved or wrote the attempt before admission'
            runner_main(runner.run_one, HERE)
            call_count = len(requests)
            try:
                runner_main(runner.run_one, HERE)
            except FileExistsError:
                pass
            else:
                raise AssertionError('existing question/budget attempt was overwritten')
            assert len(requests) == call_count, 'repeat attempt reached the provider'
            if args.mode == 'gt_tools':
                for name, code in {'numpy': 'import numpy; print(7)', 'self': "import importlib; importlib.import_module('spatial_agent_r1313')",
                    'room': 'import tools_room_area', 'legacy': 'import amazing_tools',
                    'answers': "print(open('/data2/offline_labels/forbidden.json').read())"}.items():
                    isolation[name] = runner.agent_mod.execute_python_code.invoke({'code': code})
                assert isolation['numpy'].strip() == '7', isolation
                assert all('No module named' in isolation[name] for name in ('self', 'room', 'legacy')), isolation
                assert 'forbidden' in isolation['answers'].lower(), isolation
    trace_path = output / 'finalized' / item.payload['row']['id'] / ('trace_' + item.payload['row']['id'] + '.json')
    saved = read_json(trace_path)
    from census import mechanically_complete, archive_complete, recorded_cap, select_attempt, perceptual_evidence
    assert not denied_effects, denied_effects
    result = {'fixture_only': True, 'mode': args.mode, 'output': str(output), 'trace': pin(trace_path),
              'runtime_opened_paths': sorted(opened_paths), 'forbidden_runtime_effects': denied_effects,
              'sandbox_isolation': isolation, 'repeat_attempt_refused_before_provider': True,
              'native_requests': len(requests), 'planner_requests': planner_index, 'native_schema_tool_count': len(names),
              'tools_delivered_to_later_request': sorted(delivered_tools),
              'mechanically_complete': mechanically_complete(saved), 'archive_complete': archive_complete(trace_path),
              'recorded_cap': recorded_cap(saved), 'final_error': saved.get('error'),
              'initial_inline_rgb_count': saved['initial_visual_input']['frame_count'],
              'perception_evidence': perceptual_evidence(saved),
              'successful_gt_routes': sorted({r['tool'] for r in saved['tool_telemetry'] if r.get('event') == 'gt_perception' and r.get('status') == 'ok'})}
    attempt = {'trace': saved, 'budget': 16384, 'trace_path': str(trace_path), 'trace_sha256': sha(trace_path), 'archive_complete': result['archive_complete']}
    synthetic_row = {'question_type': 'object_counting', 'question': 'Synthetic fixture, not the source question.'}
    result['synthetic_acceptance'] = select_attempt(synthetic_row, '7', [attempt])
    result['synthetic_acceptance']['scope'] = 'fixture gold7 only; not correctness of the source membership question'
    if args.mode == 'gt_tools':
        from gt_tool_bindings import GT_TOOL_NAMES
        assert result['mechanically_complete'] and result['archive_complete'], result
        assert result['synthetic_acceptance']['accepted'], result
        assert set(result['successful_gt_routes']) == set(GT_TOOL_NAMES), result
        assert set(GT_TOOL_NAMES) <= delivered_tools and len(names) == 19, result
        assert not saved['native_google_tool_responses'], 'GT perception must not issue tool-VLM calls'
        assert len(saved['native_google_provider_calls']) == 2, 'both inherited SPLIT verifiers must be archived'
        tools = [m for m in saved['trace'] if m.get('role') == 'tool']
        assert next(m['content'] for m in tools if m.get('name') == 'execute_python_code').strip() == '32', tools
        changed = copy.deepcopy(saved); changed['trace'][-1]['content'] = '<ANSWER>8</ANSWER>'
        assert not mechanically_complete(changed), 'native final-answer mismatch was accepted'
        changed = copy.deepcopy(saved); changed['llm_usage']['planner']['calls_detail'][-1]['finish_reason'] = None
        assert not mechanically_complete(changed), 'missing finish reason was accepted'
        changed = copy.deepcopy(saved); changed['llm_usage']['planner']['calls_detail'].pop()
        assert not mechanically_complete(changed), 'provider/trace count mismatch was accepted'
    elif args.mode == 'zero_answer':
        assert result['mechanically_complete'] and result['archive_complete'], result
        assert not result['synthetic_acceptance']['accepted'] and not result['perception_evidence'], result
    elif args.mode in ('empty_cap', 'malformed_cap'):
        assert result['recorded_cap'] and not result['synthetic_acceptance']['accepted'], result
        assert result['synthetic_acceptance']['needs_topup'] and len(requests) == 1, result
    else:
        assert not result['mechanically_complete'] and not result['archive_complete'], result
        assert not result['synthetic_acceptance']['accepted'] and len(requests) == 1, result
    assert result['initial_inline_rgb_count'] == 0
    terminal = Path(config['run_root']) / 'terminals' / (item.episode_id + '.json')
    write_json(terminal, {'episode_id': item.episode_id, 'fixture_only': True, 'output': str(output)})
    queue.heartbeats.publish('fixture0', state='scan_exhausted', episode_id=None)
    queue.publish_exit_receipt('fixture0', reason='scan_exhausted', slot=0, return_code=0)
    assert queue.census()['valid_complete'] == 1
    cmd_complete(coord, SimpleNamespace(work_id=config['work_id'], result=str(root / 'PROOF.json')))
    result.update(collection_lease_completed=coord.is_completed(config['work_id']), episode_claim_preserved=claim.claim_path.exists())
    proof = write_json(root / 'PROOF.json', result)
    print(json.dumps({'proof': proof, 'fixture_only': True, 'mode': args.mode, 'checks_passed': True,
                      'synthetic_accepted': result['synthetic_acceptance']['accepted']}, indent=2))
    return proof


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--mode', choices=('gt_tools', 'zero_answer', 'empty_cap', 'malformed_cap', 'network_error'), default='gt_tools')
    run_fixture(parser.parse_args())


if __name__ == '__main__':
    main()
