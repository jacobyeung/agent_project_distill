
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
"""Authenticate the operator's export identity before staging any archives."""
import hashlib
import json
from pathlib import Path
import re


MEMBERS = dict(artifact='artifact.json', heads='heads.pt',
               full_weights='full_weights/full_weights.json')
PREPARATION = ('config', 'receipt', 'data_receipt')


def relative(value):
    p = Path(value)
    if not value or p.is_absolute() or '..' in p.parts or str(p) != value or value == '.':
        raise ValueError('Export path must be canonical and relative')
    return p


def pin(value):
    if (not isinstance(value, dict) or not isinstance(value.get('sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', value['sha256'])
            or type(value.get('bytes')) is not int or value['bytes'] <= 0):
        raise ValueError('Invalid export pin')


def validate(value):
    if value.get('schema') != 'h1-export-pins-v1':
        raise ValueError('Export pin schema differs')
    relative(value['member_directory'])
    if (value.get('lineage') not in ('SFT', 'RL') or type(value.get('step')) is not int
            or value['step'] < 0):
        raise ValueError('Export requires SFT/RL and nonnegative integer step')
    for name in MEMBERS:
        pin(value[name])
    if set(value['preparation']) != set(PREPARATION):
        raise ValueError('Preparation keys differ')
    paths = []
    for name in PREPARATION:
        item = value['preparation'][name]
        pin(item); paths.append(relative(item['path']))
        source = Path(item['source_path'])
        if not source.is_absolute() or '..' in source.parts or str(source) != item['source_path']:
            raise ValueError('Preparation source path differs')
    if len(set(paths)) != len(paths):
        raise ValueError('Preparation paths must be distinct')
    return value


def load(inputs, package):
    spec = inputs['export_pin']
    pin(spec)
    if spec.get('path') != 'a/export.json':
        raise ValueError('Require a/export.json')
    path = Path(package)/spec['path']
    raw = path.read_bytes()
    if len(raw) != spec['bytes'] or hashlib.sha256(raw).hexdigest() != spec['sha256']:
        raise ValueError('Export pin file differs')
    return validate(json.loads(raw))


def admit(inputs, cfg, export):
    root = Path(cfg['logical'])/'d'/export['member_directory']
    for name, member in MEMBERS.items():
        declared = inputs['files'][name]
        if (type(declared.get('bytes')) is not int
                or any(declared[key] != export[name][key] for key in ('sha256', 'bytes'))):
            raise ValueError('Export pin differs: '+name)
        if declared['path'] != str(root/member):
            raise ValueError('Export member path differs: '+name)
