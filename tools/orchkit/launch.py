#!/usr/bin/env python3
"""The one launcher: a new job is a new config, never a fork of this file.

    launch.py prepare --kit KIT --config CONFIG.json --out PREP/ --lane L --meaning TEXT
                      --checkout EPOCH_CHECKOUT (on /scratch)
                      [--dryrun REPORT.json | --no-dryrun-reason TEXT] [--sessions SESSIONS.json]
    launch.py submit  --prep PREP/ --go GO_FILE [--execute]
    launch.py status  --prep PREP/ [--execute]
    launch.py fetch   --prep PREP/ --dest DIR [--execute]

prepare contacts nothing: it validates the config against the header and family schemas, verifies
the pins, requires a PASS dry-run report whose kit_pins_sha256 and config_sha256 equal the kit's
(or a recorded --no-dryrun-reason), runs the opacity check on every byte bound for the batch host,
records the epoch checkout's commit, renders the batch script from templates/job.sh.tmpl, mints the
job name, appends the ledger row "minted" and writes PREP/SUBMIT.json with the exact argv.

submit refuses unless the GO file names the token, refuses when the ledger shows one of our jobs
live on a one-job partition (unless the GO file says "queue behind" and names that job), prints the
command, and runs it through ORCHKIT_OSSH only with --execute. The submission script checks the
home quota and the pool's free space on the batch host against CONFIG.budgets in the same call,
before sbatch, and submits nothing when either is short. status and fetch are thin wrappers over the
same transport. Python 3.6-safe, standard library only; runs on the cluster side.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tarfile
import tempfile

if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import orchkit  # noqa: F401
    __package__ = 'orchkit'  # noqa: A001
from . import anon, ledger, pins, stage, util  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'templates', 'job.sh.tmpl')
SCHEMAS = os.path.join(HERE, 'schema')
PREFIX = 'a15_cot_ap'
TOKEN = re.compile(r'^[0-9a-f]{16}\Z')
JOB_NAME = re.compile(r'^a15_cot_ap[0-9a-f]{16}\Z')
ONE_JOB_PARTITIONS = ('general',)
OSSH = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh'
SCRIPT_LIMIT = 4 * 1024 * 1024 - 64 * 1024
UNPACK_LIMIT = 64 << 20
HOME_DEFAULT = 100 * 1024 * 1024
FETCH_LIMIT = 1 << 30
IDENTITY_FILES = ('PINS.json', 'CONFIG.json', 'DRYRUN_REPORT.json')


class LaunchError(ValueError):
    pass


# ---------------------------------------------------------------- job name

def mint_job_name(token=None):
    """The one place a job name is made: a15_cot_ap plus 16 random lowercase hex. Returns
    (token, job_name)."""
    token = token if token is not None else secrets.token_hex(8)
    if not TOKEN.match(token):
        raise LaunchError('token must be 16 lowercase hex: %r' % (token,))
    name = PREFIX + token
    if not JOB_NAME.match(name):
        raise LaunchError('job name %r does not match the format' % name)
    return token, name


# ---------------------------------------------------------------- schema (subset of JSON Schema)

TYPES = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}


def _type_ok(value, name):
    if name == 'integer':
        return type(value) is int
    if name == 'number':
        return type(value) in (int, float)
    return isinstance(value, TYPES[name]) and not (name != 'boolean' and type(value) is bool)


def check_schema(value, schema, where='$'):
    """Errors of value against a JSON Schema subset: type, enum, required, properties,
    additionalProperties, items, minItems, minimum, maximum, pattern."""
    errors = []
    kinds = schema.get('type')
    if kinds is not None:
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not any(_type_ok(value, kind) for kind in kinds):
            return ['%s: expected %s' % (where, '|'.join(kinds))]
    if value is None:
        return errors
    if 'enum' in schema and value not in schema['enum']:
        errors.append('%s: %r not in %r' % (where, value, schema['enum']))
    if isinstance(value, dict):
        for key in schema.get('required', ()):
            if key not in value:
                errors.append('%s: missing %s' % (where, key))
        props = schema.get('properties', {})
        extra = schema.get('additionalProperties', True)
        for key, item in sorted(value.items()):
            if key in props:
                errors.extend(check_schema(item, props[key], '%s.%s' % (where, key)))
            elif extra is False:
                errors.append('%s: unknown key %s' % (where, key))
            elif isinstance(extra, dict):
                errors.extend(check_schema(item, extra, '%s.%s' % (where, key)))
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            errors.append('%s: fewer than %d items' % (where, schema['minItems']))
        if 'items' in schema:
            for index, item in enumerate(value):
                errors.extend(check_schema(item, schema['items'], '%s[%d]' % (where, index)))
    if type(value) in (int, float):
        if 'minimum' in schema and value < schema['minimum']:
            errors.append('%s: below %s' % (where, schema['minimum']))
        if 'maximum' in schema and value > schema['maximum']:
            errors.append('%s: above %s' % (where, schema['maximum']))
    if isinstance(value, str) and 'pattern' in schema and not re.search(schema['pattern'], value):
        errors.append('%s: does not match %s' % (where, schema['pattern']))
    return errors


def validate_config(config):
    errors = check_schema(config, util.read_json(os.path.join(SCHEMAS, 'config.schema.json')))
    family = config.get('family', 'generic') if isinstance(config, dict) else 'generic'
    path = os.path.join(SCHEMAS, 'family.%s.schema.json' % family)
    if not os.path.isfile(path):
        errors.append('$.family: no schema for family %r' % family)
    elif isinstance(config, dict) and isinstance(config.get('spec'), dict):
        errors.extend(check_schema(config['spec'], util.read_json(path), '$.spec'))
    if isinstance(config, dict) and isinstance(config.get('job'), dict):
        job = config['job']
        if isinstance(job.get('signal_s'), int) and isinstance(job.get('time_limit_s'), int) \
                and job['signal_s'] >= job['time_limit_s']:
            errors.append('$.job.signal_s: must be below time_limit_s')
    if isinstance(config, dict):
        try:
            stage.load_plan(config)
        except stage.StageError as err:
            errors.append('$.stage: %s' % err)
    return errors


# ---------------------------------------------------------------- provenance

def provenance(checkout, config_path):
    """Commit of an epoch checkout on node-local disk; refuses /home, /data* and a dirty tree."""
    real = os.path.realpath(checkout)
    if re.match(r'^/(home|data[0-9]*)(/|$)', real):
        raise LaunchError('provenance runs only on a node-local epoch checkout, not %s' % real)
    env = dict((key, value) for key, value in os.environ.items() if not key.startswith('GIT_'))
    env['GIT_OPTIONAL_LOCKS'] = '0'

    def git(*args):
        return subprocess.check_output(['git', '-C', real] + list(args), env=env,
                                       stderr=subprocess.PIPE, universal_newlines=True).strip()

    try:
        top = os.path.realpath(git('rev-parse', '--show-toplevel'))
        commit = git('rev-parse', '--verify', 'HEAD')
        dirty = bool(git('status', '--porcelain', '--untracked-files=all'))
    except (OSError, subprocess.CalledProcessError) as err:
        raise LaunchError('provenance refused: %s' % err)
    if top != real:
        raise LaunchError('provenance refused: %s is not a repository root' % real)
    if dirty:
        raise LaunchError('provenance refused: the epoch checkout is dirty')
    return {'repo_commit': commit, 'checkout': real, 'dirty': False,
            'config_sha256': util.sha256_file(config_path)[0]}


# ---------------------------------------------------------------- bundle and script

def kit_files(kit):
    rows = []
    for current, dirs, files in os.walk(kit):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(current, name)
            if os.path.islink(path):
                raise LaunchError('kit holds a symlink: %s' % os.path.relpath(path, kit))
            if not stat.S_ISREG(os.lstat(path).st_mode):
                raise LaunchError('kit holds a special file: %s' % os.path.relpath(path, kit))
            rows.append((os.path.relpath(path, kit), path))
        for name in dirs:
            if os.path.islink(os.path.join(current, name)):
                raise LaunchError('kit holds a symlink: %s' % name)
    return rows


def snapshot(kit, dest):
    """Copy every kit file, read once, into a fresh private directory. prepare checks and bundles
    only this copy, so a change to the source kit after it is read cannot reach the batch host."""
    os.makedirs(dest, 0o700)
    for rel, path in kit_files(kit):
        target = os.path.join(dest, rel)
        if not os.path.isdir(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target), 0o700)
        with open(path, 'rb') as handle:
            data = handle.read()
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                     0o700 if os.access(path, os.X_OK) else 0o600)
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
    return dest


def bundle_bytes(kit, job):
    """Deterministic gzip tar of kit/<files> plus JOB.json."""
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            members = [('kit/' + rel, path) for rel, path in kit_files(kit)]
            for name, path in members:
                with open(path, 'rb') as handle:
                    data = handle.read()
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o755 if os.access(path, os.X_OK) else 0o644
                info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
            data = util.canonical_json(job) + b'\n'
            info = tarfile.TarInfo('JOB.json')
            info.size = len(data)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(data))
    return raw.getvalue()


def time_text(seconds):
    days, rest = divmod(int(seconds), 86400)
    text = '%02d:%02d:%02d' % (rest // 3600, rest % 3600 // 60, rest % 60)
    return '%d-%s' % (days, text) if days else text


def render(config, token, payload):
    """The batch script for one job: one template, every per-run value from CONFIG.job."""
    _, name = mint_job_name(token)
    job = config['job']
    with open(TEMPLATE, 'rb') as handle:
        text = handle.read().decode('utf-8')
    digits = payload.hex()
    lines = '\n'.join(digits[index:index + 120] for index in range(0, len(digits), 120))
    values = {
        'JOB_NAME': name, 'TOKEN': token, 'PARTITION': job['partition'], 'CPUS': str(job['cpus']),
        'MEM_GB': str(job['mem_gb']), 'TIME': time_text(job['time_limit_s']),
        'SIGNAL_S': str(job['signal_s']), 'GPUS': str(job['gpus']),
        'ACCOUNT_LINE': '#SBATCH --account=%s' % job['account'] if job.get('account')
        else '# no account line',
        'GRES_LINE': '#SBATCH --gres=gpu:%d' % job['gpus'] if job['gpus'] else '# no GPU',
        'NICE_LINE': '#SBATCH --nice=%d' % job['nice'] if job['nice'] else '# no nice',
        'CPU_GUARD': 'export CUDA_VISIBLE_DEVICES=' if not job['gpus']
        else '# GPU job: the driver refuses to start without CUDA_VISIBLE_DEVICES',
        'ROOT_PARENT': job.get('root_parent', '/tmp'), 'PACKAGE': job.get('package', 'lib'),
        'UNPACK_LIMIT': str(UNPACK_LIMIT), 'PAYLOAD_SHA256': util.sha256_bytes(payload),
        'PAYLOAD_HEX': lines,
    }
    for key, value in values.items():
        text = text.replace('{{%s}}' % key, value)
    if '{{' in text:
        raise LaunchError('template placeholder left unrendered')
    if len(text.encode('utf-8')) > SCRIPT_LIMIT:
        raise LaunchError('batch script is %d bytes; limit %d' % (len(text), SCRIPT_LIMIT))
    return text


def live_check(partition):
    """Bash that refuses when one of our jobs is live on a one-job partition, unless its name is in
    QUEUE_BEHIND (set by submit from the GO file, ahead of the pinned script)."""
    if partition not in ONE_JOB_PARTITIONS:
        return ': no one-job gate on %s' % partition
    return '\n'.join([
        'queue=$(squeue -h -u "${USER:-$(id -un)}" -p %s -o %%j </dev/null) || '
        '{ echo "LIVE unknown: squeue failed"; exit 6; }' % partition,
        'for live in $queue; do',
        '  case "$live" in %s*) ;; *) continue;; esac' % PREFIX,
        '  case " ${QUEUE_BEHIND:-} " in *" $live "*) ;; *) echo "LIVE $live"; exit 6;; esac',
        'done'])


def submit_script(config, token, script):
    """Bash for the batch host: check home quota and pool room, then sbatch; submit nothing when
    either is short."""
    budgets = config.get('budgets') or {}
    home = (budgets.get('home') or {}).get('max_bytes', HOME_DEFAULT)
    pool = (config.get('return') or {}).get('pool') or ''
    pool_need = (budgets.get('pool') or {}).get('max_bytes', 0)
    check = '\n'.join([
        'import os, sys',
        'def room(label, path, need):',
        '    try:',
        '        vfs = os.statvfs(path)',
        '        free = vfs.f_bavail * vfs.f_frsize',
        '        probe = os.path.join(path, ".p_probe")',
        '        fd = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)',
        '        try:',
        '            if need:',
        '                os.posix_fallocate(fd, 0, need)',
        '                os.fsync(fd)',
        '        finally:',
        '            os.ftruncate(fd, 0)',
        '            os.close(fd)',
        '    except OSError as err:',
        '        print("SHORT %s %s" % (label, err))',
        '        sys.exit(3)',
        '    if free < need:',
        '        print("SHORT %s free=%d need=%d" % (label, free, need))',
        '        sys.exit(3)',
        '    print("ROOM %s free=%d need=%d" % (label, free, need))',
        'room("home", os.path.expanduser("~"), %d)' % home,
        'if %r:' % pool,
        '    room("pool", %r, %d)' % (pool, pool_need),
    ])
    digest = util.sha256_bytes(script.encode('utf-8'))
    return '\n'.join([
        '#!/bin/bash',
        'set -euo pipefail',
        "python3 -E -s -B - <<'CHECK_%s'" % token, check, 'CHECK_%s' % token,
        'body=$(mktemp "${TMPDIR:-/tmp}/.b.XXXXXXXX")',
        "cat > \"$body\" <<'BATCH_%s'" % token, script.rstrip('\n'), 'BATCH_%s' % token,
        'test "$(sha256sum "$body" | cut -c1-64)" = "%s" || { echo "BODY DIFFERS"; exit 4; }' % digest,
        live_check(config['job']['partition']),
        'sbatch --test-only "$body" </dev/null >/dev/null 2>&1 || { echo "TEST-ONLY REFUSED"; exit 5; }',
        'jid=$(sbatch --parsable "$body" </dev/null)',
        'echo "JOBID=${jid%%;*}"', ''])


# ---------------------------------------------------------------- transport

def transport_argv():
    return ['timeout', '300', 'bash', os.environ.get('ORCHKIT_OSSH') or OSSH, 'bash -s']


def run_transport(argv, stdin_bytes):
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate(stdin_bytes, timeout=330)
    return process.returncode, out, err


# ---------------------------------------------------------------- prepare

def check_dryrun(path, kit_pins, config_sha):
    if not path or not os.path.isfile(path):
        raise LaunchError('no dry-run report at %s; give --no-dryrun-reason to proceed without' % path)
    report = util.read_json(path)
    if report.get('schema') != 'orchkit-dryrun-v1':
        raise LaunchError('dry-run report is not orchkit-dryrun-v1')
    if report.get('verdict') != 'PASS':
        raise LaunchError('dry-run verdict is %r, not PASS' % report.get('verdict'))
    if report.get('kit_pins_sha256') != kit_pins or report.get('config_sha256') != config_sha:
        raise LaunchError('dry-run report hashes differ from this kit and config')
    return {'path': os.path.abspath(path), 'verdict': 'PASS'}


def check_kit(kit, config_raw, rules):
    """Every kit check, on one directory: the config bytes equal the kit's CONFIG.json, the config
    validates, PINS.json is valid and named by the config, every pinned file matches, no file is
    unpinned, no hash is copied, and nothing trips the opacity check. Returns
    (config, manifest, kit_pins_sha256, config_sha256)."""
    kit_config = os.path.join(kit, 'CONFIG.json')
    if not os.path.isfile(kit_config) or util.sha256_file(kit_config)[0] != util.sha256_bytes(config_raw):
        raise LaunchError('--config differs from the kit CONFIG.json')
    config = json.loads(config_raw.decode('utf-8'))
    errors = validate_config(config)
    if errors:
        raise LaunchError('config is invalid: %s' % '; '.join(errors[:20]))
    config_sha = util.sha256_bytes(config_raw)
    manifest = pins.validate_manifest(util.read_json(os.path.join(kit, 'PINS.json')))
    kit_pins = pins.kit_identity(manifest)
    if config['kit_pins_sha256'] != kit_pins:
        raise LaunchError('config kit_pins_sha256 differs from PINS.json')
    bad = pins.differences(pins.verify(manifest, kit))
    if bad:
        raise LaunchError('pins differ: %s' % json.dumps(bad, sort_keys=True)[:2000])
    pinned = set(entry['logical_path'] for entry in manifest['entries'])
    loose = [rel for rel, _ in kit_files(kit) if rel not in pinned and rel not in IDENTITY_FILES]
    if loose:
        raise LaunchError('kit files without a pin entry: %s' % loose[:20])
    copies = pins.check_single_place(kit)
    if copies:
        raise LaunchError('single-place invariant: %s' % json.dumps(copies, sort_keys=True)[:2000])
    hits = anon.scan_tree(kit, rules)
    if hits:
        raise LaunchError('opacity: %s' % json.dumps(hits, sort_keys=True)[:2000])
    return config, manifest, kit_pins, config_sha


def build_submission(kit, config, job, rules):
    """The batch script and the submission script, rebuilt deterministically from a checked kit and
    JOB.json, after the opacity check of every part bound for the batch host."""
    script = render(config, job['token'], bundle_bytes(kit, job))
    remote = submit_script(config, job['token'], script)
    hits = anon.scan_job(rules, job_name=job['job_name'], script=script, argv=config['entry'],
                         env=(config.get('return') or {}).get('gcs_env') or {})
    hits += anon.scan_text('script', script, rules, 'name')
    hits += anon.scan_text('submit', remote, rules, 'name')
    hits += anon.scan_text('JOB.json', util.canonical_json(job).decode('utf-8'), rules, 'name')
    if hits:
        raise LaunchError('opacity: %s' % json.dumps(hits, sort_keys=True)[:2000])
    return script, remote


def prepare(kit, config_path, out, lane, meaning, checkout, dryrun=None, no_dryrun_reason=None,
            sessions=None, ledger_file=None, provenance_fn=provenance, token=None, rules=None):
    kit, out = os.path.abspath(kit), os.path.abspath(out)
    if os.path.lexists(out):
        raise LaunchError('refusing to reuse %s' % out)
    check = tempfile.mkdtemp(prefix=os.path.basename(out) + '.check.', dir=os.path.dirname(out))
    kit = snapshot(kit, os.path.join(check, 'kit'))
    with open(config_path, 'rb') as handle:
        config_raw = handle.read()
    rules = rules or anon.load_rules()
    config, manifest, kit_pins, config_sha = check_kit(kit, config_raw, rules)
    if no_dryrun_reason:
        dry = {'path': None, 'verdict': None, 'no_dryrun_reason': no_dryrun_reason}
    else:
        dry = check_dryrun(dryrun or os.path.join(kit, 'DRYRUN_REPORT.json'), kit_pins, config_sha)
    record = provenance_fn(checkout, config_path)
    token, name = mint_job_name(token)
    job = {'token': token, 'job_name': name,
           'sessions': util.read_json(sessions) if sessions else {}}
    script, remote = build_submission(kit, config, job, rules)
    argv = transport_argv()
    target = config.get('return') or {}
    gcs = ('%s/%s' % (target['gcs_prefix'].rstrip('/'), token)) if target.get('gcs_prefix') else None
    text = meaning + ('' if not no_dryrun_reason else ' | no-dryrun: ' + no_dryrun_reason)
    row = ledger.make_row('minted', token, lane=lane, meaning=text, kit_pins_sha256=kit_pins,
                          config_sha256=config_sha, partition=config['job']['partition'],
                          gpus=config['job']['gpus'], time_limit_s=config['job']['time_limit_s'],
                          pool=target.get('pool'), gcs=gcs, state='prepared')
    row = ledger._fit(row)
    ledger.validate(row)
    os.rename(check, out)
    util.atomic_write(os.path.join(out, 'BATCH.sh'), script.encode('utf-8'))
    util.atomic_write(os.path.join(out, 'SUBMIT.sh'), remote.encode('utf-8'))
    util.write_json(os.path.join(out, 'JOB.json'), job)
    submit = {'schema': 'orchkit-submit-v1', 'token': token, 'job_name': name, 'argv': argv,
              'stdin': 'SUBMIT.sh', 'script_sha256': util.sha256_bytes(script.encode('utf-8')),
              'submit_sha256': util.sha256_bytes(remote.encode('utf-8')),
              'kit_pins_sha256': kit_pins, 'config_sha256': config_sha,
              'partition': config['job']['partition'], 'gpus': config['job']['gpus'],
              'time_limit_s': config['job']['time_limit_s'], 'pool': target.get('pool'),
              'gcs': gcs, 'provenance': record, 'dryrun': dry, 'lane': lane,
              'kit_snapshot': os.path.join(out, 'kit'),
              'ledger': ledger.ledger_path(ledger_file)}
    util.write_json(os.path.join(out, 'SUBMIT.json'), submit)
    ledger.append(row, ledger_file)
    return submit


# ---------------------------------------------------------------- submit, status, fetch

def _load_prep(prep):
    submit = util.read_json(os.path.join(prep, 'SUBMIT.json'))
    for name, key in (('BATCH.sh', 'script_sha256'), ('SUBMIT.sh', 'submit_sha256')):
        if util.sha256_file(os.path.join(prep, name))[0] != submit[key]:
            raise LaunchError('%s changed after prepare' % name)
    return submit


def _names(text, token):
    return re.search(r'(?<![0-9a-f])%s(?![0-9a-f])' % token, text) is not None


def _go_names(text, token):
    """True when a line of the GO file starts with the word GO and names the token."""
    return any(_names(line, token) for line in text.splitlines()
               if re.match(r'^\s*GO(?![\w-])', line))


def rebuild(prep, record, rows, rules=None):
    """The exact submission bytes, rebuilt from a private snapshot of PREP/kit (read once, then
    checked and bundled) and PREP/JOB.json (read once), and anchored to the ledger: the minted row of the token must name this kit and config, the kit must pass every
    check again, and BATCH.sh, SUBMIT.sh and the transport argv in PREP must equal the rebuild.
    Nothing in SUBMIT.json is trusted beyond the token."""
    token, name = mint_job_name(record['token'])
    minted = [row for row in rows if row.get('event') == 'minted']
    if len(minted) != 1:
        raise LaunchError('ledger must hold exactly one minted row for %s' % token)
    job = util.read_json(os.path.join(prep, 'JOB.json'))
    kit = snapshot(os.path.join(prep, 'kit'),
                   os.path.join(tempfile.mkdtemp(prefix='.submit.', dir=prep), 'kit'))
    with open(os.path.join(kit, 'CONFIG.json'), 'rb') as handle:
        config_raw = handle.read()
    config, _, kit_pins, config_sha = check_kit(kit, config_raw, rules or anon.load_rules())
    if (minted[0].get('kit_pins_sha256'), minted[0].get('config_sha256')) != (kit_pins, config_sha):
        raise LaunchError('the ledger row of %s names another kit or config' % token)
    if job.get('token') != token or job.get('job_name') != name or record.get('job_name') != name:
        raise LaunchError('the prepared scripts do not belong to token %s' % token)
    script, remote = build_submission(kit, config, job, rules or anon.load_rules())
    for file_name, expect in (('BATCH.sh', script), ('SUBMIT.sh', remote)):
        with open(os.path.join(prep, file_name), 'rb') as handle:
            if handle.read() != expect.encode('utf-8'):
                raise LaunchError('%s differs from its rebuild; prepare again' % file_name)
    if record.get('argv') != transport_argv() or record.get('stdin') != 'SUBMIT.sh':
        raise LaunchError('the transport command differs from the one prepare recorded')
    return remote.encode('utf-8')


def claim_token(token, ledger_file=None):
    """Claim a token once for the whole account: an exclusive file beside the shared ledger, so two
    copies of one preparation cannot both reach the transport."""
    claims = ledger.ledger_path(ledger_file) + '.claims'
    if not os.path.isdir(claims):
        try:
            os.makedirs(claims, 0o700)
        except OSError:
            if not os.path.isdir(claims):
                raise
    try:
        fd = os.open(os.path.join(claims, token), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        raise LaunchError('token %s was already claimed for submission; never repeat a submit' % token)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(util.canonical_json({'token': token, 'utc': util.utc_iso(),
                                          'pid': os.getpid()}) + b'\n')
        handle.flush()
        os.fsync(handle.fileno())


def submit(prep, go, execute=False, ledger_file=None, transport=None, out=sys.stdout, rules=None):
    prep = os.path.abspath(prep)
    record = _load_prep(prep)
    token = record['token']
    if not go or not os.path.isfile(go):
        raise LaunchError('no GO file at %s' % go)
    with open(go, 'rb') as handle:
        go_text = handle.read().decode('utf-8', 'replace')
    if not _go_names(go_text, token):
        raise LaunchError('no line of the GO file starts with GO and names token %s' % token)
    rows = ledger.lookup(token, ledger_file)
    if not any(row.get('event') == 'minted' for row in rows):
        raise LaunchError('ledger has no minted row for %s' % token)
    if any(row.get('event') == 'submitted' for row in rows) or \
            os.path.exists(os.path.join(prep, 'SUBMIT_INTENT.json')):
        raise LaunchError('already submitted or attempted; never repeat an uncertain submit')
    if record['partition'] in ONE_JOB_PARTITIONS:
        live = [row for row in ledger.live(ledger_file, [record['partition']])
                if row.get('token') != token]
        behind = re.search(r'queue[ _-]behind', go_text, re.I) is not None
        if live and not (behind and all(_names(go_text, row['token']) for row in live)):
            raise LaunchError('our job %s is live on %s; the GO file must say "queue behind" and '
                              'name it' % (','.join(row['token'] for row in live), record['partition']))
    argv = record['argv']
    out.write('%s < %s\n' % (' '.join(argv), os.path.join(prep, record['stdin'])))
    if not execute:
        return {'executed': False, 'argv': argv}
    pinned = rebuild(prep, record, rows, rules)
    try:
        fd = os.open(os.path.join(prep, 'SUBMIT_INTENT.json'), os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                     0o600)
    except OSError:
        raise LaunchError('another submit of %s holds the intent; never repeat a submit' % token)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(util.canonical_json({'token': token, 'utc': util.utc_iso(),
                                          'go': os.path.abspath(go)}) + b'\n')
        handle.flush()
        os.fsync(handle.fileno())
    claim_token(token, ledger_file)
    if any(row.get('event') == 'submitted' for row in ledger.lookup(token, ledger_file)):
        raise LaunchError('ledger already shows %s submitted' % token)
    behind = sorted(set(PREFIX + found for found in re.findall(r'(?<![0-9a-f])([0-9a-f]{16})(?![0-9a-f])',
                                                                 go_text) if found != token))
    body = ('QUEUE_BEHIND=%s\n' % ("'%s'" % ' '.join(behind) if behind and re.search(
        r'queue[ _-]behind', go_text, re.I) else "''")).encode('utf-8') + pinned
    code, stdout, stderr = (transport or run_transport)(transport_argv(), body)
    text = stdout.decode('utf-8', 'replace')
    found = re.search(r'^JOBID=(\d+)\s*$', text, re.M)
    result = {'token': token, 'utc': util.utc_iso(), 'rc': code, 'stdout': text[-4000:],
              'stderr': stderr.decode('utf-8', 'replace')[-4000:]}
    if code == 0 and found:
        result.update(status='SUBMITTED', job_id=int(found.group(1)))
    elif re.search(r'^SHORT ', text, re.M):
        result.update(status='REFUSED_ROOM', job_id=None)
    elif re.search(r'^LIVE ', text, re.M):
        result.update(status='REFUSED_LIVE', job_id=None)
    else:
        result.update(status='UNCERTAIN', job_id=None)
    util.write_json(os.path.join(prep, 'SUBMISSION.json'), result)
    if result['status'] == 'SUBMITTED':
        ledger.append(ledger.make_row(
            'submitted', token, job_id=result['job_id'], lane=record.get('lane'),
            kit_pins_sha256=record['kit_pins_sha256'], config_sha256=record['config_sha256'],
            partition=record['partition'], gpus=record['gpus'],
            time_limit_s=record['time_limit_s'], pool=record['pool'], gcs=record['gcs'],
            state='PENDING'), ledger_file)
        return dict(result, executed=True)
    raise LaunchError('submission %s: %s' % (result['status'], text[-500:]))


def _job_id(prep):
    result = util.read_json(os.path.join(prep, 'SUBMISSION.json'))
    if result.get('status') != 'SUBMITTED':
        raise LaunchError('no confirmed submission in %s' % prep)
    return int(result['job_id'])


def status(prep, execute=False, ledger_file=None, transport=None, out=sys.stdout):
    prep = os.path.abspath(prep)
    record = _load_prep(prep)
    job_id = _job_id(prep)
    body = ("TZ=UTC squeue -h -j %d -o '%%i|%%j|%%T|%%M|%%l|%%R' || true\n"
            "TZ=UTC sacct -n -P -X -j %d -o JobID,JobName,State,ExitCode,Elapsed || true\n"
            % (job_id, job_id)).encode('utf-8')
    argv = record['argv']
    out.write('%s <<< %r\n' % (' '.join(argv), body.decode('utf-8')))
    if not execute:
        return {'executed': False, 'argv': argv}
    code, stdout, _ = (transport or run_transport)(argv, body)
    text = stdout.decode('utf-8', 'replace')
    state = None
    for line in text.splitlines():
        fields = line.split('|')
        if len(fields) == 5 and fields[0] == str(job_id) and fields[1] == record['job_name']:
            state = fields[2].split()[0]
    if state and state in ledger.ENDED_STATES and not any(
            row.get('event') == 'ended' for row in ledger.lookup(record['token'], ledger_file)):
        ledger.append(ledger.make_row('ended', record['token'], job_id=job_id,
                                      lane=record.get('lane'), partition=record['partition'],
                                      pool=record['pool'], gcs=record['gcs'], state=state),
                      ledger_file)
    return {'executed': True, 'rc': code, 'state': state, 'text': text}


def fetch(prep, dest, execute=False, transport=None, out=sys.stdout):
    prep, dest = os.path.abspath(prep), os.path.abspath(dest)
    record = _load_prep(prep)
    if not record.get('pool'):
        raise LaunchError('the kit has no pool to fetch from')
    folder = '%s/%s' % (record['pool'].rstrip('/'), record['token'])
    body = ("set -euo pipefail\ncd %s\n"
            "test \"$(stat -c%%s result.tar.gz)\" -le %d\n"
            "tar cf - RECEIPT.json result.tar.gz\n" % (folder, FETCH_LIMIT)).encode('utf-8')
    argv = record['argv']
    out.write('%s <<< %r\n' % (' '.join(argv), body.decode('utf-8')))
    if not execute:
        return {'executed': False, 'argv': argv}
    code, stdout, stderr = (transport or run_transport)(argv, body)
    if code:
        raise LaunchError('fetch failed (%d): %s' % (code, stderr.decode('utf-8', 'replace')[-500:]))
    stage.safe_extract(lambda: io.BytesIO(stdout), dest, 'new')
    receipt = util.read_json(os.path.join(dest, 'RECEIPT.json'))
    digest, count = util.sha256_file(os.path.join(dest, 'result.tar.gz'))
    if receipt.get('token') != record['token'] or receipt['archive']['sha256'] != digest \
            or receipt['archive']['bytes'] != count:
        raise LaunchError('fetched archive differs from its receipt')
    return {'executed': True, 'state': receipt['state'], 'dest': dest, 'bytes': count}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command')
    p = sub.add_parser('prepare')
    p.add_argument('--kit', required=True)
    p.add_argument('--config', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--lane', required=True)
    p.add_argument('--meaning', required=True)
    p.add_argument('--checkout', required=True)
    p.add_argument('--dryrun')
    p.add_argument('--no-dryrun-reason')
    p.add_argument('--sessions')
    p.add_argument('--ledger')
    s = sub.add_parser('submit')
    s.add_argument('--prep', required=True)
    s.add_argument('--go', required=True)
    s.add_argument('--execute', action='store_true')
    s.add_argument('--ledger')
    t = sub.add_parser('status')
    t.add_argument('--prep', required=True)
    t.add_argument('--execute', action='store_true')
    t.add_argument('--ledger')
    f = sub.add_parser('fetch')
    f.add_argument('--prep', required=True)
    f.add_argument('--dest', required=True)
    f.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            value = prepare(args.kit, args.config, args.out, args.lane, args.meaning, args.checkout,
                            args.dryrun, args.no_dryrun_reason, args.sessions, args.ledger)
            print(json.dumps({'token': value['token'], 'job_name': value['job_name'],
                              'kit_pins_sha256': value['kit_pins_sha256']}, sort_keys=True))
            return 0
        if args.command == 'submit':
            value = submit(args.prep, args.go, args.execute, args.ledger)
        elif args.command == 'status':
            value = status(args.prep, args.execute, args.ledger)
        elif args.command == 'fetch':
            value = fetch(args.prep, args.dest, args.execute)
        else:
            parser.print_help()
            return 2
        print(json.dumps(value, sort_keys=True))
        return 0
    except (LaunchError, pins.PinError, ledger.LedgerError, stage.StageError, OSError,
            ValueError) as err:
        sys.stderr.write('launch: %s\n' % err)
        return 2


if __name__ == '__main__':
    sys.exit(main())
