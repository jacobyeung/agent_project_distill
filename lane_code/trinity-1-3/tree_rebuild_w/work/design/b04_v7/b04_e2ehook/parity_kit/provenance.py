"""Bind journal rows to their settings, load receipt, and installed runtime."""
from copy import deepcopy
import hashlib
from importlib import metadata, util
import json
import os
import platform
import sys

from parity_kit.common import LANE


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def receipt_digest(receipt):
    # Match common.write so the row pin authenticates the actual receipt bytes.
    raw = json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n'
    return hashlib.sha256(raw.encode()).hexdigest()


def runtime_identity(settings, device):
    import torch

    def version(name):
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None

    def presence(name, distribution):
        spec = util.find_spec(name)
        return dict(present=spec is not None, version=version(distribution),
                    origin=spec.origin if spec else None)

    roots = settings.get('env_roots', [])
    if not isinstance(roots, list) or any(not isinstance(p, str) for p in roots):
        raise ValueError('env_roots must be a list of paths')
    cuda = torch.device(device).type == 'cuda'
    return dict(python=dict(version=platform.python_version(), executable=sys.executable,
                            implementation=platform.python_implementation()),
                torch=dict(version=str(torch.__version__), cuda=torch.version.cuda),
                **{n: version(n) for n in ('transformers', 'numpy', 'scipy', 'torchvision')},
                fla=presence('fla', 'flash-linear-attention'),
                causal_conv1d=presence('causal_conv1d', 'causal-conv1d'),
                PYTHONPATH=os.environ.get('PYTHONPATH'), env_roots=roots,
                cuda_device_name=torch.cuda.get_device_name(device) if cuda else None)


def row_binding(receipt, load_sha):
    if receipt.get('schema') != 'parity-load-v2':
        raise ValueError('journal requires a parity-load-v2 receipt')
    arm = receipt['arm']
    if arm not in ('own_depth', 'scale_head') or receipt['inputs']['settings']['arm'] != arm:
        raise ValueError('receipt arm differs from settings')
    settings_sha = digest(receipt['inputs']['settings'])
    runtime_sha = digest(receipt['runtime_identity'])
    if (receipt['settings_sha256'] != settings_sha
            or receipt['runtime_identity_sha256'] != runtime_sha):
        raise ValueError('receipt settings or runtime digest differs')
    return dict(arm=arm, settings_sha256=settings_sha, load_receipt_sha256=load_sha,
                runtime_identity_sha256=runtime_sha)


def validate_rows(items, receipt, load_sha):
    binding = row_binding(receipt, load_sha)
    keys = [r['key'] for r in items]
    selected = receipt['keys']
    if (len(set(selected)) != len(selected) or len(set(keys)) != len(keys)
            or set(keys) - set(selected)):
        raise ValueError('journal keys do not match this selection')
    for row in items:
        for name, expected in binding.items():
            if row.get(name) != expected:
                raise ValueError('journal provenance differs: ' + name)
    return binding


def comparison_identity(receipt):
    """Only the selected keys and their derived frame counts may vary by partition."""
    result = deepcopy(receipt)
    result.pop('keys')
    counts = result.pop('dense_frame_counts')
    if set(counts) != set(receipt['keys']):
        raise ValueError('receipt frame-count keys differ from selection')
    result.pop('settings_sha256')
    result['inputs']['settings'].pop('keys', None)
    return result


def native_kernel_comparison(runtime):
    log = LANE / 'work/n13/ret/logs/worker.log'
    with log.open() as stream:
        for line in stream:
            if '"native_runtime_bindings"' not in line:
                continue
            event = json.loads(line)
            if event.get('event') == 'native_runtime_bindings':
                break
        else:
            raise ValueError('job 170056 native runtime bindings missing')
    modules = sorted({binding['module'] for layer in event['layers']
                      for binding in layer['bindings'].values() if binding})
    native_fla = any(m.startswith('fla.') for m in modules)
    current_fla = runtime['fla']
    differs = native_fla != current_fla['present']
    return dict(job=170056, source=str(log), event='native_runtime_bindings',
                native_fla=native_fla, native_binding_modules=modules,
                current_fla=current_fla, fla_state_differs=differs,
                camera_agreement_label='within noise' if differs else 'call-text agreement',
                interpretation=('Kernel states differ; exact call strings do not establish bit equality.'
                                if differs else 'Exact call strings do not establish tensor bit equality.'))
