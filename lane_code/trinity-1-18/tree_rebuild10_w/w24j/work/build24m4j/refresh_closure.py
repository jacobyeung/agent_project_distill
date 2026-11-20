from common import *
import base64
s=(kit('qd')/'b/rb.py').read_text();modules=J.load(D/'IMPORT_CLOSURE.json')['probe']
a=s.index('\ndef load_modules():');b=s.index('\ndef command(',a)
code='\ndef load_modules():\n    names = probe_modules()\n    current = names[0]\n    try:\n'
for i,name in enumerate(modules):
 code+=f'        current = names[{i}]\n        import {name} as q{i}\n'
 if name=='transformers':code+=f'        q{i}.AutoProcessor\n        q{i}.AddedToken\n'
 code+=f'        yield current, q{i}\n'
code+='''    except Exception as error:
        missing = (error.name if isinstance(error, ImportError) else None) or current
        raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+missing) from error


def probe_modules():
    import base64
    return json.loads(base64.b64decode("'''+base64.b64encode(json.dumps(modules).encode()).decode()+'''"))

'''
s=s[:a]+code+s[b:]
for n in NAMES:replace(kit(n)/'b/rb.py',s)
J.write(D/'SEALS.json',{n:reseal(kit(n)) for n in NAMES})
print('PROBE',len(modules),'P direct third-party',list(J.load(D/'IMPORT_CLOSURE.json')['external']))
for name in ('probe','trace'):
 (D/name).rename(L/'attic/build24m4j'/(name+'_before_batches'))
for name in ('probe_tests.log','trace_imports.log'):
 (D/name).rename(L/'attic/build24m4j'/('before_batches_'+name))
