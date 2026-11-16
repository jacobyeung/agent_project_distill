"""Eight real own-head reads: four routed types, each baseline plus one registered mode."""
import argparse
import json
import os
from pathlib import Path
import time
from h1eval.items import K, load_manifest, sha, digest
from h1eval.scorers import records
from .launch import reader_factory, write_json
from .parity_adapter import ENTRY, DEFAULT_SETTINGS, settings_for, map_items, artifact_spec, prepare_runtime, validate_own_settings

MODES = {
    'camera_displacement': {'name': 'scale_translation', 'k': 2.},
    'camera_movement_direction': {'name': 'rotate_translation', 'deg': 180.},
    'camera_rotation': {'name': 'negate_turn'},
    'object_abs_distance': {'name': 'scale_scene', 'k': 2.},
}


def run(a, *, maker=None):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU first batch requires CUDA_VISIBLE_DEVICES=""')
    manifest = load_manifest(a.items)
    if manifest['name'] != 'devs1_routed':
        raise ValueError('CPU first batch requires devs1_routed')
    factory = maker or reader_factory(a.reader_root, a.reader_entry)
    settings = settings_for(a.settings, manifest['name'])
    export = a.export or settings['export_dir']
    artifact = a.artifact_manifest or settings['artifact_manifest']
    if Path(export).resolve() != Path(settings['export_dir']).resolve():
        raise ValueError('Settings export_dir differs')
    spec = artifact_spec(artifact) if isinstance(artifact, (str, Path)) else artifact
    expected = settings['artifact_manifest']
    if isinstance(expected, str):expected = artifact_spec(expected)
    if spec != expected:raise ValueError('Settings artifact binding differs')
    mapped, mapping = map_items(manifest['items'], settings, name=manifest['name'])
    selected = [next(r for r in manifest['items'] if r['question_type'] == kind) for kind in MODES]
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        # Host wrappers pre-create only cache directories and their redirected log.
        if any(p.name not in ('tmp','cache','hf','torch','triton','inductor','log') for p in out.iterdir()):
            raise ValueError('CPU receipt requires a fresh output directory')
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'item_mapping.json', mapping)
    report = dict(device='cpu', settings_file_sha256=sha(a.settings), settings_sha256=digest(settings),
                  settings=settings, mapping_sha256=mapping['sha256'],
                  items=[], passed=False)
    write_json(out / 'FIRST_BATCH.json', report)
    if maker is None:
        validate_own_settings(settings, selected)
        prepare_runtime(settings)
    from .perception_own import configured
    mode = {'name': 'none'}
    bound = []
    def own_factory(**kwargs):
        p = configured(mode, settings=settings)(**kwargs)
        bound[:] = [p]
        return p
    start = time.perf_counter()
    generator = None
    try:
        generator = factory(export, spec, [mapped[r['id']] for r in selected],
                            perception_factory=own_factory, device='cpu', settings=settings)
        report['load_seconds'] = time.perf_counter() - start
        for item in selected:
            for mode in ({'name': 'none'}, MODES[item['question_type']]):
                t = time.perf_counter()
                output = generator(mapped[item['id']])
                calls = records(output)
                finite = bound[-1].last['finite_heads']
                row = dict(id=item['id'], key=output['key'], type=item['question_type'], mode=mode,
                           text=output['text'], finish=output['finish'], calls=calls,
                           served=sum(bool(r.get('served')) for r in calls),
                           unserved=sum(not r.get('served') for r in calls),
                           seconds=time.perf_counter()-t, timings=output.get('timings', {}),
                           finite_heads=finite, intervention=bound[-1].last['intervention'])
                report['items'].append(row)
                write_json(out / 'FIRST_BATCH.json', report)
                print(json.dumps(row, allow_nan=False), flush=True)
        report['passed'] = len(report['items']) == 8 and all(
            all(r['finite_heads'].values()) for r in report['items'])
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        report['elapsed_seconds'] = time.perf_counter()-start
        write_json(out / 'FIRST_BATCH.json', report)
        if callable(getattr(generator, 'close', None)):generator.close()
    return report


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-root', required=True)
    p.add_argument('--settings', default=DEFAULT_SETTINGS)
    p.add_argument('--export');p.add_argument('--artifact-manifest')
    p.add_argument('--items', default=str(K/'items/devs1_routed.json'))
    p.add_argument('--reader-entry', default=ENTRY)
    p.add_argument('--out', required=True)
    return p


def main(argv=None):
    p = parser();a = p.parse_args(argv)
    try:run(a);return 0
    except (ValueError, FileNotFoundError, ImportError) as error:p.exit(2, str(error)+'\n')

if __name__ == '__main__':raise SystemExit(main())
