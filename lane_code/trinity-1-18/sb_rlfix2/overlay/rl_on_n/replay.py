"""Authenticate A4's m200 export and select recorded replay items without inference."""
from pathlib import Path
import json
from . import provenance as P
from .serving import A4, PAYLOAD, PINS

TYPES=('camera_displacement','camera_rotation','camera_movement_direction',
       'object_abs_distance','room_size_estimation')


def selection():
    manifest=P.load(PAYLOAD/'items/devs1_routed.json')
    items={r['id']:r for r in manifest['items']}
    chosen={t:[] for t in TYPES};seen=set()
    journals=sorted((A4/'ret/metadata/reads/0/metadata/journals').glob('*/0/items.jsonl'))
    if not journals:raise ValueError('MISSING A4 journals: '+str(A4/'ret/metadata/reads/0/metadata/journals/*/0/items.jsonl'))
    for path in journals:
        P.sha(path)
        env=P.load(path.with_name('environment.json'))
        if env['binding']['step']!=200 or env['binding']['lineage']!='SFT':
            raise ValueError('Journal is not A4 m200: '+str(path))
        with path.open() as stream:
            for line in stream:
                row=json.loads(line)
                if row['arm']!='tower' or row['mode']!='none' or not row.get('complete'):continue
                typ=row['type'];identifier=row['id']
                if typ not in chosen:continue
                if identifier in seen:raise ValueError('Duplicate A4 journal item: '+identifier)
                seen.add(identifier)
                if len(chosen[typ])==4:continue
                if identifier not in items:raise ValueError('MISSING recorded item: '+identifier)
                item=items[identifier];output=row['output']
                if item['question_type']!=typ or not isinstance(output.get('tokens'),list):
                    raise ValueError('A4 item/journal type or token mismatch: '+identifier)
                chosen[typ].append(dict(item=item,expected=output,journal=str(path),
                                       journal_sha256=P.INPUTS[str(path.resolve())]))
    for typ,rows in chosen.items():
        if len(rows)!=4:raise ValueError('MISSING four A4 journal items for '+typ)
    return [row for typ in TYPES for row in chosen[typ]]


def check_export(export_dir, config):
    """Check restored identities and actual original bytes against EXPORT_PIN.json."""
    pin=P.load(P.checked(dict(path=str(A4/PINS['export_pin'][0]),sha256=PINS['export_pin'][1])))
    if (pin['member_directory'],pin['step'],pin['lineage'])!=('m200',200,'SFT'):
        raise ValueError('Expected A4 m200 SFT export')
    directory=Path(export_dir);restore=P.load(directory/'RESTORE.json')
    for name in ('artifact','heads','full_weights'):
        original=restore['original'][name]
        if original['sha256']!=pin[name]['sha256']:
            raise ValueError('MISSING A4 m200 export at '+str(directory)+': RESTORE.original.'+name+' differs from EXPORT_PIN.json')
        P.checked(original)
    if restore['original']['config']['sha256']!=pin['preparation']['config']['sha256']:
        raise ValueError('MISSING A4 m200 preparation at '+str(config))
    P.checked(dict(path=str(config),sha256=pin['preparation']['config']['sha256']))
    for name,spec in restore['local'].items():P.checked(dict(path=str(directory/name),sha256=spec['sha256']))
    artifact=P.load(directory/'artifact.json')
    if artifact['config_sha256']!=pin['config_sha256']:raise ValueError('m200 config identity differs')
    for name in ('heads','full_weights'):P.checked(artifact[name])
    return pin
