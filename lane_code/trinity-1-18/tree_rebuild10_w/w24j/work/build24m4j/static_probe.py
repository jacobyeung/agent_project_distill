from common import *
s=(kit('qd')/'b/rb.py').read_text()
a=s.index('    result = {}\n    for name in modules:');b=s.index('        location = ',a)
s=s[:a]+'''    for name in modules:
        try:
            spec = importlib.util.find_spec(name)
        except ImportError as error:
            raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+(error.name or name)) from error
        if spec is None:
            raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+name)
    result = {}
    for name, module in load_modules():
'''+s[b:]
modules=J.load(D/'IMPORT_CLOSURE.json')['probe']
code='\n\ndef load_modules():\n    names = probe_modules()\n    current = names[0]\n    try:\n'
for i,name in enumerate(modules):
 code+=f'        current = names[{i}]\n        import {name} as q{i}\n'
 if name=='transformers':code+=f'        q{i}.AutoProcessor\n        q{i}.AddedToken\n'
 code+=f'        yield current, q{i}\n'
code+='''    except Exception as error:
        missing = (error.name if isinstance(error, ImportError) else None) or current
        raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+missing) from error
'''
s=s.replace('\ndef probe_modules():',code+'\n\ndef probe_modules():')
for n in NAMES:replace(kit(n)/'b/rb.py',s)
J.write(D/'SEALS.json',{n:reseal(kit(n)) for n in NAMES})
