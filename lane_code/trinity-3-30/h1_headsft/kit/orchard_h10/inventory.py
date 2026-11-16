"""Record named, small local metadata; never hash or copy bulk inputs."""
import argparse
import json
from pathlib import Path
from orchard_h10.common import sha, write
from orchard_h10.build import B, K, T


def catalog():
    assets=json.loads((T/'ORCHARD_ASSETS.json').read_text())
    transport=json.loads((T/'TRANSPORT.json').read_text())
    artifact=json.loads((B/'work/n13/obj/m544_artifact.json').read_text())
    result=[]
    def add(name,digest,size,there,source,transfer):
        result.append(dict(name=name,sha256=digest,bytes=size,template_registry=there,source=source,transfer=transfer))
    add('step-544 archive',transport['archive_sha256'],transport['archive_bytes'],'not listed',
        'TRANSPORT.json: four generation-pinned GCS objects; this is cloud availability evidence, not proof of Orchard disk residency',
        'Operator uses the governed Orchard transport to materialize the four pinned objects once; verify whole SHA256. Do not substitute the template D0 fetch_and_stage(), which targets run 359fcc3c.')
    for name in ('artifact','heads','full_weights'):
        member={'artifact':'m544/artifact.json','heads':'m544/heads.pt','full_weights':'m544/full_weights/full_weights.json'}[name]
        size=next(r['size'] for r in transport['members'] if r['name']==member)
        pin=transport['artifact_sha256'] if name=='artifact' else artifact[name]['sha256']
        add(name,pin,size,'not listed','step-544 '+member,'Contained in the step-544 archive; no separate copy.')
    for name in ('work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json',
                 'work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json',
                 'work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl',
                 'work/meta/x/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl',
                 'work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json',
                 'work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/prepared/s1_receipt.json',
                 'work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json',
                 'work/n13/ret/native/paired/request.json',
                 'work/c8r/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py'):
        p=B/name;add('native '+p.name,sha(p),p.stat().st_size,'not listed',str(p),'Included in the code archive; no separate staging.')
    dense=json.loads((B/'work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json').read_text())
    add('dev-S1 RGB',None,dense['rgb_bytes_from_producer_preflight'],'not listed',
        'job 170056; /scratch/jjyeung/devs1_frames on trinity-1-18; every RGB digest is in the pinned FRAMES/DENSE metadata',
        'Operator checks Orchard for an exact archive by manifest first. Otherwise archive once on the owning compute node and transfer at <=8 MB/s, never file-by-file. Archive SHA256 is OPEN; preserve all 32/64 dense frames.')
    add('G3T weights','prefix:d460957b',5300000000,'not listed','trinity-1-18 /scratch/jjyeung/k1/g3t/model.safetensors; b04 STATUS estimate',
        'Obtain the full hash and exact size; governed archive at <=8 MB/s if not already authenticated on Orchard.')
    add('G3T config','prefix:5aeb2acd',None,'not listed','trinity-1-18 /scratch/jjyeung/k1/g3t/config.json',
        'Obtain full hash and size with the G3T archive.')
    add('SAM 3 checkpoint','9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e',None,'not listed',
        'b05 stage/sam3.pt; tree/student_pilot/sam3_tower.py CHECKPOINT_SHA256',
        'Obtain exact size and an authorized accessible source; governed archive at <=8 MB/s. Do not access the stopped 1-13 lane.')
    add('SAM 3 source',None,None,'not listed','upstream revision 5dd401d1c5c1d5c3eedff06d41b77af824517619',
        'Archive the exact reviewed source with vocabulary assets; pin archive size/SHA and every source file through the SAM receipt.')
    add('SAM 3 receipt',None,None,'not listed','b05 lane/code/owngrd/vendor/SAM3_RECEIPT.json; host binding not available here',
        'Obtain the actual receipt, full hash and size; it must bind the checkpoint, upstream revision and source_files.')
    for name in ('selector_head.json','selector_head.safetensors'):
        p=B/'heads/selector/work/run_iso'/name
        # Hash the small JSON; use its authenticated weight pin without opening the tensor file.
        pin=sha(p) if p.suffix=='.json' else json.loads((p.parent/'selector_head.json').read_text())['weights_sha256']
        add('run_iso '+name,pin,p.stat().st_size,'not listed',str(p),
            'Operator archives both files once, verifies the weight digest, and transfers at <=8 MB/s. No tensor file is copied by this build.')
    p=B/'work/n13/obj/model_8005668fc14ce5ee.tar'
    add('original model manifest archive',sha(p),p.stat().st_size,'not listed',str(p),
        'Include this metadata archive in the governed input archive; stage_restore authenticates the member against the original receipt.')
    add('original processor assets',None,7037953,'not listed',str(B/'work/n13/obj/base_small.tgz'),
        'Obtain the archive SHA256; its ~7 MB size is local stat evidence. Unpack config/tokenizer/processor assets, then stage_restore verifies each against the original model manifest. The registry base archive has a different manifest and does not prove these bytes.')
    add('Python environment with torch, torchvision, transformers >=5.12, scipy',None,None,'version set not proven',
        'Template runtime groups below; optional compatible overlay under the stable data root',
        'Reuse the template runtime archives, then supply any missing packages in one authenticated archive and an exact versions receipt. Include SAM dependencies (iopath, portalocker, ftfy, timm, pycocotools, wcwidth) and Python runtime closure. No install or download in the job.')
    for i,group in enumerate(assets['groups']):
        for j,(path,size,digest) in enumerate(group):
            add(f'template runtime {i}/{j}',digest,size,'yes',path,'Reuse in place on Orchard; template copy_parts/unpack stages once on the allocated node.')
    for name in ('base_manifest','bwrap_pin','camera_archive'):
        row=assets[name];add('template '+name,row['sha256'],row.get('bytes'),'yes',row['path'],
            'bwrap is used; base/camera archives are inventory evidence only and are not staged by this job.')
    add('template base archive',None,assets['base_archive_bytes'],'yes',assets['base_archive'],
        'Not used by this job; registry records size and a separate base manifest, not a whole-archive SHA256.')
    for name in ('vnice','terminator'):
        add(name,assets[name+'_sha256'],None,'hash only; path not recorded','ORCHARD_ASSETS.json',
            'Operator supplies the exact logical script path and an authorized policy receipt. Authenticate scripts after runtime staging; workers run under vnice. Never start, stop, or bypass a terminator.')
    return result


def render(package):
    package=Path(package);cfg=json.loads((package/'CONFIG.json').read_text());rows=catalog()
    rows.insert(0,dict(name='code archive',sha256=cfg['payload_sha256'],bytes=(package/'0.tgz').stat().st_size,
        template_registry='new local package',source=str(package/'0.tgz'),transfer='Governed archive upload after ORCH releases GPUs/staging. CONFIG.json payload_pins binds every source member.'))
    write(K/'orchard_h10/INPUT_CATALOG.json',rows)
    lines=['# Orchard staging contract','',
        'No remote presence was checked. “Yes” below means the template registry recorded the exact asset on 2026-11-13; the job reauthenticates its bytes.',
        'The registry does not prove that job 170056’s frames, G3T, SAM 3, selector, or the step-544 export remain staged.',
        '',f'Package: `{package.relative_to(K)}`. Plan SHA256: `{cfg["plan_sha256"]}`.',
        'The code archive contains tree/, h1eval/, auth/, rows/, the dev-S1 item file, reviewed b04 code, parity_kit dependencies and pinned native metadata. It contains no weights or RGB.',
        'CONFIG.json lists every member with size and SHA256; template_pins records the unmodified transport source. TOKENS.json stays on Trinity.',
        '', '| Input | Expected SHA256 | Bytes | Template registry |', '|---|---|---:|---|']
    for r in rows:lines.append(f'| {r["name"]} | `{r["sha256"] or "OPEN"}` | {r["bytes"] if r["bytes"] is not None else "OPEN"} | {r["template_registry"]} |')
    lines+=['','INPUT_CATALOG.json records the source and transfer requirement for every row. OPEN_INPUTS.md lists all inputs without proof of Orchard residency.',
        'Unknown sizes and hashes are explicitly OPEN. Estimates are not authenticated sizes. Production admission requires full hashes and exact byte counts in 1.json.',
        'See OPERATIONS.md for the stable archive layout, login CPU check, submission, return, and resume commands.']
    (K/'orchard_h10/STAGING.md').write_text('\n'.join(lines)+'\n')
    lines=['# Open Orchard inputs','',
        'Production submission is blocked until the operator resolves these rows. This build submitted and uploaded nothing.',
        'Confirm exact existing Orchard archives before transferring. Use one governed archive transfer at a time, at <=8 MB/s through Trinity; no folder or per-file transfers.',
        'Plan more than ~30 GB through the head node with an admin. Prefer the generation-pinned cloud export to bringing the 21.6 GB export through Trinity.', '']
    for r in rows:
        if r['template_registry']!='yes':
            lines += [f'- **{r["name"]}**: {r["bytes"] if r["bytes"] is not None else "OPEN"} bytes; SHA256 `{r["sha256"] or "OPEN"}`. Registry: {r["template_registry"]}. {r["transfer"]} Source: `{r["source"]}`.']
    lines+=['','The real-JSON regression fixture is also unavailable at /dev/shm/jjyeung/h1tmp/from118. It is a local validation input, not an Orchard runtime dependency.']
    (K/'orchard_h10/OPEN_INPUTS.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('package');a=p.parse_args();render(a.package)
