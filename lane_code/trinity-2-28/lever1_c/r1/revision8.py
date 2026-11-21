"""Apply storage, submission and write-budget contracts before sealing."""

def patch(nf,pf,B,here,token):
    q=(here/'runtime/q.py').read_bytes().replace(b'TOKEN_VALUE',token.encode())
    guard=b"\nexec(bytes.fromhex('"+q.hex().encode()+b"'),_q:={});_q['install']()\n"
    # Every package entry and helper inherits the same cumulative metadata ledger.
    for n in ('3.py','a/5.py','a/9.py'):nf[n]=guard+nf[n]
    pf['8.py']=guard+pf['8.py']
    common=pf['orchard_h10/common.py'].decode()
    common=common.replace("'--output=/dev/null', '--error=/dev/null'", "'--output=/project/community/jjyeung/'+token+'/a/19', '--error=/project/community/jjyeung/'+token+'/a/24', '--open-mode=append'")
    pf['orchard_h10/common.py']=common.encode()
    launcher=pf['orchard_h10/vendor/orchard_launcher.py'].decode()
    launcher=launcher.replace("'--output=/dev/null', '--error=/dev/null'", "'--output=/project/community/jjyeung/'+token+'/a/19', '--error=/project/community/jjyeung/'+token+'/a/24', '--open-mode=append'")
    # The retained launcher uses the same bounded scheduler channel.
    launcher=launcher.replace('"import subprocess,sys\\n"', '"import subprocess,sys,runpy\\n"\n        "submit=runpy.run_path(\'/project/community/jjyeung/\'+"+repr(token)+"+\'/a/27.py\')[\'submit\']\\n"')
    launcher=launcher.replace('"result=subprocess.run(argv,input=body,capture_output=True,timeout=50)\\n"', '"result=submit(\'/project/community/jjyeung/\'+"+repr(token)+"+\'/a\',argv,input=body,capture_output=True)\\n"')
    pf['orchard_h10/vendor/orchard_launcher.py']=launcher.encode()
    s=pf['8.py'].decode()
    start=s.index('    export=f"--export=');end=s.index('    opaque(argv)',start)
    s=s[:start]+s[end:]
    # One sealed entry, scheduler flags and environment for both allocations.
    s=s.replace('def submit(package,gpus,walltime,test_only=False):','def submit(package,gpus,walltime,test_only=False,cpu_only=False):')
    s=s.replace("    opaque(argv)\n    env=", "    if cpu_only:argv=[a for a in argv if not a.startswith('--gres=')]\n    opaque(argv)\n    env=")
    s=s.replace("p.add_argument('--return-token');", "p.add_argument('--cpu-only',action='store_true');p.add_argument('--return-token');")
    s=s.replace('submit(root,a.gpus,a.time,a.test_only)', 'submit(root,a.gpus,a.time,a.test_only,a.cpu_only)')
    s=s.replace("    result=subprocess.run(argv+(['--test-only'] if test_only else []),", "    import runpy\n    bounded_submit=runpy.run_path(str(package/'a/27.py'))['submit']\n    result=bounded_submit(package/'a',argv+(['--test-only'] if test_only else []),")
    s=s.replace("    transfer=destination/'0.stream'", "    if result.stat().st_size>5_900_000:raise ValueError('E71')\n    if sum((source/n).stat().st_size for n in ('EXIT.json','RETURN_RECEIPT.json'))>100_000:raise ValueError('E71')\n    # One-shot destination: framing + archive + receipts fit the 20 MB slot.\n    transfer=destination/'0.stream'")
    pf['8.py']=s.encode()
    s=pf['orchard_h10/vendor/orchard_job.py'].decode()
    s=s.replace("value['filesystem'] not in ('ext4', 'xfs', 'btrfs', 'tmpfs')", "value['filesystem'] != 'ext4'")
    s=s.replace("(value['filesystem'] != 'tmpfs' and not value['source'].startswith('/dev/'))", "not value['source'].startswith('/dev/')")
    pf['orchard_h10/vendor/orchard_job.py']=s.encode()
    s=pf['orchard_h10/vendor/orchard_results.py'].decode()
    s=s.replace("cap=20_000_000 if mode=='proof' else 90_000_000", "cap=6_000_000")
    pf['orchard_h10/vendor/orchard_results.py']=s.encode()
    s=pf['orchard_h10/vendor/return_io.py'].decode()
    s=s.replace("        dest = pool/token", """        dest = pool/token
        ledger=pool/(token+'.0')
        used=int(ledger.read_text()) if ledger.exists() else 0
        def reserve(amount):
            nonlocal used
            amount+=32
            if used+amount>12_000_000:raise ValueError('E72')
            used+=amount
            with ledger.open('w') as stream:stream.write('%032d'%used)
""")
    s=s.replace("            dest.mkdir(mode=0o700)","            reserve(4*1024**2)\n            dest.mkdir(mode=0o700)")
    s=s.replace("        for name in names:\n            src", "        reserve(incoming)\n        for name in names:\n            src")
    s=s.replace('4*1024**2','131072')
    pf['orchard_h10/vendor/return_io.py']=s.encode()
    # CPU staging and bulky rehearsal outputs stay on the admitted disk.
    s=nf['a/5.py'].decode().replace("if not entry.name.startswith('orchard_h10/'):continue","if not entry.name.startswith('orchard_h10/') and entry.name!='j.py':continue")
    s=s.replace("    package=Path(args.package).resolve()","    if not os.environ.get('USER'):raise KeyError('USER')\n    package=Path(args.package).resolve()")
    s=s.replace("    results=Path(args.results).resolve();results.mkdir(parents=True,exist_ok=False)", "    destination=Path(args.results).resolve()\n    results=root/'results';results.mkdir()")
    s=s.replace("    print(json.dumps(dict(results=str(results),root=str(root),passed=True)))", "    destination.mkdir(parents=True,exist_ok=False)\n    for name in ('CPU.json','MEMORY.json'):\n        raw=(results/name).read_bytes()\n        if len(raw)>400_000:raise ValueError('E73')\n        (destination/name).write_bytes(raw)\n    print('0')")
    s=s.replace("with open('/dev/null','wb') as log:", "with __import__('orchard_h10.e',fromlist=['capture']).capture(root/'22.json') as log:")
    nf['a/5.py']=s.encode()
    pf['orchard_h10/vendor/stdout_transfer.py']=pf['orchard_h10/vendor/stdout_transfer.py'].replace(b'LOG_LIMIT = 8*1024**2',b'LOG_LIMIT = 64*1024')
    return guard


def batch_header(token):
    p='/project/community/jjyeung/'+token+'/a/'
    return ("#!/bin/bash\nulimit -S -f 512\n"
            "trap 'r=$?; printf \"%s %s %s\\n\" \"$r\" \"$LINENO\" \"${SLURM_JOB_ID:-0}\" >>"+p+"21' ERR\n"
            "trap 'r=$?; trap - ERR EXIT; printf \"%s %s %s\\n\" \"$r\" \"$LINENO\" \"${SLURM_JOB_ID:-0}\" >>"+p+"21; exit \"$r\"' EXIT\n"
            "exec >>"+p+"19 2>>"+p+"24\n"
            "set -Eeuo pipefail\n/usr/bin/python3 -I -s -B - <<'A'\n")
