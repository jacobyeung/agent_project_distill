"""Local A4 post-processing: preserve reviewed helpers and require an export binding."""
import argparse
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orchard_h10.common import canonical, valid_token, write
from u0.a12 import batch



# Vendored verbatim from cont_ops17/work/build_r10.py; no script-side effects.
HEAD_OLD = "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\n"
def wrap_batch(text, tok):
    # ORCH ANSWER 0318Z item 2: node-local log, EXIT trap copies node line + exit code + last 60 lines to the package's a/x<job>;
    # USR1 (stop margin) is forwarded to the reader; a failed copy never changes the exit code. #SBATCH exclude: item 3.
    t = text.decode(); assert t.startswith(HEAD_OLD) and t.endswith('\nA\n') and t.count('\nA\n') == 1
    head = ("#!/bin/bash\n#SBATCH --exclude=orchard-community-2\nset -uo pipefail\n"
            "P=/project/community/jjyeung/okh7/a15_cot_ap" + tok + "\nL=/tmp/a${SLURM_JOB_ID:-0}.l\nR=$P/a/x${SLURM_JOB_ID:-0}\n"
            "fin(){ rc=$?; { head -n 1 \"$L\"; echo \"exit $rc\"; tail -n 60 \"$L\"; } > \"$R\" 2>/dev/null || true; exit $rc; }\n"
            "trap fin EXIT\n"
            "echo \"node $(hostname -s) tmp_free_kb $(df -Pk /tmp | awk 'NR==2{print $4}') gpus $(nvidia-smi -L 2>/dev/null | wc -l) cvd ${CUDA_VISIBLE_DEVICES:-none}\" > \"$L\" 2>/dev/null\n"
            "/usr/bin/python3 -I -s -B - >>\"$L\" 2>&1 <<'A' &\n")
    tail = "\nA\nPID=$!\ntrap 'kill -USR1 $PID 2>/dev/null' USR1\nwhile true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done\nexit $rc\n"
    return (head + t[len(HEAD_OLD):-len('\nA\n')] + tail).encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def tarbytes(files):
    # The same deterministic serializer used by cont_ops' build_r1.py.
    result = io.BytesIO()
    with gzip.GzipFile(fileobj=result, mode='wb', mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w') as archive:
            for name, raw in sorted(files.items()):
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                member.mode = 0o600
                archive.addfile(member, io.BytesIO(raw))
    return result.getvalue()


def unpack(raw):
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        total = 0
        for member in archive:
            path = Path(member.name)
            total += member.size
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != member.name or member.name in files or total > 64*1024**2):
                raise ValueError('Unsafe code archive')
            files[member.name] = archive.extractfile(member).read()
    return files


def bootstrap(text):
    lines = [line for line in text.splitlines() if line.startswith('b=bytes.fromhex(')]
    if len(lines) != 1:
        raise ValueError('A4 batch encoding differs')
    files = unpack(bytes.fromhex(ast.literal_eval(lines[0][len('b=bytes.fromhex('):-1])))
    if set(files) != {'0.py', '7.py', '0.json'}:
        raise ValueError('A4 bundle inventory differs')
    return files


def checked_binding(path):
    value = json.loads(Path(path).read_text())
    required = {'run', 'step', 'member_directory', 'lineage', 'object', 'config_sha256',
                'base_identity', 'frame_layout', 'preparation_sha256', 'archive_bytes', 'archive_sha256'}
    if not required <= value.keys() or type(value['step']) is not int or value['step'] < 600:
        raise ValueError('Require a reviewed step-600-or-later export binding')
    if type(value['archive_bytes']) is not int or value['archive_bytes'] <= 0:
        raise ValueError('Require reviewed export archive bytes')
    if value['lineage'] not in ('SFT', 'RL'):
        raise ValueError('Invalid export lineage')
    if any(not isinstance(value[k], str) or not value[k] for k in required-{'step','preparation_sha256','archive_bytes'}):
        raise ValueError('Incomplete export binding')
    member = Path(value['member_directory'])
    if member.is_absolute() or '..' in member.parts or str(member) != value['member_directory']:
        raise ValueError('Invalid member directory')
    import re
    prep = value['preparation_sha256']
    if not isinstance(prep, dict) or set(prep) != {'config', 'receipt', 'data_receipt'}:
        raise ValueError('Incomplete preparation binding')
    if any(not isinstance(h, str) or not re.fullmatch('[0-9a-f]{64}', h)
           for h in [value['config_sha256'], value['archive_sha256'], *prep.values()]):
        raise ValueError('Invalid binding digest')
    return value


REVIEWED_PAYLOAD = '4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d'


def authenticate(base, source, original, payload, manifest_path, extension_pins_path):
    if manifest_path is None or extension_pins_path is None:
        raise ValueError('Require reviewed MANIFEST and EXTENSION_PINS')
    manifest = json.loads(Path(manifest_path).read_text())
    pins = json.loads(Path(extension_pins_path).read_text())
    expected = {n: pin['after_sha256'] for patch in manifest['patches'].values()
                for n, pin in patch['files'].items() if n.startswith('u0/')}
    if not pins or pins != expected:
        raise ValueError('Extension pins differ from MANIFEST')
    if sha(original) != REVIEWED_PAYLOAD or manifest['a4_payload_pin'] != dict(
            sha256=sha(original), bytes=len(original)):
        raise ValueError('Require the reviewed A4 payload')
    batch_raw = (base/'package/BATCH.sh').read_bytes()
    if sha(batch_raw) != manifest['operator_base_pin']['batch_sha256']:
        raise ValueError('A4 batch pin differs')
    if sha(bootstrap(batch_raw.decode())['0.py']) != manifest['operator_base_pin']['decoded_bootstrap_sha256']:
        raise ValueError('A4 bootstrap pin differs')
    for name in ('package/0.json', 'package/3.py', 'package/a/0.json',
                 'package/a/4.py', 'package/a/7.py', 'fetch_return.py'):
        raw = (base/name).read_bytes()
        if manifest['a4_member_pins'][name] != dict(sha256=sha(raw), bytes=len(raw)):
            raise ValueError('A4 member pin differs: '+name)
    for name in ('tower_sequence.py', 'unpack_return.py', 'package/a/5.py'):
        raw = (base/name).read_bytes()
        if manifest['operator_files'][name] != dict(sha256=sha(raw), bytes=len(raw)):
            raise ValueError('Patched operator pin differs: '+name)
    paths = list((source/'u0').rglob('*'))
    if (source/'u0').is_symlink() or any(p.is_symlink() for p in paths):
        raise ValueError('Extension source must be regular')
    actual = {str(p.relative_to(source)):sha(p.read_bytes()) for p in paths if p.is_file()}
    if actual != pins:
        raise ValueError('Extension inventory differs from reviewed pins')
    for name in ('entry', 'job', 'runner', 'prepare'):
        rel = 'orchard_h10/'+name+'.py'
        if sha(payload[rel]) != manifest['base_pin']['inventory'][rel]:
            raise ValueError('Alias base differs: '+rel)


def build(base_operator, source_root, export_binding, destination, token, *,
          enable_extensions=False, processor_only=False, manifest_path=None, extension_pins_path=None):
    if not enable_extensions:
        raise ValueError('A4 overlay build is OFF; require --enable-extensions')
    base = Path(base_operator).resolve()
    source = Path(source_root).resolve()
    out = Path(destination).resolve()
    token = valid_token(token)
    binding = checked_binding(export_binding)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Require a fresh operator directory')
    original = (base/'package/0.tgz').read_bytes()
    public = json.loads((base/'package/0.json').read_text())
    if sha(original) != public['payload_sha256'] or len(original) != public['payload_bytes']:
        raise ValueError('A4 payload differs')
    payload = unpack(original)
    authenticate(base, source, original, payload, manifest_path, extension_pins_path)
    cfg = json.loads(payload['9.json'])
    if canonical(cfg) != public['plan_sha256']:
        raise ValueError('A4 plan differs')
    if not isinstance(cfg.get('export_binding'), dict):
        raise ValueError('A4 reviewed export binding is missing')
    for name, pin in cfg['payload_pins'].items():
        if sha(payload[name]) != pin['sha256'] or len(payload[name]) != pin['bytes']:
            raise ValueError('A4 payload member differs: '+name)
    keys = ('stage1_select_rule', 'perception_memo', 'perception_memo_modules',
            'perception_memo_verify_ids', 'save_own_depth')
    if any(k not in cfg for k in keys):
        raise ValueError('A4 run keys are missing')
    if cfg['stage1_select_rule'] != 'candidates_argmax' or cfg['perception_memo'] != 'on':
        raise ValueError('Require the reviewed A4 run profile')
    bundled = bootstrap((base/'package/BATCH.sh').read_text())
    if json.loads(bundled['0.json']) != public:
        raise ValueError('A4 bundled public descriptor differs')
    # Keep 8.py, common, export admission, vendor code and serving bytes from A4.
    for path in sorted((source/'u0').rglob('*')):
        if path.is_symlink():
            raise ValueError('Extension source must be regular')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            payload[str(path.relative_to(source))] = path.read_bytes()
    for name, alias in (('entry','a13'),('job','a16'),('runner','a17'),('prepare','a18')):
        payload['orchard_h10/'+name+'.py'] = payload['u0/'+alias+'.py']
    cfg.update(token=token, export_binding=binding, read_extensions=True,
               read_scene_shards=False, read_atomic_journal=False,
               read_processor_only='on' if processor_only else 'off',
               read_processor_cache='on', read_vision_cache='off' if processor_only else 'on',
               read_sam_cache='off' if processor_only else 'on',
               read_cache_bytes=(4 if processor_only else 12)*1024**3)
    cfg['payload_pins'] = {n:dict(sha256=sha(b), bytes=len(b)) for n,b in payload.items() if n != '9.json'}
    payload['9.json'] = json.dumps(cfg, sort_keys=True).encode()
    raw = tarbytes(payload)
    if len(raw) > 8*1024**2:
        raise ValueError('Code archive exceeds local allowance')
    public = dict(token=token, payload_sha256=sha(raw), payload_bytes=len(raw), plan_sha256=canonical(cfg))
    package = out/'package'
    package.mkdir(parents=True)
    for name in ('3.py','a/0.json','a/4.py','a/5.py','a/7.py'):
        dest = package/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((base/'package'/name).read_bytes())
    for name in ('tower_sequence.py','fetch_return.py','unpack_return.py'):
        (out/name).write_bytes((base/name).read_bytes())
    # A4 seals the whole-tar receipt as constants in its fill helper. Bind the
    # new constants to the required reviewed export, retaining all admission code.
    fill = (package/'a/4.py').read_text()
    replacements = {'REVIEWED_OBJECT':binding['object'],
                    'REVIEWED_ARCHIVE_BYTES':binding['archive_bytes'],
                    'REVIEWED_ARCHIVE_SHA256':binding['archive_sha256']}
    lines = fill.splitlines(keepends=True)
    for name, value in replacements.items():
        positions = [i for i,line in enumerate(lines) if line.startswith(name+' = ')]
        if len(positions) != 1:
            raise ValueError('A4 fill helper constant differs: '+name)
        lines[positions[0]] = name+' = '+repr(value)+'\n'
    (package/'a/4.py').write_text(''.join(lines))
    (package/'a').chmod(0o700)
    operator = (out/'tower_sequence.py').read_bytes()
    (package/'a/6.py').write_bytes(operator)
    for name in ('0.json','CONFIG.json'):
        write(package/name, public)
    (package/'0.tgz').write_bytes(raw)
    (package/'BATCH.sh').write_bytes(wrap_batch(batch(tarbytes({'0.py':bundled['0.py'], '7.py':operator,
                                                  '0.json':(package/'0.json').read_bytes()}), token).encode(), token))
    # Never carry the step-200 inputs, CPU proof or submit ledger into a new package.
    for name in ('a/1.json','a/export.json'):
        write(package/name, dict(pending=True))
    for name, data in payload.items():
        path = out/'src'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    write(out/'EXPORT_BINDING.json', binding)
    immutable = ('0.tgz','0.json','3.py','BATCH.sh','CONFIG.json','a/0.json','a/4.py','a/5.py','a/6.py','a/7.py')
    write(package/'PACKAGE.json', dict(token=token, files={n:sha((package/n).read_bytes()) for n in immutable}))
    write(out/'BUILD.json', dict(base_payload_sha256=sha(original), base_plan_sha256=canonical(json.loads(unpack(original)['9.json'])),
          export_binding_sha256=canonical(binding), operator_sha256=sha(operator),
          bootstrap_sha256=sha(bundled['0.py']), submit_helper_sha256=sha(payload['8.py']),
          profile='processor_only' if processor_only else 'caches_only', cards=1, expected=636,
          partition='general', **public))
    return dict(directory=str(out), **public)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('base-operator','source-root','export-binding','out','token','manifest','extension-pins'):
        parser.add_argument('--'+key, required=True)
    parser.add_argument('--enable-extensions', action='store_true')
    parser.add_argument('--processor-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.base_operator,args.source_root,args.export_binding,args.out,args.token,
                          enable_extensions=args.enable_extensions,processor_only=args.processor_only,
                          manifest_path=args.manifest,extension_pins_path=args.extension_pins), sort_keys=True))
