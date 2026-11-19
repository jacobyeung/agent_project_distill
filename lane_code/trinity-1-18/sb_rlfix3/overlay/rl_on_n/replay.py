"""Authenticate A4's m200 export and select recorded replay items without inference."""
from pathlib import Path
import hashlib
import json
import os
import sys
from . import provenance as P
from .serving import A4, PAYLOAD, PINS

TYPES=('camera_displacement','camera_rotation','camera_movement_direction',
       'object_abs_distance','room_size_estimation')
# Recorded reads whose calls reach SAM 3 and the selector, and reads whose budget forced the close.
REQUIRED={'gap':('vsi590k_042674','vsi590k_042690','vsi590k_042715','vsi590k_042717'),
          'budget_fired':('vsi590k_044622','vsi590k_161806')}
COUNTS={**{t:4 for t in TYPES},**{group:len(ids) for group,ids in REQUIRED.items()}}
DEVICE='NVIDIA H100 80GB HBM3'


def call_records(output):
    calls=output.get('calls',[])
    return calls['records'] if isinstance(calls,dict) else calls


def exercises(group,output):
    """Whether one decoded read reaches the path its replay group must cover."""
    if group=='gap':
        families=[c.get('family') for c in call_records(output)]
        return families.count('ground')>=2 and 'gap' in families
    if group=='budget_fired':
        return bool(output.get('decode_budget',{}).get('fired'))
    return True


def selection():
    manifest=P.load(PAYLOAD/'items/devs1_routed.json')
    items={r['id']:r for r in manifest['items']}
    wanted={identifier:group for group,ids in REQUIRED.items() for identifier in ids}
    chosen={group:[] for group in COUNTS};seen=set()
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
                if typ not in TYPES:continue
                if identifier in seen:raise ValueError('Duplicate A4 journal item: '+identifier)
                seen.add(identifier)
                group=wanted.get(identifier,typ)
                if len(chosen[group])==COUNTS[group]:continue
                if identifier not in items:raise ValueError('MISSING recorded item: '+identifier)
                item=items[identifier];output=row['output']
                if item['question_type']!=typ or not isinstance(output.get('tokens'),list):
                    raise ValueError('A4 item/journal type or token mismatch: '+identifier)
                if not exercises(group,output):
                    raise ValueError('A4 journal item does not exercise '+group+': '+identifier)
                chosen[group].append(dict(group=group,item=item,expected=output,journal=str(path),
                                         journal_sha256=P.INPUTS[str(path.resolve())]))
    for group,rows in chosen.items():
        if len(rows)!=COUNTS[group]:
            raise ValueError(f'MISSING {COUNTS[group]} A4 journal items for {group}: found {len(rows)}')
    return [row for group in COUNTS for row in chosen[group]]


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


def export_identity(export_dir):
    """Original export pins of a restore; training must start from the export the replay read."""
    restore=P.load(Path(export_dir)/'RESTORE.json')
    return {name:restore['original'][name]['sha256'] for name in ('artifact','heads','full_weights','config')}


def require_scratch(paths, resolve=True):
    """Replay inputs and interpreter stay on node-local /scratch."""
    for name,path in paths.items():
        value=Path(path).resolve() if resolve else Path(os.path.abspath(path))
        if not str(value).startswith('/scratch/'):
            raise ValueError(f'{name} must be under /scratch: {path}')


def require_interpreter():
    require_scratch({'RL_PYTHON':sys.executable,'sys.prefix':sys.prefix},resolve=False)


def require_card(name):
    if name!=DEVICE:raise ValueError(f'Replay requires {DEVICE}, A4\'s recorded card; found {name}')


def replay_key(**parts):
    return hashlib.sha256(P.canonical(parts).encode()).hexdigest()


def matched_items(path, key):
    """Matched items appended by an earlier replay with the same key; partial or foreign lines are ignored."""
    done={}
    if Path(path).is_file():
        for line in Path(path).read_text().splitlines():
            try:row=json.loads(line)
            except ValueError:continue
            if row.get('key')==key and row.get('match') is True:done[row['id']]=row
    return done


def append_item(path, row):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
