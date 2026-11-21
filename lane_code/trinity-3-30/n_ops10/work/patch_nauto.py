"""n_ops10 patch of n_ops9/work/auto/nauto.py (ORCH NOTE 0659Z item 3, ORCH ANSWER 0658Z items 5-6). Usage: python3 patch_nauto.py SRC DST"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()

def rep(old, new):
    global s
    assert s.count(old) == 1, ('not unique', old[:80])
    s = s.replace(old, new)

# 1. judge a job only from parse lines that carry its own id
rep("raw = rd(M + '/last.raw'); age =",
    "lm = re.match(r'^\\S+ job=(\\S+) ', line)\n"
    "if not lm or lm.group(1) != job: line = ''  # n_ops10 (ORCH NOTE 0659Z): judge a job only from its own lines; a new job has no state until then\n"
    "raw = rd(M + '/last.raw'); age =")
rep("if sa:\n    p = sa.group(1).split('|');",
    "if sa and sa.group(1).split('|')[0].split('.')[0] == job:\n    p = sa.group(1).split('|');")

# 2. host key: the user accepted orchard-login-001's key (ANSWER 0658Z); the watch never stops on a host-key line
old_hk = s[s.index("# 1. host key:"):s.index("# 2. watcher alive")]
new_hk = '''# 1. host key (ORCH ANSWER 0658Z items 5-6, n_ops10): every line the watcher filtered is in mon/hk.log; the watch keeps running (no mon/stop).
# A warning line raises a BLOCKER. A fingerprint other than the accepted one, or a warning without any fingerprint, also writes HOSTKEY_ALERT,
# which makes sess_job.sh refuse to mint or install until ORCH answers. Lines naming only the accepted key without a warning are logged as alerts.
ACC = 'SHA256:lXwQfg9riWzIueT7rJbgpMFV4YEZuqAYP9ceieGEFDA'
hk = rd(M + '/hk.log').splitlines(); new_hk = hk[S.get('hk_n', 0):]; S['hk_n'] = len(hk)
warn = [l for l in new_hk if re.search(r'IDENTIFICATION HAS CHANGED|POSSIBLE DNS SPOOFING|Host key verification failed|Offending|has changed', l)]
fps = set(re.findall(r'SHA256:[A-Za-z0-9+/=]+', '\\n'.join(new_hk))); other = sorted(fps - {ACC})
if warn or other:
    gate = bool(other) or not fps
    if gate and not os.path.exists(HKA): open(HKA, 'w').write(utc + '\\n' + '\\n'.join(new_hk[:12]) + '\\n')
    alert('HOSTKEY', (warn or new_hk)[0])
    blocker(job, 'HOSTKEY', 'host-key line on the Orchard connection (fingerprints seen: %s; accepted %s; %s); watch keeps running: %s' % (
                ', '.join(sorted(fps)) or 'none', ACC, 'HOSTKEY_ALERT written, no mint or install' if gate else 'accepted key, mint not gated',
                ' / '.join(new_hk[:6])),
            'tail -20 %s/hk.log; cat %s' % (M, HKA), 'ORCH ANSWER 0658Z: tell ORCH with the full line; no session minted or installed until ORCH answers if the key is not the accepted one; read-only calls keep running; nobody edits ~/.ssh/config')
elif new_hk: alert('HOSTKEY_LINE', 'accepted key only: ' + new_hk[0])
'''
s = s.replace(old_hk, new_hk)
rep("if not tmux_has('nops_mon') and not os.path.exists(M + '/stop') and not os.path.exists(HKA):",
    "if not tmux_has('nops_mon') and not os.path.exists(M + '/stop'):")
rep("'HOSTKEY': ('cat n_ops8/work/HOSTKEY_ALERT; tail MON/hk.log', 'ORCH RULING 2152Z: hold all Orchard calls until the orchestrator answers; never edit known_hosts'),",
    "'HOSTKEY': ('tail -20 MON/hk.log; cat n_ops8/work/HOSTKEY_ALERT', 'ORCH ANSWER 0658Z: post the full line to ORCH; a key other than the accepted one: mint or install no session until ORCH answers; read-only calls continue'),")
open(dst, 'x').write(s)
print('patched', dst)
