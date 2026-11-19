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

# Read A/job 173060, package a15_cot_apdc76460c3a164; override with --bound-export.
DEFAULT_BOUND_EXPORT = {'archive_sha256': 'dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5', 'artifact': {'bytes': 11474, 'sha256': '5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd'}, 'config_sha256': '9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4', 'full_weights': {'bytes': 1794, 'sha256': '1de983c9839c1ed25a9113bb5d3b473eaa8be6ae914d9227b143fdc6dd80334c'}, 'heads': {'bytes': 2763214343, 'sha256': 'e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7'}, 'lineage': 'SFT', 'member_directory': 'm400', 'object': 'q8/8865619b/6ed2c7aa_m400.tar', 'preparation': {'config': {'bytes': 20569, 'path': 'p0/config.json', 'sha256': 'b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad', 'source_path': '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'}, 'data_receipt': {'bytes': 73933, 'path': 'p0/data_receipt.json', 'sha256': '03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47', 'source_path': '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa/inputs/data_receipt.json'}, 'receipt': {'bytes': 86401, 'path': 'p0/receipt.json', 'sha256': 'a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda', 'source_path': '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json'}}, 'run': '6ed2c7aa', 'schema': 'h1-export-pins-v1', 'step': 400}

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


def gate(operator, prepared, proof, config_template, settings_out, config_out, asset_receipts=None, bound_export=None):
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
    paths = (dict(restore=Path(asset_receipts)/'RESTORE.json',binding=Path(asset_receipts)/'binding.json',
                  export_pin=Path(asset_receipts)/'EXPORT_PIN.json') if asset_receipts else
             dict(restore=Path(config['export'])/'RESTORE.json',binding=Path(config['artifact_manifest']),
                  export_pin=Path(config['export_pin'])))
    assets = {key:sha(path.read_bytes()) for key,path in paths.items()}
    inputs_path = Path(asset_receipts)/'1.json' if asset_receipts else package/'a/1.json'
    if sha(inputs_path.read_bytes()) != receipt['inputs']:
        raise ValueError('Gate input evidence differs from CPU proof')
    export_pin = read(inputs_path)['export_pin']
    if (export_pin['path'] != 'a/export.json' or assets['export_pin'] != export_pin['sha256']
            or paths['export_pin'].stat().st_size != export_pin['bytes']):
        raise ValueError('Staged export pin bytes differ from CPU inputs')
    if any(assets[key] != receipt['ready'][key] for key in ('restore','binding')):
        raise ValueError('Staged assets differ from CPU READY pins')
    identity = read(paths['export_pin']); binding = cfg['export_binding']
    if any(identity.get(key) != binding[key] for key in
           ('run','step','member_directory','lineage','object','config_sha256','archive_sha256')) or any(
            identity.get('preparation',{}).get(key,{}).get('sha256') != digest
            for key,digest in binding['preparation_sha256'].items()):
        raise ValueError('Staged export identity differs from adopted step binding')
    selected = read(bound_export) if bound_export else DEFAULT_BOUND_EXPORT
    if identity != selected:
        raise ValueError('Staged export differs from selected export (default: reviewed step 400)')
    config.update(enable_caches=slots, read_cache_bytes=settings['read_cache_bytes'],
                  adoption_profile=expected, adoption_plan_sha256=public['plan_sha256'],
                  adoption_kit=cfg['gate_kit_sha256'],
                  adoption_assets=assets, required_device_type='H100_80GB')
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
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['bundle_guard_passed'] is True and c['entry_sequence_passed'] is True
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
g=c['bundle_guard']
assert g['passed'] is True and g['path']=='7.py' and g['guard_target']=='6.py' and g['action']=='test'
assert g['operator_sha256']==sha(p/'a/6.py') and g['batch_sha256']==sha(p/'BATCH.sh')
e=c['entry_sequence'];root=Path(c['root'])
assert e['passed'] is True and e['entry_sequence_passed'] is True
assert e['events']==['guard_installed','write_test','operator_dispatch']
assert e['operator_sha256_before']==e['operator_sha256_after']==c['operator_sha256']
assert e['path']=='7.py' and e['guard_target']=='6.py' and e['action']=='test'
assert e['operator_sha256']==c['operator_sha256'] and e['batch_sha256']==sha(p/'BATCH.sh')
assert e['pool']==str(root/'wpool') and e['token']==v['token']
w=e['write_test']
assert type(w['bytes']) is int and w['bytes']==4*1024**2
assert isinstance(w['sha256'],str) and len(w['sha256'])==64 and all(ch in '0123456789abcdef' for ch in w['sha256'])
with tarfile.open(p/'0.tgz') as archive:
    guard_sha=hashlib.sha256(archive.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
assert e['guard_target_sha256']==guard_sha
assert {k:v for k,v in e.items() if k!='entry_sequence_passed'}==g
assert e['requested_argv'][-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]
assert e['dispatched_argv']==e['requested_argv'][:-2]+[str(root/'7.py'),str(root/'a/1.json')]
m=c['memory']
assert m==json.loads((p/'a/c/MEMORY.json').read_text())
assert m['fits'] is True and m['basis']=='fixed_g3t_shapes'
assert m['perception_memo_modules']==['g3t'] and m['sam_measurement_required'] is False
print('All CPU receipt checks passed')
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
def decode(v):
 if isinstance(v,str):return bytes.fromhex(v[1:]).decode() if v.startswith('u') else (_ for _ in ()).throw(ValueError('Invalid gate token'))
 if isinstance(v,dict):return {decode(k):decode(x) for k,x in v.items()}
 if isinstance(v,list):return [decode(x) for x in v]
 return v
gate=decode(json.loads((p/'a/g.json').read_text())['u0'])
keys=('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth','read_processor_only','read_processor_cache','read_vision_cache','read_sam_cache','read_cache_bytes')
expected={k:cfg[k] for k in keys}
if (gate.get('passed') is not True or gate.get('adoption_plan_sha256')!=pub['plan_sha256'] or gate.get('required_device_type')!='H100_80GB' or json.dumps(gate.get('adoption_profile'),sort_keys=True)!=json.dumps(expected,sort_keys=True)):raise ValueError('GPU gate differs from adopted plan/profile/device')
assets=dict(restore=proof['ready']['restore'],binding=proof['ready']['binding'],export_pin=h(p/'a/export.json'))
if gate.get('adoption_assets')!=assets:raise ValueError('GPU gate assets differ from CPU proof')
if gate.get('adoption_kit')!=cfg['gate_kit_sha256']:raise ValueError('GPU gate kit/comparator/sample differ from MANIFEST pins')
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
    fill = pre+'''if [ "${1:-}" != --worker ]; then
  mkdir -m 700 "$P/a/0.lock"
  test ! -e "$P/a/1.txt"
  nohup bash "$0" --worker </dev/null >"$P/a/0.log" 2>&1 &
  printf '%s\\n' "$!" > "$P/a/0.txt"
  exit 0
fi
test -d "$P/a/0.lock"
fin(){ rc=$?; printf '%s\\n' "$rc" > "$P/a/1.txt"; exit "$rc"; }
trap fin EXIT
'''
    fill += 'export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\n'
    fill += 'OBJECT='+q(binding['object'])+'\ncp '+q(binding['done'])+' "$E/5"\n'
    fill += '/usr/bin/python3 -I -s -B -c '+q('import sys; from pathlib import Path; assert Path(sys.argv[1]).read_text().split() == sys.argv[2:]')+' "$E/5" '+q(binding['object'])+' '+str(binding['archive_bytes'])+' '+q(binding['archive_sha256'])+'\n'
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
    g.add_argument('--asset-receipts',help='Exact CPU-emitted asset receipts; workers recheck the staged files')
    g.add_argument('--bound-export',help='Reviewed export.json; defaults to the pinned step-400 export from read A/job 173060')
    a = parser.parse_args()
    if not a.enable_extensions:parser.error('Preparation is OFF; require --enable-extensions')
    if a.action=='binding':
        result=derive_binding(a.template,a.artifact,a.done,dict(config=a.config,receipt=a.receipt,data_receipt=a.data_receipt),a.out)
    elif a.action=='operations':result=operations(a.operator,a.binding,a.dry_root,a.out)
    else:result=gate(a.operator,a.prepared,a.proof,a.config,a.settings_out,a.config_out,a.asset_receipts,a.bound_export)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
