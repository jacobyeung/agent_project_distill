from pathlib import Path
for key in ('vsi','revsi'):
 p=Path('kit')/key/'launcher/orchard_launcher.py';s=p.read_text().replace('def fetch(destination):','def fetch(destination, transfer=None):').replace("if ap['bytes']>=20_000_000:","if ap['bytes']>=20_000_000 and transfer is None:")
 s=s.replace("                subprocess.run(SSH+[shlex.join(command)],stdout=out,stderr=err,check=True,timeout=180)","                if transfer is None:\n                    subprocess.run(SSH+[shlex.join(command)],stdout=out,stderr=err,check=True,timeout=180)\n                else:\n                    transfer(SSH+[shlex.join(command)],out,err,ap['bytes'])")
 p.write_text(s)
p=Path('kit/rebind.py');s=p.read_text().replace('import shlex\n','import shlex\nimport os\nimport signal\nimport subprocess\nimport time\n')
index=s.index('\ndef fetch(a):')
s=s[:index]+'''
def governed_transfer(argv, output, errors, size, token):
    """Register a stopped source and a live rate limiter before payload IO."""
    helpers = Path('/scratch/jjyeung/io_governor')
    for name in ('register.py','ratelimit.py'):
        if not (helpers/name).is_file():
            raise ValueError('The IO governor helpers are unavailable')
    lane = 'r'+token
    record = Path('/data3/jjyeung/orch_n13_20261026/io_governor/streams')/(lane+'.json')
    if record.exists():
        raise ValueError('An IO stream record already exists; reconcile it before fetching')
    stop_code = 'import os,signal,sys;os.kill(os.getpid(),signal.SIGSTOP);os.execvp(sys.argv[1],sys.argv[1:])'
    source = subprocess.Popen([sys.executable,'-B','-c',stop_code,*argv],stdout=subprocess.PIPE,stderr=errors)
    pacer = None
    try:
        pacer = subprocess.Popen([sys.executable,'-B',str(helpers/'ratelimit.py'),'-q','-L','1000','-B','65536'],
                                 stdin=source.stdout,stdout=output,stderr=errors)
        source.stdout.close()
        deadline = time.monotonic()+30
        while True:
            state = Path(f'/proc/{source.pid}/stat').read_text().rsplit(')',1)[1].split()[0]
            ready = Path(f'/proc/{pacer.pid}/comm').read_text().strip()=='ratelimit'
            if state=='T' and ready: break
            if source.poll() is not None or pacer.poll() is not None or time.monotonic()>deadline:
                raise RuntimeError('The stopped IO pipeline did not become ready')
            time.sleep(0.05)
        subprocess.run([sys.executable,'-B',str(helpers/'register.py'),'--lane',lane,'--pid',str(source.pid),
            '--member-pid',str(pacer.pid),'--rl-pid',str(pacer.pid),'--expected-bytes',str(size),
            '--tier','3','--kind','pull','--nominal-mbps','8','--tunnel-mbps','8',
            '--io-weight','1','--tunnel-weight','1','--allow-resume'],check=True,stdout=errors,stderr=errors)
        source_code = source.wait()
        pacer_code = pacer.wait()
        if source_code or pacer_code:
            raise RuntimeError('The governed transfer failed; do not retry it automatically')
        if record.exists():
            record.rename(record.with_name(lane+'.done.'+str(time.time_ns())))
    finally:
        for process in (source,pacer):
            if process is not None and process.poll() is None:
                process.terminate()
                if process is source: os.kill(process.pid,signal.SIGCONT)
                process.wait(timeout=20)

''' +s[index:]
s=s.replace("        L.fetch(a.destination)","        L.fetch(a.destination, transfer=lambda argv,out,err,size: governed_transfer(argv,out,err,size,c['token']))")
p.write_text(s)
