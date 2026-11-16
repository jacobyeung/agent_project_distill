"""Build the source-only upload and native-form embedded batch; submit nothing."""
import argparse
import base64
from copy import deepcopy
import difflib
import hashlib
import gzip
import io
import json
from pathlib import Path
import shlex
import tarfile

import job_support as H

ROOT = Path(__file__).resolve().parent
TOKEN = 'b7e31d84a90c62f5'
WRAPPERS = ('batch_entry.py', 'stage_job.py', 'phase_worker.py', 'job_support.py', 'phase_support.py')
REF = ROOT / 'reference/sj/orch_cd/evalx/work/milestone'

def tar_bytes(files):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as archive:
        for name, raw in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size, item.mode, item.mtime = len(raw), 0o644, 0
            archive.addfile(item, io.BytesIO(raw))
    return output.getvalue()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deadline-unix', default='none',
                        help='Optional absolute cutoff; none uses the allocation duration')
    parser.add_argument('--allocation-seconds', type=int, default=10800)
    args = parser.parse_args()
    assert args.allocation_seconds > 0
    deadline = None if args.deadline_unix.lower() == 'none' else int(args.deadline_unix)
    out = ROOT / 'packet'
    out.mkdir(exist_ok=True)
    family = json.loads((ROOT / 'reference/FAMILY.json').read_text())
    diff = json.loads((ROOT / 'manifest_v2/DIFF.json').read_text())
    plan = json.loads((ROOT / 'INPUTS_PLAN.json').read_text())
    # Reuse the uploaded source bytes; wrapper changes live in the batch payload.
    code = deepcopy(json.loads((out / 'CONFIG.json').read_text())['code'])
    source_name = Path(code['name']).name
    source = out / source_name
    assert source.stat().st_size == code['bytes'] and H.sha(source) == code['sha256']
    assert code['name'] == 'q8/' + TOKEN + '/d6e92a81.tar'
    assert code['bytes'] == 44328960
    assert code['sha256'] == 'e9ffe4aef8b1c6a055b5f7083d1d925ad82760d76e08532bf3a4a3dd200de1e0'
    code.update(generation='1794820770137604', crc32c='lDDvFQ==')
    logical_manifest = '/scratch/jjyeung/a40fbc19.json'
    H.dump(out / 'UPLOAD.json', {k:v for k,v in code.items() if k != 'members'})
    assets = deepcopy(family['assets'])
    # Archive identity remains C8r's; this path is the opaque operator alias.
    assets['base']['path'] = '/project/community/jjyeung/f3069074.tar'
    export = deepcopy(plan['export'])
    for row in export['parts']:
        row['name'] = row.pop('uri').removeprefix('gs://cmu-gpucloud-jjyeung/')
    anchor = deepcopy(plan['anchors'])
    anchor['name'] = anchor.pop('uri').removeprefix('gs://cmu-gpucloud-jjyeung/')
    anchor['generation'] = '1794806692483376'
    anchor['members'] = json.loads((ROOT / 'inputs/anchors.members.json').read_text())
    config = dict(token=TOKEN, assets=assets, code=code, anchors=anchor, export=export,
                  export_destination='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece',
                  manifest=logical_manifest, manifest_sha256=diff['v2_sha256'],
                  manifest_binding_digest=diff['v2_binding_digest'], captures_unchanged=True,
                  tower_binding='/scratch/jjyeung/k1/run_tower_sam_2/BINDING.json',
                  logical_run='/scratch/jjyeung/a7e31d84/r/a',
                  pool='/project/community/jjyeung/okh7/' + TOKEN,
                  pointer='/project/community/jjyeung/okh7/' + TOKEN + '/a.json',
                  cloud='gs://cmu-gpucloud-jjyeung/q8/' + TOKEN + '/r',
                  capture_reserve_seconds=600, return_margin_seconds=900,
                  canary_limit_seconds=3000, allocation_seconds=args.allocation_seconds)
    if deadline is not None:
        config['deadline_unix'] = deadline
    from audit_config import audit
    H.dump(ROOT / 'evidence/REPORT6_FIELD_AUDIT.json', audit(config))
    H.dump(out / 'CONFIG.json', config)
    boot = {name: (ROOT / name).read_bytes() for name in WRAPPERS}
    # Small native wrappers are available before the source upload is staged.
    for relative in ('chain_save.py', 'orchard_stage.py', 'orchard_job.py', 'orchard_results.py',
                     'native_bootstrap.py', 'orchard_native/native_stage.py'):
        boot['reference/sj/orch_cd/evalx/work/milestone/' + relative] = (REF / relative).read_bytes()
    boot['a.json'] = json.dumps(config, sort_keys=True).encode()
    bundle = gzip.compress(tar_bytes(boot), mtime=0)
    assert len(bundle) < 6 * 1024**2
    # Port the native embedded batch verbatim except for opaque names and entrypoint.
    import sys
    sys.path.insert(0, str(REF))
    import orchard_launcher
    script = orchard_launcher.render_batch(bundle, TOKEN)
    script = script.replace('EVALX_BATCH_BOOTSTRAP', 'A7E31D84').replace("('evalx_'+job+", "('a_'+job+")
    before = "str(root/'bootstrap/orchard_job.py'),\n    '--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')"
    assert before in script
    script = script.replace('exec python3 ', 'exec /usr/bin/python3 ', 1)
    script = script.replace(before, "str(root/'batch_entry.py'),str(root)")
    (out / 'a7e31d84.sh').write_text(script)
    command = ['/usr/local/bin/sbatch', '--parsable', '--account=mt01', '--partition=general',
               '--nodes=1', '--ntasks=1', '--gres=gpu:1', '--cpus-per-task=16', '--mem=200G',
               '--time=%02d:%02d:%02d' % (args.allocation_seconds // 3600, args.allocation_seconds // 60 % 60, args.allocation_seconds % 60), '--no-requeue', '--output=/dev/null', '--error=/dev/null',
               '--chdir=/tmp', '--job-name=a15_cot_ap' + TOKEN]
    (ROOT / 'submit_command.txt').write_text('# Operator only, after independent review and orchestrator GO.\n'
        + '# allocation_seconds=' + str(args.allocation_seconds) + '; deadline_unix=' + str(deadline) + '\n'
        + shlex.join(command) + ' < a7e31d84.sh\n')
    (ROOT / 'fetch_command.txt').write_text('# Operator: run through the registered governor stream, never from this build.\n'
        '# Read the opaque pool a.json pointer or the job RETURN_RECEIPT to obtain RETURN_TOKEN and JOB_ID.\n'
        "set -o pipefail\ngcloud storage cat 'gs://cmu-gpucloud-jjyeung/q8/" + TOKEN + "/r/RETURN_TOKEN/result.tar.gz#GENERATION' | pv -q -L 8m > RETURN.tar.gz\n"
        '# Verify its size and SHA256 against EXIT.json before extraction into /scratch.\n')
    comparisons = [(REF / 'orchard_native/native_stage.py', ROOT / 'stage_job.py'),
                   (REF / 'orchard_native/native_job.py', ROOT / 'batch_entry.py'),
                   (REF / 'orchard_native/native_worker.py', ROOT / 'phase_worker.py'),
                   (REF / 'orchard_results.py', ROOT / 'job_support.py')]
    text = ''.join(''.join(difflib.unified_diff(a.read_text().splitlines(True), b.read_text().splitlines(True),
                                              fromfile=str(a.relative_to(ROOT)), tofile=b.name)) for a,b in comparisons)
    (ROOT / 'evidence/wrappers_v2.diff').write_text(text)
    H.dump(out / 'PACKAGE.json', dict(source=code['sha256'], source_bytes=code['bytes'],
        batch_sha256=H.sha(out / 'a7e31d84.sh'), batch_bytes=(out / 'a7e31d84.sh').stat().st_size,
        review_required=True, upload_generations_pending=False, submitted=False))
    ledger = dict(token=TOKEN, purpose='K1 phase own wrapper, prepare only',
        source_object=code['name'], source_sha256=code['sha256'], source_bytes=code['bytes'],
        batch='a7e31d84.sh', batch_sha256=H.sha(out / 'a7e31d84.sh'), batch_bytes=(out / 'a7e31d84.sh').stat().st_size,
        allocation_seconds=args.allocation_seconds, deadline_unix=deadline, return_margin_seconds=900, pool=config['pool'], cloud=config['cloud'],
        manifest_sha256=config['manifest_sha256'], submitted=False)
    (ROOT / 'ORCHARD_LEDGER.pending.jsonl').write_text(json.dumps(ledger, sort_keys=True) + '\n')
    print(json.dumps(dict(source_name=source_name, source_sha256=code['sha256'], upload_bytes=code['bytes'],
        batch_sha256=H.sha(out / 'a7e31d84.sh'), batch_bytes=(out / 'a7e31d84.sh').stat().st_size, files=len(code['members']))))

if __name__ == '__main__':
    main()
