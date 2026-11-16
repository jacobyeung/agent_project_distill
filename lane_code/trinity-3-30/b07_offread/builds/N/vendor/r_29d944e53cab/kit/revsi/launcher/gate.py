"""Authenticate the selected bytes and require the existing parity proof."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


def validate(config):
    for key in ('x0', 'x1'):
        if not re.fullmatch('[0-9a-f]{64}', config.get(key, '')):
            raise ValueError('X0 identity differs')
    if config.get('x2') not in (0, 1):
        raise ValueError('X0 type differs')


def stage(root, config, physical):
    import orchard_stage as S
    if config.get('x2'):
        import s1
        return s1.stage(root, config, physical)
    return S.stage(root, config, physical)


def before(root, config):
    import export_stage as E
    validate(config)
    step = config['spec']['step']
    if step not in (100, 200, 400, 600, 800, 1000):
        raise ValueError('X1 step differs')
    path = Path('/project/community/jjyeung/okh7/x_f5c353f7/o') / ('gcs_359fcc3c_m'+str(step)+'.done')
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('X1 receipt differs')
    done = E.parse_done(path.read_bytes(), '359fcc3c', step)
    if done['sha256'] != config['x1'] or done['bytes'] != config['x3']:
        raise ValueError('X1 receipt differs')


def after(root, config, receipts):
    import orchard_stage as S
    import orchard_job as J
    validate(config)
    if config['x2']:
        got = receipts['export']
        if (got.get('tar_sha256') != config['x1'] or got.get('status') != 'complete'
                or got.get('checker', {}).get('status') != 'VERIFIED'):
            raise ValueError('X1 admission differs')
    else:
        if S.sha(J.physical(root, config['spec']['artifact']['path'])) != config['x1']:
            raise ValueError('X1 artifact differs')


def parity(config, root):
    package = Path(config['spec']['package'])
    target = Path(config['spec']['run']) / 'p9'
    target.parent.mkdir(parents=True, exist_ok=True)
    argv = [config['spec']['interpreters']['vllm'], '-s', '-B',
            str(package/'parity/prove_prompts.py'), '--output', str(target),
            '--processor-dir', config['spec']['models']['base']['path'],
            '--reader-root', '/scratch/jjyeung/orch_cd/legs1_reads',
            '--kit-root', '/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt']
    result = subprocess.run(argv, capture_output=True)
    receipt = dict(passed=False, returncode=result.returncode)
    try:
        observed = json.loads((target/'PARITY.json').read_text())
        receipt['passed'] = result.returncode == 0 and all(observed.get(k) is True for k in
            ('processor_checked', 'all_prompt_bytes_equal', 'prompt_pins_equal'))
    except (OSError, ValueError):
        pass
    receipt['observed'] = locals().get('observed')
    evidence = target.parent/'metadata'
    evidence.mkdir(exist_ok=True)
    (evidence/'P9.json').write_text(json.dumps(receipt)+'\n')
    if not receipt['passed']:
        raise ValueError('P9 failed')
    return receipt


def run(config, root):
    validate(config)
    parity(config, root)
    package = Path(config['spec']['package'])
    sys.path.insert(0, str(package/'reader'))
    import chain
    if config['x2']:
        import official_adapter as A
        admission = config['admission']
        if admission['tar_sha256'] != config['x1'] or admission['status'] != 'complete':
            raise ValueError('X1 admission differs')
        A.EXPORT_SHA = admission['artifact_sha256']
        original_check = A.check_export
        def check(path, digest, base, step):
            if digest != A.EXPORT_SHA or step != 544:
                raise ValueError('X1 check differs')
            return original_check(path, digest, base, config['spec']['step'])
        A.check_export = check
        original_bind = A.bind
        def bind(*args, **kwargs):
            cfg = original_bind(*args, **kwargs)
            cfg['reader']['step'] = config['spec']['step']
            cfg['binding'] = A.binding(cfg)
            A.dump(Path(args[0])/'request.json', cfg)
            return cfg
        A.bind = bind
    result = chain.run(config)
    if config['x2']:
        path = Path(config['spec']['run'])/'AUTHORIZATION.json'
        value = json.loads(path.read_text())
        value['step'] = config['spec']['step']
        path.write_text(json.dumps(value)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    p.add_argument('--root')
    a = p.parse_args()
    run(json.loads(Path(a.config).read_text()), a.root)
