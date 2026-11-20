from common import *
p=L/'out/rcj/x.py';s=p.read_text()
a=s.index('        # The same pinned small archive')
s=s[:a]+'''        # Resolve selected metadata through the kit's authenticated handover
        # reader. No checkpoint part or weight file is opened or copied here.
        handover = self.z.pool_file(self.spec['pool'], Path(self.spec['pool'])/self.spec['milestone']/'s.tar')
        with tarfile.open(handover) as archive:
            raw = archive.extractfile('MANIFEST.json').read()
        if hashlib.sha256(raw).hexdigest() != self.spec['m4']['v']:
            raise ValueError('R1_STAGED_PIN_MANIFEST_DIFFERS')
        manifest = json.loads(raw)
        if h in {item['sha256'] for item in manifest['files']}:
            values, metadata = self.z.small_archive(handover, roots=[dict(path='p.json', sha256=h)])
            if h in values:
                return self.member([str(handover)], h, field, [values[h]['member']])
'''+s[a:]
replace(p,s)
a=J.load(D/'RCJ_PLAN_AUDIT.json');m=W/'ext/m400real/MANIFEST.json';spec=J.load(kit('qd')/'k/p.json');J.checked(m,spec['m4']['v']);m=J.load(m)
found={x['sha256']:dict(path=x['path'],bytes=x['bytes']) for x in m['files']}
for h,origins in a['required_hashes'].items():
 if origins==['small_lookup_runtime_required']:
  assert h in found,h
  a['required_hashes'][h]=['handover_small_archive']
a['authenticated_handover_manifest_sha256']=spec['m4']['v'];a['unmapped_hashes']=[]
replace(D/'RCJ_PLAN_AUDIT.json',json.dumps(a,indent=2)+'\n')
model=J.load(D/'P_AUTH.json')['model']
assert not ({h for n,h in model['files'].items() if n.endswith('.safetensors')} & set(a['required_hashes']))
print('All 65 required hashes map to sealed staged inventories or authenticated handover metadata; no weights')
