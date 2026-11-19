"""Private-host helpers for public settings and authenticated return restoration."""
import argparse
import json
from pathlib import Path
import sys


def relocate(value, aliases):
    if isinstance(value,dict):return {k:relocate(v,aliases) for k,v in value.items()}
    if isinstance(value,list):return [relocate(v,aliases) for v in value]
    if isinstance(value,str):
        for old,new in sorted(aliases.items(),key=lambda pair:-len(pair[0])):
            if value==old or value.startswith(old+'/'):return new+value[len(old):]
    return value


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('seal','restore','stage-kit'))
    parser.add_argument('--source-root',required=True)
    parser.add_argument('--input',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--config');parser.add_argument('--aliases');parser.add_argument('--private-source',action='append',default=[])
    args=parser.parse_args()
    source=Path(args.source_root).resolve()
    sys.path[:0]=[str(source/'u0'),str(source),str(source/'tree'),str(source/'b')]
    from a9 import seal_settings,restore
    if args.action=='stage-kit':
        import hashlib
        from a9 import pack
        incoming=Path(args.input);out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
        for old,new in (('run.py','u0.py'),('compare.py','u1.py')):
            (out/new).write_bytes((incoming/old).read_bytes())
        (out/'a9.py').write_bytes((source/'u0/a9.py').read_bytes())
        sample=json.loads((incoming/'sample50.json').read_bytes())
        (out/'u0.json').write_text(json.dumps({'u0':pack(sample)},sort_keys=True)+'\n')
        identity=json.loads((incoming/'SAMPLE_IDENTITY.json').read_bytes())
        identity['logical_sample_sha256']=identity['sample_sha256']
        identity['sample_sha256']=hashlib.sha256((out/'u0.json').read_bytes()).hexdigest()
        (out/'u1.json').write_text(json.dumps({'u0':pack(identity)},sort_keys=True)+'\n')
        pins=json.loads((incoming/'EXTENSION_PINS.json').read_bytes())
        (out/'u3.json').write_text(json.dumps({'u0':pack(pins)},sort_keys=True)+'\n')
        base=json.loads((incoming/'BASE_PIN.json').read_bytes())
        (out/'u4.json').write_text(json.dumps({'u0':pack(base)},sort_keys=True)+'\n')
        config=json.loads(Path(args.config).read_bytes()) if args.config else json.loads((incoming/'config.example.json').read_bytes())
        seal_settings(config,out/'u2.json')
    elif args.action=='seal':
        value=json.loads(Path(args.input).read_bytes())
        aliases=json.loads(Path(args.aliases).read_bytes()) if args.aliases else {}
        seal_settings(relocate(value,aliases),args.out)
    else:
        if not args.private_source:parser.error('Private manifests/settings are required to restore IDs')
        from a8 import activate
        activate(enabled=True)
        from a9 import read_wire
        restore(args.input,args.out,[read_wire(json.loads(Path(path).read_bytes())) for path in args.private_source])
    return 0


if __name__=='__main__':raise SystemExit(main())
