#!/usr/bin/env python3
"""Assemble a kit directory: family code, CONFIG.json, PINS.json and the job-side package.

    pack.py --code DIR --config CONFIG.json --out KIT [--code-prefix code] [--package lib]
            [--inputs DIR] [--remote REMOTE_ENTRIES.json] [--commit SHA] [--source-seal DIGEST]

The family code is copied under KIT/<code-prefix>/, files of --inputs under KIT/inputs/, and the
job-side modules (util, stage, ret) into KIT/<package>/, which they import relatively. The
library's own name never ships. REMOTE_ENTRIES.json is a list of complete pin entries (kind gcs
or orchard) whose bytes and sha256 their producer recorded; they join the manifest as written.
CONFIG.json gains kit_pins_sha256 and job.package. The kit must pass the opacity check and the
single-place invariant, or pack exits 1 and leaves the kit for inspection. Cluster side;
Python 3.6-safe, standard library only.
"""
import argparse
import json
import os
import re
import shutil
import sys

if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import orchkit  # noqa: F401
    __package__ = 'orchkit'  # noqa: A001
from . import anon, pins, util  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
JOB_SIDE = ('util.py', 'stage.py', 'ret.py')
PACKAGE = re.compile(r'^[a-z][a-z0-9_]{0,15}$')


class PackError(ValueError):
    pass


def _copy_tree(source, dest, prefix, role, spec):
    for current, dirs, files in os.walk(source):
        dirs[:] = sorted(name for name in dirs if name != '__pycache__')
        for name in sorted(files):
            path = os.path.join(current, name)
            if os.path.islink(path):
                raise PackError('refusing a symlink: %s' % path)
            if name.endswith(('.pyc', '.pyo')):
                continue
            rel = '/'.join([prefix, os.path.relpath(path, source).replace(os.sep, '/')])
            target = os.path.join(dest, rel)
            if not os.path.isdir(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            shutil.copyfile(path, target)
            shutil.copymode(path, target)
            spec.append({'role': role, 'logical_path': rel})


def pack(code, config_path, out, code_prefix='code', package='lib', inputs=None, remote=None,
         commit=None, source_seal=None, rules=None):
    out = os.path.abspath(out)
    if os.path.lexists(out):
        raise PackError('refusing to reuse %s' % out)
    rules = rules or anon.load_rules()
    if not PACKAGE.match(package) or package == 'orchkit' or anon.scan_text('package', package,
                                                                             rules, 'name'):
        raise PackError('package name %r is not allowed' % package)
    if code_prefix in (package, 'inputs') or not PACKAGE.match(code_prefix):
        raise PackError('code prefix %r is not allowed' % code_prefix)
    os.makedirs(out)
    spec = []
    _copy_tree(code, out, code_prefix, 'code', spec)
    if inputs:
        _copy_tree(inputs, out, 'inputs', 'input', spec)
    lib = os.path.join(out, package)
    os.makedirs(lib)
    with open(os.path.join(lib, '__init__.py'), 'wb'):
        pass
    spec.append({'role': 'code', 'logical_path': package + '/__init__.py'})
    for name in JOB_SIDE:
        shutil.copyfile(os.path.join(HERE, name), os.path.join(lib, name))
        spec.append({'role': 'code', 'logical_path': '%s/%s' % (package, name)})
    manifest = pins.build(out, {'commit': commit, 'source_seal': source_seal, 'entries': spec})
    if remote:
        extra = util.read_json(remote)
        if not isinstance(extra, list):
            raise PackError('--remote holds a list of pin entries')
        for entry in extra:
            if entry.get('source', {}).get('kind') not in ('gcs', 'orchard'):
                raise PackError('a remote entry must be gcs or orchard: %s' % entry.get('logical_path'))
        manifest['entries'] = sorted(manifest['entries'] + extra,
                                     key=lambda row: row['logical_path'])
        pins.validate_manifest(manifest)
    util.write_json(os.path.join(out, 'PINS.json'), manifest)
    config = util.read_json(config_path)
    config['kit_pins_sha256'] = pins.kit_identity(manifest)
    config.setdefault('job', {})['package'] = package
    util.write_json(os.path.join(out, 'CONFIG.json'), config)
    hits = anon.scan_tree(out, rules)
    copies = pins.check_single_place(out)
    summary = {'kit': out, 'kit_pins_sha256': config['kit_pins_sha256'],
               'config_sha256': util.sha256_file(os.path.join(out, 'CONFIG.json'))[0],
               'entries': len(manifest['entries']), 'opacity_hits': hits,
               'single_place_violations': copies}
    if hits or copies:
        raise PackError('kit refused: %s' % json.dumps(summary, sort_keys=True)[:3000])
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--code', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--code-prefix', default='code')
    parser.add_argument('--package', default='lib')
    parser.add_argument('--inputs')
    parser.add_argument('--remote')
    parser.add_argument('--commit')
    parser.add_argument('--source-seal')
    args = parser.parse_args(argv)
    try:
        summary = pack(args.code, args.config, args.out, args.code_prefix, args.package,
                       args.inputs, args.remote, args.commit, args.source_seal)
    except (PackError, pins.PinError, OSError, ValueError) as err:
        sys.stderr.write('pack: %s\n' % err)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
