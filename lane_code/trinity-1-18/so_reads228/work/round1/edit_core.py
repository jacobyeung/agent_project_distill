from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/so_reads228/work/round1/kit')
for p in K.glob('*.py'):
    s=p.read_text().replace('A4_PINS.json','A10b_PINS.json').replace("HERE/'A4", "HERE/'A10b").replace('172744','173060').replace('m200','m400').replace('A4','A10b')
    p.write_text(s)
p=K/'common228.py';s=p.read_text()
s=s.replace("STAGE = Path('/scratch/jjyeung/a4228')","STAGE = Path('/scratch/jjyeung/orch_n30/reads228')")
s=s.replace("VNICE = Path('/data3/shared/scripts/vnice/vnice.sh')","VNICE = Path('/data3/shared/scripts/vnice/vnice.sh')\nTERMINATOR = VNICE.with_name('terminator.sh')")
s=s.replace("text=True).strip()","universal_newlines=True).strip()")
s=s.replace("def local(path):", "def beneath(path, root):\n    try:Path(path).relative_to(root);return True\n    except ValueError:return False\n\ndef local(path):")
s=s.replace("path.resolve().is_relative_to('/scratch/jjyeung')", "beneath(path.resolve(),'/scratch/jjyeung')")
s=s.replace("env.update(CUDA_VISIBLE_DEVICES=card", "env.update(USER='jjyeung',LOGNAME='jjyeung',CUDA_VISIBLE_DEVICES=card")
s=s.replace("    return env\n", "    for key,rel in (('HOME','home'),('CUDA_CACHE_PATH','cache/nv'),('MPLCONFIGDIR','cache/mpl')):\n        p=out/rel;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)\n    # Both CUDA and matplotlib writes remain inside the reader's audited cache root.\n    env['XDG_CACHE_HOME']=str(out/'cache')\n    return env\n")
s=s.replace("def deployment(package):", "def policy_check(pins=None):\n    pins=pins or read(HERE/'A10b_PINS.json')\n    for name,path in (('vnice',VNICE),('terminator',TERMINATOR)):\n        checked(path,pins['policy'][name])\n\ndef deployment(package):")
s=s.replace("    for name,spec in pins['package'].items():", "    policy_check(pins)\n    for name,spec in pins['package'].items():")
p.write_text(s)
p=K/'compare228.py';s=p.read_text()
s=s.replace("for record in value['records']:","for index,record in enumerate(value['records']):")
s=s.replace("result.append({k:v for k,v in record.items() if k not in ('response','forced_tokens','seconds','timings')})", "result.append((index,record['family'],record['call'],record['served'],record['at_token']))")
s=s.replace('bindings[kind]=binding','bindings[kind]=env')
start=s.index("        info=root/'metadata/LOCAL_RUN.json'")
end=s.index("    if canonical(data[0][:50])",start)
s=s[:start]+'''        for value in env.values():
            settings=value.get('settings')
            if not isinstance(settings,dict):reasons.append(label+': missing settings; OFF required')
            elif any(k.startswith('read_') and v not in ('off',False,0,None,[]) for k,v in settings.items()):
                reasons.append(label+': Extension-enabled settings; OFF required')
        if label=='trinity':
            info=root/'metadata/LOCAL_RUN.json'
            if not info.is_file():reasons.append('trinity: missing LOCAL_RUN.json')
            else:
                local_run=read(info)
                for key,wanted in (('backend','trinity-local'),('host','trinity-2-28'),('mode','OFF')):
                    if local_run.get(key)!=wanted:reasons.append('trinity: LOCAL_RUN '+key+' must be '+wanted)
            cards=root/'metadata/CARDS.json'
            if not cards.is_file() or 'RTX 6000 Ada' not in str(read(cards).get('snapshot',{}).get('name','')):
                reasons.append('trinity: CARDS snapshot must identify RTX 6000 Ada')
            # Check every journal environment, including empty/unselected journal directories.
            for path in sorted((root/'metadata/reads').glob('*/metadata/journals/*/*/environment.json')):
                if not str(read(path).get('host','')).startswith('trinity-2-28'):
                    reasons.append('trinity: journal host differs: '+str(path.relative_to(root)))
            receipt=root/'metadata/RETURN_ID.json'
            job=read(receipt).get('job') if receipt.is_file() else None
            if job is None or str(job)==str(fixed.get('reference_job','173060')):
                reasons.append('trinity: missing RETURN_ID or Orchard reference job reused')
    for kind in set(envs[0])&set(envs[1]):
        for key in BINDINGS:
            if envs[0][kind]['binding'][key]!=envs[1][kind]['binding'][key]:reasons.append('binding differs: '+str(kind)+'.'+key)
''' + s[end:]
s=s.replace("    if isinstance(a,list):","    if isinstance(a,(list,tuple)):")
s=s.replace("    result=compare(a.orchard,a.trinity_return);write(a.out,result)","    destination=local(a.out)\n    result=compare(a.orchard,a.trinity_return);write(destination,result)")
p.write_text(s)
p=K/'read228.py';s=p.read_text().replace('preflight, full OFF read','preflight, OFF prefix read')
s=s.replace('import json','import argparse\nimport json')
s=s.replace("def main():\n    if len(sys.argv)!=3:raise Refusal('Usage: read228.sh <package> <card>')\n    target_host();root=package_root(sys.argv[1]);card=sys.argv[2]", "def main(argv=None):\n    parser=argparse.ArgumentParser(description=__doc__)\n    parser.add_argument('package');parser.add_argument('card')\n    parser.add_argument('--items',type=int,default=50)\n    a=parser.parse_args(argv)\n    if not 1<=a.items<=636:raise Refusal('--items must be in 1..636')\n    target_host();root=package_root(a.package);card=a.card")
s=s.replace("str(root),card,str(out)]","str(root),card,str(out),'--items',str(a.items)]")
p.write_text(s)
for name in ('run228.sh','compare228.sh','read228.sh'):
    p=K/name;s=p.read_text().replace('/scratch/jjyeung/envs/p1cpu/bin/python','/scratch/jjyeung/b01ec87a6f29b/d/v/py')
    if name=='read228.sh':
        start=s.index('if [[ $#');end=s.index('kit_dir=',start);s=s[:start]+s[end:]
        s=s.replace('"$1" "$2"','"$@"')
    p.write_text(s)
p=K/'worker228.py';s=p.read_text().replace("    else:\n        from e2e_reader import parity\n",'')
p.write_text(s)
p=K/'bootstrap228.py';s=p.read_text().replace("step=200","step=400").replace("source/'ret/metadata/INPUTS.json'","source/'package/a/1.json'").replace("source/'ret/metadata/EXPORT_PIN.json'","source/'package/a/export.json'")
p.write_text(s)
p=K/'return228.py';s=p.read_text().replace("    number=secrets.randbelow(2**32-1)+1", "    # Reserve the reference job ID so a local receipt cannot accidentally reuse it.\n    number=secrets.randbelow(2**32-2)+1\n    if number>=173060:number+=1")
p.write_text(s)
print('Updated A10b contracts, comparison, environments, wrappers and control defaults.')
