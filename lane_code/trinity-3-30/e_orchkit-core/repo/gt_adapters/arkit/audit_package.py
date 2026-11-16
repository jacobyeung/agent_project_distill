"""Seal and verify the exact r1313 package; all generated authorities stay off Git."""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
from gt_scene_assets import DATA_ROOT, data_path, pin, read_json, sha, verify, write_json

HERE = Path(__file__).resolve().parent
TASK = DATA_ROOT / 'runtime_control/gt_teacher_r1313'
RUNTIME_FILES = frozenset('''collect.py coordination.py donor_geometry.py donor_grounding.py episode_custody.py
frame_alignment.py gt_errors.py gt_label_matcher_r1313.py gt_scene_assets.py gt_tool_bindings.py gt_training_r1313.py
native_google_telemetry.py nondeleting_lifecycle.py provider_history.py reference_native_tool_telemetry.py
run_experiment_r1313.py spatial_agent_r1313.py trace_archive.py training_assets.py training_policy.py
training_publication.py transport_admission.py audit_package.py prompt_base_1313.txt
pool_harness/__init__.py pool_harness/atomicfs.py pool_harness/state.py pool_harness/pool.py
pool_harness/telemetry.py pool_harness/watchdog.py'''.split())
OFFLINE_FILES = frozenset('''README.md build_sources.py census.py prepare_gt_scene.py test_collector.py
test_trace_archive.py test_gt_tools.py test_runner_transport.py test_admission.py validate_package.py
arkit_source.py arkit_alignment.py prepare_arkit_scene.py prepare_corpus.py arkit_fixtures.py test_arkit_adapter.py'''.split())
REQUIRED_FILES = RUNTIME_FILES | OFFLINE_FILES
DEPENDENCIES = ('numpy', 'scipy', 'opencv-python', 'Pillow', 'google-genai', 'langchain',
                'langchain-core', 'langchain-google-genai', 'langchain-openai', 'langgraph', 'scikit-learn', 'matplotlib')
ENVIRONMENT = {
    'APPEAR_EVIDENCE': None, 'CI3D': '0', 'CI3D_GUARD': None, 'DENSE_DIR': None,
    'DG_GATE': None, 'DISABLE_SALVAGE': None, 'EMPTYAI_RETRY': None, 'FLOOR_REL_Z': None,
    'FORCE_DENSE': None, 'FORCE_PC_SOURCE': 'g3t_scaled', 'G1_GATE': None, 'G2_COUNT_FIX': None,
    'G3T_METRIC': None, 'G3T_SCALE_JSON': None, 'G3T_UNIK3D_SCALED_DENSE_DIR': None,
    'GP_NATIVE': '1', 'IDANCHOR': None, 'MC_EXTENT': None, 'NF5_CANNOT_LINK': None,
    'NF6_EARLIEST_VISIBLE': None, 'NF7_GROUNDING_UNION': None, 'NV_CACHE_CONTROL': None,
    'NV_INFERENCE_API_KEY': None, 'NV_INFERENCE_BASE_URL': None, 'NV_INFERENCE_DATA_CLASSIFICATION': None,
    'NV_PLANNER_MODEL': 'gemini-3.1-pro-preview', 'NV_RETRY_ATTEMPTS': '3', 'NV_TIMEOUT_SECONDS': None,
    'NV_VERIFIER_MODEL': 'gemini-3.1-pro-preview', 'R306_ALLOW_LEGACY_SCALE_ENVS': None,
    'R740_CONSUMPTION_EPISODE': None, 'R740_CONSUMPTION_EVENT_FILE': None, 'ROOM_POLY': '0',
    'SALVAGE_NUMGUARD': None, 'SCALE_CORRECTION_JSON': None, 'STEP_CAP': None,
    'STR3_ARBITER': None, 'STR7_TOOL': None, 'TOOL_VLM_MODEL': 'gemini-3.5-flash',
    'PYTHONDONTWRITEBYTECODE': '1', 'HF_HOME': '/data2/jjyeung/cache/huggingface',
    'HUGGINGFACE_HUB_CACHE': '/data2/jjyeung/cache/huggingface/hub',
    'TORCH_HOME': '/data2/jjyeung/cache/torch', 'PIP_CACHE_DIR': '/data2/jjyeung/cache/pip',
}


def source_census(root=HERE):
    root = Path(root)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != REQUIRED_FILES:
        raise ValueError(f'package file census drift: missing={sorted(REQUIRED_FILES - actual)}, unexpected={sorted(actual - REQUIRED_FILES)}')
    for relative in sorted(REQUIRED_FILES):
        path = root / relative
        if path.is_symlink():
            raise ValueError('source symlinks are not admitted')
        if path.suffix == '.py':
            compile(path.read_text(), str(path), 'exec')
    return {name: sha(root / name) for name in sorted(REQUIRED_FILES)}


def verify_contract(path, digest, *, root=HERE):
    path = data_path(path)
    if sha(path) != digest:
        raise ValueError('source contract digest drift')
    contract = read_json(path)
    if contract.get('schema') != 'r1313-vsi590k-gt-collector-v1' or contract.get('round') != 1313:
        raise ValueError('wrong training source contract')
    if contract.get('runtime_files') != sorted(RUNTIME_FILES) or contract.get('offline_files') != sorted(OFFLINE_FILES):
        raise ValueError('source closure census differs from the executable authority')
    if contract.get('source_files') != source_census(root):
        raise ValueError('source bytes differ from the admitted contract')
    if contract.get('effective_environment') != ENVIRONMENT:
        raise ValueError('effective teacher settings drift')
    from training_assets import MEMBERSHIP, MEMBERSHIP_SHA
    if contract.get('membership') != {'path': str(MEMBERSHIP), 'sha256': MEMBERSHIP_SHA} or sha(MEMBERSHIP) != MEMBERSHIP_SHA:
        raise ValueError('training membership authority drift')
    if contract.get('model') != {'requested_id': 'gemini-3.1-pro-preview'}:
        raise ValueError('teacher model identity drift')
    return contract


def derivation_checks():
    from build_sources import TRAINING, GT, UNCHANGED, derived_sources, verify_donors, segment
    donors = verify_donors()
    unchanged = list(UNCHANGED) + ['episode_custody.py', 'transport_admission.py']
    for name in unchanged:
        if sha(HERE / name) != sha(TRAINING / name):
            raise ValueError('inherited archival/pool source changed: ' + name)
    generated = derived_sources()
    kernels = ('donor_geometry.py', 'donor_grounding.py', 'frame_alignment.py', 'gt_errors.py', 'gt_label_matcher_r1313.py')
    for name in kernels:
        if (HERE / name).read_text() != generated[name]:
            raise ValueError('donor projection kernel changed: ' + name)
    if sha(HERE / 'prompt_base_1313.txt') != sha(TRAINING / 'prompt_base_1311.txt'):
        raise ValueError('structural prompt change is outside this adapter')
    donor_text, local_text = (GT / 'coord.py').read_text(), (HERE / 'coordination.py').read_text()
    donor_nodes = {n.name: n for n in ast.parse(donor_text).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    local_nodes = {n.name: n for n in ast.parse(local_text).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    for name in ('now_iso', 'write_json', 'read_json', 'validate_work_id', 'Coord', 'do_claim', 'move_lease', 'cmd_heartbeat', 'cmd_complete'):
        expected = segment(donor_text, donor_nodes[name])
        if name == 'do_claim':
            expected = expected.replace('git("rev-parse", "--abbrev-ref", "HEAD")', 'None').replace('git("rev-parse", "--short", "HEAD")', 'None')
        if ast.dump(ast.parse(expected), include_attributes=False) != ast.dump(ast.parse(segment(local_text, local_nodes[name])), include_attributes=False):
            raise ValueError('nondeleting donor lease operation drift: ' + name)
    return {'donors': donors, 'unchanged_training_files': unchanged, 'unchanged_GT_kernels': list(kernels),
            'coordination_delta': 'donor nondeleting lease functions; explicit AGENT_ID; branch/commit metadata null, no Git subprocesses',
            'routing_delta': 'donor find_frames/boxes/points/segment_frame/segment_video replace VLM perception; same literal19-tool roster',
            'geometry_delta': 'official aligned_pose/intrinsic; sourceK/3, identity target crop; GT-valid support, canonical_geometry scale1'}


def seal(output):
    derivation = derivation_checks()
    from training_assets import MEMBERSHIP, MEMBERSHIP_SHA
    dependencies = {}
    for name in DEPENDENCIES:
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            if name != 'opencv-python':
                raise
            dependencies['opencv-python-headless'] = importlib.metadata.version('opencv-python-headless')
    contract = {'schema': 'r1313-vsi590k-gt-collector-v1', 'round': 1313, 'arm': 'teacher_training_GT',
                'model': {'requested_id': 'gemini-3.1-pro-preview'}, 'effective_environment': ENVIRONMENT,
                'source_files': source_census(), 'runtime_files': sorted(RUNTIME_FILES), 'offline_files': sorted(OFFLINE_FILES),
                'source_root': str(HERE), 'parent_reported_base_commit': '5477aea303647ad7b89bc21ff2421543d01c1868',
                'membership': {'path': str(MEMBERSHIP), 'sha256': MEMBERSHIP_SHA},
                'design_authorities': {name: pin(TASK / name) for name in ('DESIGN_BRIEF.md', 'DESIGN_REVIEW.md', 'CONTROLLING_USER_CLARIFICATION.md', 'GT_PERCEPTION_AMENDMENT.md')},
                'dependencies': dependencies, 'derivation': derivation,
                'budget_policy': '16384 initial; only offline incorrect-and-capped selection permits one32768 attempt',
                'teacher_inputs': 'text/question/choices initially; GT tool observations; no required inlineRGB',
                'student_inputs': 'question and authenticated32RGB only; no GT at benchmark inference',
                'runtime_data': 'answer-free50k membership, immutable prepared scene receipts/assets, attempt archives, claims and collection lease',
                'offline_label_boundary': 'census.py alone loads the pinned offline labels; providers accept only scene/frame/label',
                'default_run_root': str(DATA_ROOT / 'collection_gt_r1313')}
    spec = write_json(output, contract)
    verify_contract(spec['path'], spec['sha256'])
    print(json.dumps(spec, sort_keys=True))
    return spec


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('seal'); build.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('verify'); check.add_argument('--contract', type=Path, required=True); check.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    if args.command == 'seal':
        seal(args.output)
    else:
        contract = verify_contract(args.contract, args.contract_sha256)
        print(json.dumps({'verified': True, 'source_files': len(contract['source_files']), 'round': 1313}))


if __name__ == '__main__':
    main()
