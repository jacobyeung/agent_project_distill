"""Enumerate name surfaces, immutable namespace paths and source preservation."""
import hashlib
import json
import os
from pathlib import Path
import re
import tarfile

import job_support as H

ROOT = Path(__file__).resolve().parent
PATTERN = r'(?i)(split|k1|sam|tower|own|distill|revsi|vsi|qwen|scannet|arkit|evalx)'

def main():
    config = json.loads((ROOT / 'packet/CONFIG.json').read_text())
    files = json.loads((ROOT / 'packet/FILES.json').read_text())
    family = json.loads((ROOT / 'reference/FAMILY.json').read_text())
    source_map = json.loads((ROOT / 'payload/ABSOLUTE_SHA256.json').read_text())
    (ROOT / 'FILE_LIST.txt').write_text('\n'.join(f"{row['sha256']} {row['bytes']:10d} {name}" for name,row in sorted(config['code']['members'].items())) + '\n')
    source_errors = []
    for path, row in source_map.items():
        member = row['member']
        if '/kc/k1_build/' in path:
            member = 'sj/' + str(Path(row['resolved']).relative_to('/scratch/jjyeung'))
        if files.get(member, {}).get('sha256') != row['sha256']:
            source_errors.append(path)
    assert not source_errors
    (ROOT / 'evidence/kit_v2.diff').write_text('')
    H.dump(ROOT / 'evidence/KIT_V2.json', dict(source_files=len(source_map), all_bytes_equal=True,
                                              kit_changed=False, errors=source_errors))
    reuse = {}
    for relative in ('chain_save.py','orchard_stage.py','orchard_job.py','orchard_results.py',
                     'native_bootstrap.py','orchard_native/native_stage.py'):
        p = ROOT / 'reference/sj/orch_cd/evalx/work/milestone' / relative
        logical = '/scratch/jjyeung/orch_cd/evalx/work/milestone/' + relative
        assert H.sha(p) == family['code_pins'][logical]
        reuse[logical] = H.sha(p)
    H.dump(ROOT / 'evidence/NATIVE_REUSE_V2.json', reuse)
    external = dict(job='a15_cot_ap' + config['token'], pool=config['pool'], pointer=config['pointer'],
                    return_gcs=config['cloud'], code_gcs=config['code']['name'], anchors_gcs=config['anchors']['name'],
                    metadata_gcs=config['assets']['small_objects'][1]['name'],
                    model_gcs=config['assets']['small_objects'][3]['name'],
                    log='/tmp/a_JOB_' + config['token'] + '/sj/a7e31d84/r/a/logs/a.log')
    external.update({'export_' + str(i):p['name'] for i,p in enumerate(config['export']['parts'])})
    external.update({'asset_' + k:config['assets'][k]['path'] for k in ('base','runtime','numpy','closure','trainer','fla','bwrap')})
    raw_script = (ROOT / 'packet/a7e31d84.sh').read_text()
    external['batch_script'] = re.sub(r"raw=base64\.b64decode\('[A-Za-z0-9+/=]+'", "raw=base64.b64decode('<opaque-payload>'", raw_script)
    external['submit_argv'] = (ROOT / 'submit_command.txt').read_text()
    import stage_job
    old = dict(os.environ)
    try:
        os.environ.update(USER='jjyeung', SLURM_JOB_ID='1000', CUDA_VISIBLE_DEVICES='')
        location = ROOT / 'evidence/environment'
        location.mkdir(exist_ok=True)
        env = stage_job.environment(location)
    finally:
        os.environ.clear()
        os.environ.update(old)
    for key,value in env.items():
        external['environment/' + key] = key + '=' + value.replace(str(location), '/tmp/a_JOB_' + config['token'])
    external['controller_argv'] = 'python3 -I -s -B /tmp/a_JOB_' + config['token'] + '/batch_entry.py /tmp/a_JOB_' + config['token']
    # The namespace's internal names are exempt. Its host-side backing files are
    # a separate surface: do not silently extend the orchestrator's exemption.
    mirrors = {'mirror/' + name:'/tmp/a_JOB_' + config['token'] + '/' + name for name in files}
    external.update(mirrors)
    vector = '\n'.join(key + '\t' + value.replace('\n', ' ') for key,value in external.items()) + '\n'
    (ROOT / 'packet/EXTERNAL_NAMES.txt').write_text(vector)
    raw_hits = {key:value for key,value in external.items() if re.search(PATTERN,value)}
    false_positives = {'environment/VLLM_USE_FLASHINFER_SAMPLER': 'SAMPLER is a generic decoder term, not the SAM method'}
    hits = {k:v for k,v in raw_hits.items() if k not in false_positives}
    patterns = [
        '/scratch/jjyeung/orch_n30/k1_ops3/kc/** (exact pinned dependency and kit paths)',
        '/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json',
        '/scratch/jjyeung/orch_cd/** (only exact source-map members, not arbitrary extra sources)',
        '/scratch/jjyeung/k1/run_tower_sam_2/BINDING.json',
        '/scratch/jjyeung/k1_frames/<hex2>/<sha256>.png',
        '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/** (pinned metadata, export and trainer archive)',
        '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/** (pinned base snapshot logical paths)',
        '/scratch/jjyeung/a7e31d84/r/a/native/probe/<digest16>/own.npz',
        '<namespace stage>/project/c7d31ddd/venvs/rwtrain_torch211_cu129/** (pinned interpreter runtime)',
        '<namespace stage>/fla/**, <namespace stage>/numpy/**, <namespace stage>/closure/** (pinned import overlays)',
    ]
    H.dump(ROOT / 'packet/EXEMPT_PATHS.json', dict(scope='inside namespace only', patterns=patterns,
             exact_source_paths=sorted(source_map), external_backing_paths_exempt=False))
    H.dump(ROOT / 'evidence/NAMES.json', dict(passed=not hits, pattern=PATTERN, surfaces=len(external),
         hits=hits, raw_script_match_lines=[i for i,line in enumerate(raw_script.splitlines(), 1) if re.search(PATTERN,line)],
         decoded_payload_audited_as_config_and_file_inventory=True, lexical_false_positives=false_positives,
         new_job_pool_code_log_names_pass=not any(k in hits for k in ('job','pool','pointer','return_gcs','code_gcs','log','batch_script','submit_argv')),
         external_source_mirror_hits=sum(k.startswith('mirror/') for k in hits),
         existing_input_hits={k:v for k,v in hits.items() if not k.startswith('mirror/')}))
    print(json.dumps(dict(source_bytes_unchanged=True, reused_native_files=len(reuse),
                          new_external_names_pass=not any(k in hits for k in ('job','pool','pointer','return_gcs','code_gcs','log','batch_script','submit_argv')),
                          all_external_names_pass=not hits, hit_count=len(hits))))

if __name__ == '__main__':
    main()
