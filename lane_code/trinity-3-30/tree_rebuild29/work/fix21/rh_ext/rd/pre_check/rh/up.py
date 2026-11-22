"""The rehearsal's upload planner pass: the kit's own b/pc.py Copier, one pass as its --loop runs it
(pass_once(final=False, small=False): stop, exports, checkpoints), over the rehearsal's scratch sink.
usage (inside the rehearsal sandbox, started with --unshare-net): up.py <sink> <copier root> <job>
Differences from the job's loop, all on purpose: train is the sink (not p/q/r); the root holding
live_spool is scratch; the session map is a local one written here (every part the kit's names allow, each
URL a label https://a15-local-sink.invalid/<local record path>), so the job's session file is never read;
the writer is rh/sw.py (the kit's gc.py with its transport replaced by a local recorder), never gc.py over
HTTPS. A Python audit hook refuses and records every connect or name lookup; the process has no network
namespace route anyway. Writes log/plan.json (what was planned, sent and where) and prints a short form."""
import json, os, sys, time
from pathlib import Path

NOUPLOAD = 'https://a15-local-sink.invalid'
NET = {'socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr', 'socket.sendto',
       'socket.sendmsg', 'http.client.connect', 'urllib.Request', 'ftplib.connect', 'smtplib.connect', 'nntplib.connect'}
SPAWN = {'subprocess.Popen', 'os.posix_spawn', 'os.exec', 'os.system', 'os.spawn', 'os.fork'}
events = []


def hook(name, args):
    if name in NET:
        events.append(dict(event=name, args=repr(args)[:300], refused=True))
        raise RuntimeError('A15: network refused in the rehearsal planner: ' + name)
    if name.startswith('socket.') or name in SPAWN:   # argv only: a process environment is never logged
        shown = args[1] if name in ('subprocess.Popen', 'os.posix_spawn', 'os.exec') and len(args) > 1 else args
        events.append(dict(event=name, args=repr(shown)[:800]))


sys.addaudithook(hook)
t0 = time.time()
# the network namespace this pass runs in: only the loopback device may exist (bwrap --unshare-net)
ifaces = sorted(x.partition(':')[0].strip() for x in Path('/proc/self/net/dev').read_text().splitlines()[2:] if x.strip())
log = Path(os.environ['A15_LOG']); run = Path(os.environ['A15_RUN']).resolve()
kit = Path(os.environ['Q_KIT']).resolve(); sys.path.insert(0, str(kit / 'b'))
from z import seal
seal(kit)
import pc
sink, root, job = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
for p in (sink, root):
    if not (p == run or run in p.parents):
        raise ValueError('A15: planner path outside the scratch run folder: ' + str(p))
here = Path(__file__).resolve().parent
up = sink / 'up'
up.mkdir(parents=True, exist_ok=True)
names = pc.read(kit / 'k/y.json')
keys = sorted(v + '.j' + job + f'.part{i:02d}-of-04' for v in names['objects'].values() for i in range(4))
private = root / 'live_spool/private'
private.mkdir(parents=True, exist_ok=True, mode=0o700); os.chmod(private, 0o700)
sess = private / 'sess.json'
if not sess.exists():
    fd = os.open(sess, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(json.dumps({k: NOUPLOAD + str(up / k) for k in keys}, sort_keys=True))
os.environ['A15_UPSINK'] = str(up)
c = pc.Copier(kit, root, job, train=sink, writer=here / 'sw.py')
markers = sorted([*sink.glob('checkpoint_*/complete.json'), *sink.glob('m*/artifact.json')])
c.pass_once(final=False, small=False)
spool = root / 'live_spool'


def lines(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


state = {p.name: (pc.read(p) if p.suffix in ('.json', '.done') else None) for p in sorted((spool / 'state').glob('*'))}
receipts = lines(Path(str(spool / 'private/sess.json') + '.receipts.jsonl'))
writer_audit = [r for p in sorted(up.glob('audit_*.jsonl')) for r in lines(p)]
created = sorted(str(p) for base in (root, sink) for p in base.rglob('*') if p.is_file())
outside = [p for p in created if not Path(p).resolve().is_relative_to(run)]
receipt_paths = sorted({r.get('file') for r in receipts} | {r.get('local_sink') for r in receipts})
net = [e for e in events + writer_audit if e['event'] in NET or e['event'].startswith('socket.')]
spawned = [e for e in events if e['event'] in SPAWN]
foreign_spawn = [e for e in spawned if e['event'] == 'subprocess.Popen' and (str(here / 'sw.py') not in e['args'] or 'gc.py' in e['args'])]
done = {k: v for k, v in state.items() if k.endswith('.done')}
sent = {m.parent.name: ('gcs_' + m.parent.name + '.done') in done for m in markers}
ok = (ifaces == ['lo'] and bool(markers) and all(sent.values()) and not net and not foreign_spawn and not outside
      and all(str(r.get('local_sink', '')).startswith(str(up) + '/') and str(r.get('file', '')).startswith(str(run) + '/') for r in receipts))
out = dict(schema='a15-planner-v1', status='PASS' if ok else ('NOTHING_TO_SEND' if not markers and ifaces == ['lo'] else 'FAIL'),
           network_devices=ifaces,
           seconds=round(time.time() - t0, 1), sink=str(sink), root=str(root), markers=[str(m) for m in markers], sent=sent,
           order=[r.get('phase') for r in lines(spool / 'final_order.jsonl')], state=state, receipts=receipts,
           receipt_paths=receipt_paths, session_labels=dict(count=len(keys), prefix=NOUPLOAD + str(up) + '/'),
           network_events=net, spawned=spawned, foreign_spawn=foreign_spawn, files_created=created, outside_run=outside,
           retry_log=(spool / 'retry.log').read_text()[-4000:] if (spool / 'retry.log').exists() else '',
           writer_log=(spool / 'upload.log').read_text()[-4000:] if (spool / 'upload.log').exists() else '')
(log / 'plan.json').write_text(json.dumps(out, indent=1, default=str) + '\n')
print(json.dumps({k: out[k] for k in ('status', 'network_devices', 'seconds', 'sent', 'order', 'receipt_paths', 'network_events', 'foreign_spawn', 'outside_run')}, default=str)[:3000], flush=True)
sys.exit(0 if out['status'] in ('PASS', 'NOTHING_TO_SEND') else 1)
