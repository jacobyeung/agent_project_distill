"""Mandatory byte-backed frame-host checks, with one sealed receipt per step."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import urllib.request
from urllib.parse import urlsplit, unquote
from student_pilot.p3_provenance import digest, file_pin, load, pinned
from student_pilot.r2_portable import bound

ITEMS = (1, 2, 4, 5, 9, 11)


class Checklist:
    def __init__(self, root, packet, cfg):
        self.root, self.packet, self.cfg = Path(root), packet, cfg
        self.receipts = {}
        self.output = self.root/'o/ee000008'
        self.output.mkdir(parents=True, exist_ok=True)

    def step(self, item, action):
        from .build import capsule_json
        if item not in ITEMS or item in self.receipts:
            raise ValueError('Unknown or repeated host check')
        try:
            evidence = action()
            value = dict(item=item, status='PASS', evidence=evidence)
        except Exception as error:
            value = dict(item=item, status='REFUSE', reason_sha256=digest(str(error)))
            (self.output/(str(item)+'.json')).write_bytes(capsule_json(value))
            raise ValueError('Host check '+str(item)+' refused') from error
        path = self.output/(str(item)+'.json')
        path.write_bytes(capsule_json(value))
        self.receipts[item] = file_pin(path)
        return evidence

    def runtime(self):
        from .staging import P
        value = load(self.root/'o/01.json')
        zero = load(self.root/'k/0.json')
        plan = load(bound(zero['staging'], self.root))
        if (value.get('stdlib_version') != [3, 6] or value.get('venv_sha256') != plan['venv']['sha256']
                or value.get('bwrap_sha256') != plan['bwrap']['sha256']
                or sys.executable != P+'/venvs/rwtrain_torch211_cu129/bin/python'):
            raise ValueError('Pinned sandbox runtime did not execute')
        scripts = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.root/'b').glob('*.py')}
        if not scripts or value.get('files') != scripts:
            raise ValueError('Bootstrap script proof differs')
        import numpy
        import torch
        if torch.empty(1, device='cpu').is_cuda:
            raise ValueError('Runtime CPU check failed')
        return dict(bootstrap=file_pin(self.root/'o/01.json'), executable=file_pin(sys.executable),
                    numpy=numpy.__version__, torch=torch.__version__)

    def stage_inputs(self):
        from .staging import stage_inputs, validate_plan
        zero = load(self.root/'k/0.json')
        plan = load(bound(zero['staging'], self.root))
        validate_plan(self.cfg, plan['entries'])
        from .input_check import sources
        source_proof = sources(plan)
        if 'b7_inputs' in self.cfg:
            from student_pilot.b7_inputs import validate
            validate(self.cfg['b7_inputs'], 'a2' if self.cfg['geometry_connector']=='gf1' else 'a0', verify=True)
        stage_inputs(plan['entries'], self.root)
        return self.staged()

    def staged(self):
        from .staging import relative_paths, checked
        zero = load(self.root/'k/0.json')
        plan = load(bound(zero['staging'], self.root))
        records = {}
        for name in sorted(set(plan['entries']) | relative_paths(self.cfg)):
            entry = plan['entries'][name]
            target = self.root/name
            if entry.get('directory'):
                if not target.is_dir() or not any(target.iterdir()):
                    raise ValueError('Staged directory is absent or empty')
                records[name] = dict(archive_sha256=entry['sha256'], directory=True)
            else:
                records[name] = file_pin(checked(target, entry['sha256']))
        if not records:
            raise ValueError('No staged pins were checked')
        return records

    def roundtrip(self):
        spec = self.packet['checks']['roundtrip']
        tool = bound(self.cfg['r2_persistence']['uploader'], self.root)
        sessions = bound(spec['sessions'], self.root)
        key = spec['prefix']+'/01'
        if not spec['prefix'].startswith('j/') or '..' in spec['prefix'].split('/'):
            raise ValueError('Round trip requires a job-local object prefix')
        from .build import bad_string
        if bad_string(spec['prefix'], load(self.root/'b/wh.json')):
            raise ValueError('Round trip object prefix is not opaque')
        url = urlsplit(spec['download_url'])
        if (url.scheme != 'https' or not (url.hostname == 'storage.googleapis.com'
                or (url.hostname or '').endswith('.storage.googleapis.com'))
                or not unquote(url.path).endswith('/'+key)):
            raise ValueError('Download does not bind the uploaded object')
        state = dict(schema='cpu-state-probe-v1', synthetic=True,
                     model=[0.125], optimizer=dict(step=1,moment=[0.25]), rng=[17], position=1)
        raw = json.dumps(state,sort_keys=True).encode()
        path = self.output/'04.bin'
        path.write_bytes(raw)
        module_spec = importlib.util.spec_from_file_location('pinned_writer', tool)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        if module.main(['put', str(sessions), key, str(path)]):
            raise ValueError('Object upload failed')
        records = [json.loads(s) for s in Path(str(sessions)+'.receipts.jsonl').read_text().splitlines()]
        selected = [v for v in records if v['name'] == key]
        if len(selected) != 1 or not selected[0].get('generation') or selected[0]['sha256'] != hashlib.sha256(raw).hexdigest():
            raise ValueError('Upload generation or digest differs')
        request = urllib.request.Request(spec['download_url'])
        with urllib.request.urlopen(request, timeout=60) as reply:
            generation = reply.headers.get('x-goog-generation')
            if generation != str(selected[0]['generation']):
                raise ValueError('Downloaded generation differs')
            restored = reply.read(len(raw)+1)
        if restored != raw or json.loads(restored) != state:
            raise ValueError('Restored state differs')
        return dict(upload=selected[0], download_generation=generation,
                    restored_sha256=hashlib.sha256(restored).hexdigest(),
                    stand_in='small synthetic model, optimizer, RNG and position state')

    def banks(self):
        from student_pilot.r2_policy import seal_catalog
        files = self.packet['checks']['bank_files']
        if not files:
            raise ValueError('Real bank files are missing')
        actual = seal_catalog({name:file_pin(bound(pin,self.root)) for name,pin in files.items()})
        expected = load(bound(self.cfg['r2_evaluation']['catalog'],self.root))
        if actual != expected or not actual['items']:
            raise ValueError('Bank bytes differ from the bound membership')
        return dict(catalog_sha256=digest(actual), files=files, items=len(actual['items']))

    def vocabulary(self):
        from transformers import AutoProcessor
        from student_pilot.r2_openers import vocabulary, preparation
        artifact = pinned(self.cfg['init_artifact']['artifact'])
        processor = AutoProcessor.from_pretrained(str(artifact.parent),local_files_only=True,trust_remote_code=False)
        recorded = load(artifact).get('routing_vocabulary')
        if not recorded or not recorded.get('tokens'):
            raise ValueError('Staged export lacks its recorded opener vocabulary')
        processor._routing_tokens = recorded['tokens']
        if any(processor.tokenizer.convert_tokens_to_ids(token) != index
               for token,index in recorded['tokens']['ids'].items()):
            raise ValueError('Export tokenizer opener IDs differ')
        preparation(self.cfg)
        expected = load(bound(self.cfg['routing_vocabulary'],self.root))
        actual = vocabulary(processor)
        if any(expected.get(key) != value for key,value in actual.items()):
            raise ValueError('Staged export vocabulary differs from the witness')
        return dict(artifact=file_pin(artifact), **actual)

    def outputs(self):
        from .build import scan
        return scan(self.root)

    def finish(self):
        if set(self.receipts) != set(ITEMS):
            raise ValueError('Required host checks are incomplete')
        for item, pin in self.receipts.items():
            value = load(pinned(pin))
            if value.get('item') != item or value.get('status') != 'PASS':
                raise ValueError('Host check receipt changed')
        return {str(k):v for k,v in self.receipts.items()}
