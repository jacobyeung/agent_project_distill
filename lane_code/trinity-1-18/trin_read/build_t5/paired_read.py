"""Pinned e193 protocol with independently selected model weights; no GPU imports."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import trinity_read as T

CAMERA = T.SJ/'orch_cd/evalx/work/camera'
REGISTRY_SHA = 'ed50d0ed9e7d5e8eb7edf01207353af77fe31ebf53f69d3c7da1455c0051fa7a'
CONTRACT_SHA = 'de37837d33638f844983d0c0a1a92c6594d1f910671c91ba70067e8ece4a7fa4'
LEG_SHA = 'd16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a'


def contract(family):
    path = Path(__file__).with_name('e193_contract.json')
    if T.sha(path) != CONTRACT_SHA:
        raise ValueError('e193 contract changed')
    return T.load(path)[family]


def select_model(root, config, slot):
    path = T.physical(root, CAMERA/'models.json')
    if T.sha(path) != REGISTRY_SHA:
        raise ValueError('Camera model registry changed')
    models = T.load(path)
    if slot not in ('cp1m200', 'f17'):
        raise ValueError('Unknown model slot')
    if config['spec']['models']['base'] != models['base']:
        raise ValueError('Base snapshot differs')
    spec = config['spec']
    spec['model_slot'] = slot
    spec['artifact'] = copy.deepcopy(models[slot])
    # cp1m200 names the accepted protocol, not the weight identity.
    spec['models'] = dict(base=models['base'], cp1m200=models[slot])
    spec['step'] = 200 if slot == 'cp1m200' else None
    spec['model_identity'] = dict(slot=slot, source=str(CAMERA/'models.json'),
                                  registry_sha256=REGISTRY_SHA, spec=models[slot])
    return config


def rebind(cfg):
    cfg['binding'] = hashlib.sha256(json.dumps(
        {k:v for k,v in cfg.items() if k not in ('binding', 'output')}, sort_keys=True).encode()).hexdigest()


def validate_protocol(cfg, family):
    accepted = contract(family)
    for key in ('cells', 'max_tokens', 'temperature', 'thinking', 'max_model_len',
                'max_seqs', 'inflight', 'engine_version', 'gpus', 'source_sha256'):
        if cfg[key] != accepted[key]:
            raise ValueError('e193 protocol differs: '+key)
    for key in ('pins', 'timing_version', 'fps_rule', 'timing_authority_sha256',
                'adapter_sha256', 'code_pins_sha256'):
        if cfg['devs1'][key] != accepted['devs1'][key]:
            raise ValueError('e193 payload differs: '+key)
    if cfg['legs1']['decision_arm'] != 'B2048':
        raise ValueError('e193 decision arm differs')


class Bridge:
    """Keep the CP1 duplicate cell and budget code for every weight source."""
    def __init__(self, reader, family, spec, camera=None):
        self.family, self.spec = family, spec
        self.reader = Path(reader)
        sys.path.insert(0, str(self.reader/'out'))
        import direct
        if T.sha(direct.__file__) != LEG_SHA:
            raise ValueError('LEG reader changed')
        self.leg = direct
        self.__file__ = __file__
        if family == 'camera':
            self.camera = Path(camera or CAMERA)
            for name, pin in contract('camera')['camera_leg']['generation_code_pins'].items():
                if T.sha(self.camera/name) != pin:
                    raise ValueError('Camera code pin differs: '+name)
            sys.path.insert(0, str(self.camera/'vendor/r5'))
            import adapter
            if Path(adapter.__file__).resolve() != (self.camera/'vendor/r5/adapter.py').resolve():
                raise ValueError('Use a fresh process per family')
            self.vendor = adapter
            self.origin = adapter.R4
            self.PAYLOADS = {'camera': self.camera/'payload'}
        else:
            self.vendor, _ = direct.modules()
            self.origin = self.vendor.R3
            self.PAYLOADS = direct.PAYLOADS
        self.vendor.R3.check_model_specs = self.vendor.R4.check_model_specs = self.model_specs
        self.vendor.R4.legacy_adapter = lambda: self.vendor.R3

    def modules(self):
        return self.vendor, None

    def model_specs(self, models, model):
        if model != 'cp1m200' or models != self.spec['models']:
            raise ValueError('Bound weights differ from selected model')
        pin = models[model]
        if pin['kind'] == 'c1_export':
            self.leg.model_specs(models, model)
        elif pin['kind'] == 'archive':
            accepted = T.load(Path(__file__).with_name('e193_contract.json'))['main']['models']['base']
            if models['base'] != accepted or pin != dict(kind='archive',
                    path=str(T.AP/'bdad3598/k/f17.tar'),
                    sha256='47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae'):
                raise ValueError('Unpinned archive or base')
        else:
            raise ValueError('Unsupported model kind')

    def bind(self, args):
        self.origin.bind(NS(payload=str(self.PAYLOADS[self.family]), dest=args.dest, kit=args.kit,
                            cell='cp1m200', models=args.models, frames_root=args.frames_root, dry=True))
        dest = Path(args.dest); cfg = T.load(dest/'request.json')
        leg = copy.deepcopy(contract(self.family)['legs1'])
        pin = self.spec['artifact']
        leg.update(artifact={k:pin[k] for k in ('path', 'sha256')},
                   step=self.spec['step'], name='LEG-S1-m'+str(self.spec['step']) if self.spec['step'] else 'LEG-S1-f17',
                   export_verification=None, export_bytes_verified=False)
        cfg['legs1'] = leg
        cfg['trinity_binding'] = dict(wrapper_sha256=T.sha(__file__), contract_sha256=CONTRACT_SHA)
        if self.family == 'camera':
            cfg['camera_leg'] = copy.deepcopy(contract('camera')['camera_leg'])
            cfg['camera_leg']['wrapper_sha256'] = T.sha(__file__)
        validate_protocol(cfg, self.family)
        rebind(cfg)
        T.dump(dest/'request.json', cfg)

    def check_export(self, path, pin, base, step):
        if self.spec['artifact']['kind'] == 'c1_export':
            return self.leg.check_export(path, pin, base, step)
        if T.sha(path) != pin:
            raise ValueError('Archive full-file SHA256 differs')
        return dict(status='VERIFIED', kind='archive', sha256=pin, bytes=Path(path).stat().st_size)

    def launch(self, args):
        cfg = T.load(Path(args.dest)/'request.json')
        validate_protocol(cfg, self.family)
        self.model_specs(cfg['models'], 'cp1m200')
        if cfg['build_only'] or not cfg['legs1']['export_bytes_verified']:
            raise ValueError('Dry/unverified bind cannot launch')
        self.check_export(self.spec['artifact']['path'], self.spec['artifact']['sha256'],
                          cfg['models']['base']['path'], self.spec['step'])
        return self.vendor.launch(args)
