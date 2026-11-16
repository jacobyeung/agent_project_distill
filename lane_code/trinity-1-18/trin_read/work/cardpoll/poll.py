"""Card poller (trin_read2): every 600 s read trinity-1-3 locally and trinity-1-18 with one ssh; a card empty (<100 MiB, no app)
in a poll is reread 300 s later; if still empty, write CARD_FOUND.json and exit. Never launches anything."""
import json, subprocess, time
from pathlib import Path
D = Path('/scratch/jjyeung/orch_n30/trin_read/work/cardpoll'); S = D/'read.sh'
def read(host):
    cmd = ['bash', str(S)] if host == 'trinity-1-3' else ['timeout', '120', 'ssh', '-o', 'ConnectTimeout=20', host, 'bash -s']
    with S.open() as f:
        out = subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).stdout
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()); (D/('%s_%s.txt' % (host, stamp))).write_text(out)
    lines = out.splitlines(); i = lines.index('APPS') if 'APPS' in lines else len(lines)
    busy = {l.split(',')[0].strip() for l in lines[i+1:] if l.startswith('GPU-')}
    empty = []
    for l in lines[3:i]:
        p = [x.strip() for x in l.split(',')]
        if len(p) == 3 and p[1] not in busy and int(p[2].split()[0]) < 100: empty.append((p[0], p[1]))
    return empty, stamp
while True:
    for host in ('trinity-1-3', 'trinity-1-18'):
        empty, t1 = read(host)
        if empty:
            time.sleep(300); again, t2 = read(host)
            both = [c for c in again if c in empty]
            if both:
                (D/'CARD_FOUND.json').write_text(json.dumps(dict(host=host, cards=both, readings=[t1, t2]), indent=1)); raise SystemExit(0)
        time.sleep(30)
    time.sleep(570)
