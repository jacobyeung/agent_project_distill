"""Explicit local A4 operation plans and parity settings; never launches jobs."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from u0.a19 import checked_binding, sha, tarbytes, unpack
from orchard_h10.common import canonical

PROFILE_KEYS = ('stage1_select_rule', 'perception_memo', 'perception_memo_modules',
                'perception_memo_verify_ids', 'save_own_depth', 'read_processor_only',
                'read_processor_cache', 'read_vision_cache', 'read_sam_cache', 'read_cache_bytes')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def derive_binding(template, artifact, done, prep_files, output):
    value = read(template); art = read(artifact)
    fields = Path(done).read_text().split()
    if len(fields) != 3 or fields[0] != value['object']:
        raise ValueError('Whole-tar receipt object differs from target')
    if art['step'] != value['step'] or value['member_directory'] != 'm'+str(art['step']):
        raise ValueError('Artifact step differs from reviewed target')
    for key, filename in (('heads','heads.pt'), ('full_weights','full_weights/full_weights.json')):
        tail = Path(value['run'])/value['member_directory']/filename
        if Path(art[key]['path']).parts[-len(tail.parts):] != tail.parts:
            raise ValueError('Artifact run/member differs from target')
    for key in ('config_sha256', 'base_identity', 'frame_layout'):
        supplied = value.get(key)
        if supplied and not str(supplied).startswith('FILL_FROM_') and supplied != art[key]:
            raise ValueError('Reviewed artifact field differs: '+key)
        value[key] = art[key]
    hashes = {key:sha(Path(path).read_bytes()) for key,path in prep_files.items()}
    if hashes != value['preparation_sha256']:
        raise ValueError('Preparation differs from reviewed template')
    receipt = read(prep_files['receipt']); config = read(prep_files['config'])
    if receipt['config_sha256'] != art['config_sha256'] or any(
            config[k] != art[k] for k in ('base_identity','frame_layout')):
        raise ValueError('Preparation artifact identity differs')
    value.update(archive_bytes=int(fields[1]), archive_sha256=fields[2])
    # Keep the reviewed Orchard paths; prep_files are authenticated local copies.
    if set(value['prep_paths']) != set(prep_files) or not value['done']:
        raise ValueError('Require reviewed remote receipt paths')
    write(output, value); checked_binding(output)
    return value


def package_config(operator):
    package = Path(operator)/'package'; public = read(package/'0.json')
    raw = (package/'0.tgz').read_bytes()
    if sha(raw) != public['payload_sha256']:raise ValueError('Payload differs')
    cfg = json.loads(unpack(raw)['9.json'])
    if canonical(cfg) != public['plan_sha256'] or cfg.get('read_extensions') is not True:
        raise ValueError('Require a bound ON package')
    for name,pin in read(package/'PACKAGE.json')['files'].items():
        if sha((package/name).read_bytes()) != pin:raise ValueError('Package file differs: '+name)
    return package, public, cfg


def gate(operator, prepared, proof, config_template, settings_out, config_out):
    package, public, cfg = package_config(operator)
    receipt = read(proof); raw = Path(prepared).read_bytes()
    if (receipt.get('passed') is not True or receipt['plan'] != public['plan_sha256']
            or receipt['payload'] != public['payload_sha256'] or receipt['ready']['settings'] != sha(raw)
            or receipt['operator_sha256'] != sha((package/'a/6.py').read_bytes())):
        raise ValueError('Prepared settings proof differs from adopted package')
    settings = json.loads(raw)
    spec = importlib.util.spec_from_file_location('adopted_operator', package/'a/6.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    descriptor, = module.descriptors(str(package))
    for key in PROFILE_KEYS[:5]:settings[key] = descriptor[key]
    expected = {key:cfg[key] for key in PROFILE_KEYS}
    if {key:settings.get(key) for key in PROFILE_KEYS} != expected:
        raise ValueError('Prepared/adopted read profile differs')
    slots = [i for i,name in enumerate(('processor','vision','sam')) if settings['read_'+name+'_cache']=='on']
    config = read(config_template)
    config.update(enable_caches=slots, read_cache_bytes=settings['read_cache_bytes'],
                  adoption_profile=expected, adoption_plan_sha256=public['plan_sha256'])
    write(settings_out, settings); write(config_out, config)
    return config


SUBMIT_CHECK = '''import hashlib,json,os,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);pool=Path(sys.argv[2]);h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
pub=json.loads((p/'0.json').read_text());proof=json.loads((p/'a/c/CPU.json').read_text())
with tarfile.open(p/'0.tgz') as t:cfg=json.load(t.extractfile('9.json'))
if h(p/'0.tgz')!=pub['payload_sha256']:raise ValueError('Payload differs')
for key in ('passed','entry_sequence_passed','bundle_guard_passed'):
 if proof.get(key) is not True:raise ValueError('CPU receipt failed: '+key)
if (proof['plan']!=pub['plan_sha256'] or proof['payload']!=pub['payload_sha256'] or proof['inputs']!=h(p/'a/1.json') or proof['operator_sha256']!=h(p/'a/6.py')):raise ValueError('CPU receipt binding differs')
memory=proof['memory']
if memory.get('fits') is not True or memory.get('basis')!='fixed_g3t_shapes' or memory.get('read_cache_bytes')!=cfg['read_cache_bytes']:raise ValueError('CPU memory proof differs')
for name in ('dry.json','dry2.json'):
 if json.loads((p/'a'/name).read_text()).get('passed') is not True:raise ValueError('Dry check failed')
if not pool.is_dir() or pool.is_symlink():raise ValueError('Return pool missing or linked')
total=0
def fail(error):raise error
for base,dirs,files in os.walk(str(pool),followlinks=False,onerror=fail):
 for name in dirs+files:
  f=Path(base)/name
  if f.is_symlink():raise ValueError('Unexpected pool symlink')
 for name in files:
  total+=(Path(base)/name).stat().st_size
  if total>75000000:raise ValueError('Return pool exceeds 75 MB')
print(json.dumps(dict(passed=True,pool_bytes=total)))
'''


def operations(operator, binding_path, dry_root, destination):
    package, public, cfg = package_config(operator)
    binding = checked_binding(binding_path)
    if binding != cfg['export_binding']:raise ValueError('Operation binding differs from package')
    if set(binding['prep_paths']) != {'config','receipt','data_receipt'}:
        raise ValueError('Require prep_paths from reviewed target')
    out = Path(destination); out.mkdir(parents=True, exist_ok=False)
    raw = tarbytes({str(p.relative_to(package)):p.read_bytes() for p in package.rglob('*') if p.is_file()})
    (out/'1.tgz').write_bytes(raw); (out/'SHA256').write_text(sha(raw)+'  1.tgz\n')
    for old,new in (('dryres2.py','d.py'),('dry2.py','d2.py')):
        (out/new).write_bytes((Path(dry_root)/old).read_bytes())
    q = shlex.quote
    pre = '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\n'
    pre += 'P='+q('/project/community/jjyeung/okh7/a15_cot_ap'+public['token'])+'\n'
    place = pre+'(cd "$D" && sha256sum -c SHA256)\ntest ! -e "$P"\nmkdir -m 700 "$P"\ntar -xzf "$D/1.tgz" -C "$P"\nchmod 700 "$P/a"\n'
    fill = pre+'export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\n'
    fill += 'OBJECT='+q(binding['object'])+'\ncp '+q(binding['done'])+' "$E/5"\n'
    fill += 'test "$(cat "$E/5")" = '+q(binding['object']+' '+str(binding['archive_bytes'])+' '+binding['archive_sha256'])+'\n'
    for key,n in (('config',7),('receipt',8),('data_receipt',9)):
        fill += 'cp '+q(binding['prep_paths'][key])+' "$E/'+str(n)+'"\n'
        fill += 'test "$(sha256sum "$E/'+str(n)+'" | cut -d\' \' -f1)" = '+q(binding['preparation_sha256'][key])+'\n'
    fill += '''for i in 0 1 2 3; do
  test ! -e "$E/$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"
  mv "$E/$i.partial" "$E/$i"
done
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9"'''
    fill += ' --lineage '+q(binding['lineage'])+' --step '+str(binding['step'])+''' --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
PREP=$(sha256sum "$P/a/6" | cut -d' ' -f1)
/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"
(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)
/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"
printf '%s\\n' 0 > "$P/a/1.txt"
'''
    cpu = pre+'''test "$(cat "$P/a/1.txt")" = 0
test ! -e "$P/a/4.txt"
test ! -e "$P/a/c"
CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \\
 sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 \\
 --job-name="${P##*/}" --cpus-per-task=8 --mem=200G --time=04:00:00 \\
 --exclude='orchard-flame-[0-31],orchard-community-2' --export=ALL --no-requeue --chdir=/tmp \\
 --output="$P/a/4.log" --error="$P/a/4.err" \\
 --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${CPU_REPLY%%;*}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s\\n' "$CPU_JOB" > "$P/a/4.txt"
'''
    submit = pre+'''test ! -e "$P/a/8.txt"
/usr/bin/python3 -I -s -B "$D/check.py" "$P" /project/community/jjyeung/okh7/ae71c903
squeue -u jjyeung -p general -h > "$P/a/9.txt"
test ! -s "$P/a/9.txt"
(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)
JOB_REPLY=$(cd "$P" && /usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 04:30:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\\n' "$JOB" > "$P/a/8.txt"
'''
    fetch = pre+'''JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$P" "$JOB" <<'PY'
import json,sys
from pathlib import Path
print(json.loads((Path(sys.argv[1])/'0.json').read_text())['token']+format(int(sys.argv[2]),'08x'))
PY
)
(cd "$P" && /usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f")
'''
    for name,text in (('o_place.sh',place),('o_pull_fill.sh',fill),('o_cpu.sh',cpu),('o_sub.sh',submit),('o_fetch.sh',fetch)):
        (out/name).write_text(text)
    (out/'check.py').write_text(SUBMIT_CHECK)
    return dict(delivery_sha256=sha(raw), package='/project/community/jjyeung/okh7/a15_cot_ap'+public['token'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable-extensions', action='store_true')
    sub = parser.add_subparsers(dest='action', required=True)
    b = sub.add_parser('binding')
    for key in ('template','artifact','done','config','receipt','data-receipt','out'):b.add_argument('--'+key, required=True)
    o = sub.add_parser('operations')
    for key in ('operator','binding','dry-root','out'):o.add_argument('--'+key, required=True)
    g = sub.add_parser('gate')
    for key in ('operator','prepared','proof','config','settings-out','config-out'):g.add_argument('--'+key, required=True)
    a = parser.parse_args()
    if not a.enable_extensions:parser.error('Preparation is OFF; require --enable-extensions')
    if a.action=='binding':
        result=derive_binding(a.template,a.artifact,a.done,dict(config=a.config,receipt=a.receipt,data_receipt=a.data_receipt),a.out)
    elif a.action=='operations':result=operations(a.operator,a.binding,a.dry_root,a.out)
    else:result=gate(a.operator,a.prepared,a.proof,a.config,a.settings_out,a.config_out)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
