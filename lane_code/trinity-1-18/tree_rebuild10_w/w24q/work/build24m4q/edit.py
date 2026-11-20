import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=L/'out/rcj/pc.py';s=p.read_text()
a=s.index('        matches = [line for line in lines');b=s.index('    except OSError:',a)
s=s[:a]+'''        # A traceback ends at its first unindented exception line. Buffered
        # stdout can follow it, and chained exceptions start another traceback.
        starts = [i for i, line in enumerate(lines) if line == 'Traceback (most recent call last):']
        if starts:
            for line in lines[starts[-1]+1:]:
                if re.fullmatch(r'[A-Za-z_][\\w.]*(?::.*)?', line):
                    reason += ':'+line[:4096]
                    break
'''+s[b:]
a=s.index('\ndef run_bound(')
s=s[:a]+'''
def metadata_mounts(value):
    from student_pilot.p3_provenance import pinned
    root = Path(value['root'])
    if not root.is_absolute() or '..' in root.parts:
        raise ValueError('E98')
    result = {}
    for name, h in value['files'].items():
        # These are the small, pinned assets consumed by the constructor.
        # Weight indices and generation settings are not processor inputs.
        if not name.endswith(('.json', '.txt', '.jinja', '.model')):
            continue
        if name.endswith('.index.json') or Path(name).name == 'generation_config.json':
            continue
        part = Path(name)
        if part.is_absolute() or '..' in part.parts:
            raise ValueError('E98')
        target = str(root/part)
        result[target] = dict(source=str(pinned(dict(path=target, sha256=h))), sha256=h)
    if not result:
        raise ValueError('E98')
    return result

'''+s[a:]
s=s.replace("            write(control,dict(config=config,model=model,model_value=load(pinned(model)),environment=env,tree_sha256=sealed['tree_sha256'],samples=str(sample_path),output=str(result)))\n            cmd=rb.command(q,control,source,mounts if side=='p' else {},env)","            value=load(pinned(model))\n            assets=metadata_mounts(value)\n            write(control,dict(config=config,model=model,model_value=value,environment=env,tree_sha256=sealed['tree_sha256'],samples=str(sample_path),output=str(result),assets=assets))\n            cmd=rb.command(q,control,source,{},env)")
s=s.replace("            cmd[-3:]=[str(script),str(control),str(source)]", "            # Install after broad namespace mounts so neither side hides these files.\n            at=cmd.index('--chdir')\n            for target,item in sorted(assets.items()):\n                cmd[at:at]=['--ro-bind',item['source'],target];at+=3\n            cmd[-3:]=[str(script),str(control),str(source)]")
replace(p,s)
