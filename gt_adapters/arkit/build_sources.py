"""Derive the r1313 source files from authenticated frozen donors, without overwrites."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAINING = Path('/home/jjyeung/agent_project/agent/rounds/candidates/r1311_vsi_distill_native_summary')
GT = Path('/data2/jjyeung/agent_project_data/r1298_req229_common_gt/v14/cells/gt_gt_high/package')
GT_CONTRACT_SHA = '0027aa304dd8255eb9ead6d6e7fb473fbba45fd12b667febf6a70634806972a1'
TASK = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313')
UNCHANGED = ('native_google_telemetry.py', 'reference_native_tool_telemetry.py',
             'provider_history.py', 'trace_archive.py', 'training_policy.py',
             'training_publication.py', 'nondeleting_lifecycle.py',
             'pool_harness/__init__.py', 'pool_harness/atomicfs.py', 'pool_harness/state.py',
             'pool_harness/pool.py', 'pool_harness/telemetry.py', 'pool_harness/watchdog.py',
             'test_trace_archive.py', 'test_collector.py')


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def verify_donors():
    assert sha(GT / 'contract.json') == GT_CONTRACT_SHA, 'GT donor contract drift'
    assert sha(TASK / 'DESIGN_REVIEW.md') == '0f8fc6056e107c66fe9ecfc87e1a32d64d7402b0b3cf1ce3e62eaedf71a44e13'
    assert sha(TASK / 'DESIGN_BRIEF.md') == 'a583b1ca0402ce63523de7e92c56afd543905db04b14084eb7aaaa5d30c90ab1'
    assert '## Verdict: PASS' in (TASK / 'DESIGN_REVIEW.md').read_text()
    result = {}
    for root in (TRAINING, GT):
        contract = json.loads((root / 'contract.json').read_text())
        files = contract['runtime_files']
        for name, digest in files.items():
            if sha(root / name) != digest:
                raise ValueError(f'frozen donor drift: {root / name}')
        result[str(root)] = {'contract_sha256': sha(root / 'contract.json'), 'files': files}
    return result


def segment(text, node):
    start = min([node.lineno] + [d.lineno for d in getattr(node, 'decorator_list', [])])
    return ''.join(text.splitlines(keepends=True)[start - 1:node.end_lineno])


def selected_nodes(text, names):
    return '\n\n'.join(segment(text, n) for n in ast.parse(text).body if getattr(n, 'name', None) in names) + '\n'


def derived_sources():
    outputs = {name: (TRAINING / name).read_text() for name in UNCHANGED}
    for name in ('collect.py', 'training_assets.py', 'census.py', 'spatial_agent_r1311.py', 'run_experiment_r1311.py'):
        content = (TRAINING / name).read_text().replace('r1311', 'r1313').replace('1311.txt', '1313.txt')
        if name in ('collect.py', 'training_assets.py'):
            content = content.replace('R1308', 'R1313').replace('r1308', 'r1313').replace("'round':1311", "'round':1313")
        outputs[name.replace('r1311', 'r1313')] = content
    outputs['prompt_base_1313.txt'] = (TRAINING / 'prompt_base_1311.txt').read_text()
    text = (GT / 'gt_geometry_provider_r1298.py').read_text()
    nodes = {getattr(n, 'name', ''): n for n in ast.parse(text).body}
    constants = '\n'.join(segment(text, n) for n in ast.parse(text).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('MIN_DEPTH_M', '_PLY_DTYPES') for t in n.targets))
    outputs['donor_geometry.py'] = ('from __future__ import annotations\nimport hashlib\nfrom pathlib import Path\nfrom typing import Any\nimport numpy as np\nfrom scipy.ndimage import minimum_filter\n\n' + constants + '\n\n' + selected_nodes(text, {'GTProviderError', 'sha256_file', '_require_file', '_load_vertices'}) + '\nclass Renderer:\n' + '\n'.join(segment(text, n) for n in nodes['R804GTGeometryProvider'].body if getattr(n, 'name', '') in ('_pose', '_render')) + '\n')
    text = (GT / 'gt_grounding_provider_r1298.py').read_text()
    chunks = []
    for node in ast.parse(text).body:
        name = getattr(node, 'name', None)
        if isinstance(node, ast.ImportFrom) and node.module == 'gt_geometry_provider_r1298':
            chunks.append('from donor_geometry import GTProviderError, _require_file, sha256_file\n')
        elif isinstance(node, ast.ImportFrom) and node.module == 'run_integrity':
            chunks.append('from gt_errors import UnmappedGroundingLabel\n')
        elif isinstance(node, ast.ImportFrom) and node.module == 'gt_label_matcher_r1298':
            chunks.append('from gt_label_matcher_r1313 import match_label as _LOCAL_MATCH_LABEL\n')
        elif name == 'REQ113GTGroundingProvider':
            chunks.append('class REQ113GTGroundingProvider:\n' + '\n'.join(segment(text, method) for method in node.body if isinstance(method, ast.FunctionDef) and method.name not in ('__init__', '_camera')))
        elif name == 'provider':
            continue
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id in ('GROUNDING_ASSET_MANIFEST', '_PROVIDER', '_PROVIDER_LOCK', '__all__') for t in targets):
                continue
            chunks.append(segment(text, node))
        else:
            chunks.append(segment(text, node))
    outputs['donor_grounding.py'] = '\n\n'.join(chunks) + '\n'
    outputs['gt_label_matcher_r1313.py'] = (GT / 'gt_label_matcher_r1298.py').read_text()
    text = (GT / 'frame_alignment.py').read_text()
    outputs['frame_alignment.py'] = 'import numpy as np\n\n' + selected_nodes(text, {'transform_geometry', 'canonical_geometry'})
    text = (GT / 'run_integrity.py').read_text()
    outputs['gt_errors.py'] = 'import json\nfrom functools import wraps\n\n' + selected_nodes(text, {'UnmappedGroundingLabel', 'grounding_refusal'})
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    donors = verify_donors()
    if not args.receipt.resolve().is_relative_to(TASK):
        raise ValueError('source derivation receipts belong under the task root')
    if args.verify_only:
        outputs = {}
    else:
        outputs = derived_sources()
        for name, content in outputs.items():
            path = HERE / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                if path.read_text() != content:
                    raise ValueError(f'refusing to overwrite derived source: {name}')
            else:
                with path.open('x') as handle:
                    handle.write(content)
    receipt = {'schema': 'r1313-source-derivation-v1', 'donors': donors,
               'generated': {name: sha(HERE / name) for name in outputs},
               'scope': 'training collector; donor projection kernels without evaluation manifests or membership assertions'}
    with args.receipt.open('x') as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps({'verified_donors': len(donors), 'generated_files': len(outputs), 'receipt': str(args.receipt)}))


if __name__ == '__main__':
    main()
