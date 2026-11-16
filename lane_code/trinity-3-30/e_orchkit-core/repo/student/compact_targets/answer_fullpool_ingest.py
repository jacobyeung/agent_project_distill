"""Answer ingestion from compact_v25_ingest.py at 5411443.

Reuse trace authentication and RGB sampling without rendering reasoning targets.
Run roots are explicit; collector files are only read. Both collections retain
r1313 receipt schema/round even when their directory is named r1316.
"""
import re
from collections import defaultdict
from pathlib import Path
from . import compact_counted_v1 as v1
from student.landing.student_pilot.admission import native_final
from student.landing.student_pilot.detailed_audit import messages, provider_matches
MODEL = 'gemini-3.1-pro-preview'
SCHEMA = 'compact-v2.5-authenticated-trace-source-v1'
FORBIDDEN_ROOT = Path('/home/jjyeung/agent_project_distill')

def require(condition, reason, detail=''):
    if not condition:
        raise v1.Deferral(reason, detail)


def allowed_path(path, run_root, trace_path=None):
    path = Path(path)
    require(path.is_absolute(), 'ingest_relative_path', str(path))
    require(not path.is_relative_to(FORBIDDEN_ROOT), 'ingest_forbidden_path', str(path))
    resolved = v1.safe_path(path)
    require(not resolved.is_relative_to(FORBIDDEN_ROOT), 'ingest_forbidden_path', str(path))
    require(not resolved.is_relative_to(Path(run_root).resolve()) or str(path) == trace_path, 'ingest_unlisted_run_path', str(path))
    return resolved


def authenticate_trace(decision, payload):
    require(v1.sha256_bytes(payload) == decision.get('trace_sha256'), 'source_hash_mismatch', decision.get('trace_path', ''))
    require(all(decision.get(key) is True for key in ('accepted', 'answer_correct', 'mechanically_complete', 'has_perceptual_evidence')),
            'ingest_not_strict_accepted', decision.get('id', ''))
    raw = v1.decode_json(payload)
    receipt = raw.get('run_receipt') or {}
    inputs = receipt.get('input_rows') or []
    require(len(inputs) == 1 and isinstance(inputs[0], dict), 'ingest_identity_mismatch', 'One authenticated input row is required')
    row = inputs[0]
    require(row.get('id') == decision['id'] == raw.get('question_id') and all(raw.get(key) == row.get(key) for key in ('scene_name', 'question_type', 'question')),
            'ingest_identity_mismatch', decision['id'])
    require(not any(raw.get(key) for key in ('error', 'budget_terminal', 'orphan_tool_drop')), 'ingest_incomplete_trace', decision['id'])
    require(receipt.get('schema') == 'r1313-training-episode-v1' and receipt.get('round') == 1313 and receipt.get('fixture_only') is False,
            'ingest_native_provenance', 'Not a production r1313 trace')
    require(receipt.get('planner_output_budget_tokens') == decision.get('chosen_budget') and re.fullmatch('[0-9a-f]{64}', receipt.get('membership_sha256', '')),
            'ingest_native_provenance', 'Budget or membership binding is absent')
    require(receipt.get('selected_frames_sha256') == receipt.get('scene_receipt', {}).get('sha256') and receipt.get('student_inputs', {}).get('modality') == 'question_and_RGB_only',
            'ingest_native_provenance', 'RGB receipt or modality changed')
    transcript, _ = messages(raw)
    calls, returns = {}, defaultdict(list)
    for index, message in enumerate(transcript):
        if message.get('role', '').lower() in ('ai', 'aimessage'):
            usage = message.get('usage_metadata')
            require(provider_matches(message) and isinstance(usage, dict) and usage == message['raw_response'].get('usage_metadata')
                    and all(type(usage.get(key)) is int and usage[key] >= 0 for key in ('input_tokens', 'output_tokens', 'total_tokens'))
                    and message.get('response_metadata', {}).get('finish_reason') == 'STOP'
                    and message.get('response_metadata', {}).get('model_name') == MODEL,
                    'ingest_native_provenance', f'{decision["id"]}: message {index}')
        for call in message.get('tool_calls') or []:
            require(isinstance(call.get('id'), str) and call['id'] not in calls, 'ingest_duplicate_call', decision['id'])
            calls[call['id']] = (index, call)
        if message.get('role', '').lower() in ('tool', 'toolmessage'):
            call_index, call = calls.get(message.get('tool_call_id'), (-1, {}))
            require(call_index < index and call.get('name') == message.get('name'), 'ingest_unbound_tool_return', decision['id'])
            if message.get('content'):
                returns[message['tool_call_id']].append(index)
    require(bool(decision.get('perceptual_evidence')), 'ingest_perceptual_evidence', decision['id'])
    for evidence in decision['perceptual_evidence']:
        call_index, call = calls.get(evidence.get('tool_call_id'), (-1, {}))
        received = returns.get(evidence.get('tool_call_id'), [])
        require(call.get('name') == evidence.get('tool') and len(received) == 1 and call_index < received[0]
                and any(message.get('role', '').lower() in ('ai', 'aimessage') for message in transcript[received[0] + 1:]),
                'ingest_perceptual_evidence', decision['id'])
    final = native_final(raw)
    require(final['message_index'] == len(transcript) - 1, 'ingest_native_provenance', 'The final answer is not terminal')
    return raw, row, final


def rgb_metadata(path, digest, run_root, check_frame):
    path = allowed_path(path, run_root)
    receipt = v1.decode_json(v1.checked_payload(path, digest))
    frames = receipt.get('frames')
    require(isinstance(frames, list) and len(frames) == 32, 'ingest_rgb_schema', str(path))
    for frame in frames:
        frame_path = allowed_path(frame['path'], run_root)
        check_frame({'path': str(frame_path), 'sha256': frame['sha256']})
    video = receipt.get('video') or {}
    require(isinstance(video.get('fps'), (int, float)) and video['fps'] > 0, 'ingest_rgb_schema', 'Missing original FPS')
    count = video.get('decoded_frame_count', video.get('total_num_frames', video.get('num_frames', video.get('frame_count'))))
    require(type(count) is int and count > max(frame['ordinal'] for frame in frames), 'ingest_rgb_schema', 'Missing original frame count')
    return {'frames': [{'path': frame['path'], 'sha256': frame['sha256']} for frame in frames],
            'frame_indices': [frame['ordinal'] for frame in frames], 'timestamps': [frame['timestamp_sec'] for frame in frames],
            'fps': video['fps'], 'total_num_frames': count}

