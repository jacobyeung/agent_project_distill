"""Generate the A-only step-600 Orchard commands. Python 3.6 stdlib.

Usage: python gen600c.py [output-directory]
Inputs remain under in/; no connection or submission is made by this generator.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
OUT.mkdir(parents=True, exist_ok=True)
S = '/project/community/jjyeung/okh7/813f42db/c21a600'
WALLTIME = '03:00:00'
b = json.loads((HERE/'in/BIND600.json').read_text())
old = json.loads((HERE/'in/BIND400.json').read_text())
assert b['step'] == 600 and b['member_directory'] == 'm600'
assert b['run'] == '6ed2c7aa' and b['object'] == 'q8/8865619b/6ed2c7aa_m600.tar'
for k in ('config_sha256', 'base_identity', 'frame_layout', 'preparation_sha256', 'prep_paths'):
    assert b[k] == old[k], k
keys = ('base_identity', 'config_sha256', 'frame_layout', 'lineage', 'member_directory',
        'object', 'preparation_sha256', 'run', 'step', 'archive_bytes', 'archive_sha256')

def write(name, data):
    (OUT/name).write_text(data)

build = '#!/bin/bash\nset -euo pipefail\numask 077\nS=%s\ntest ! -e "$S"\nmkdir -m 700 "$S"\n' % S
for name, data in [('b.py', (HERE/'build_r11.py').read_text()),
                   ('bind.json', json.dumps({k:b[k] for k in keys}, sort_keys=True)),
                   ('read_plan.py', (HERE/'make_read_plan_c600.py').read_text()),
                   ('read_plan_template.json', (HERE/'in/out4s/A/READ_PLAN.json').read_text()),
                   ('d.py', (HERE/'in/dryres2.py').read_text()),
                   ('d2.py', (HERE/'dry2_c600.py').read_text())]:
    if name == 'b.py':
        data = data.replace("K = Path(os.environ.get('KROOT', '/project/community/jjyeung/okh7'))",
                            "K = Path('/project/community/jjyeung/okh7')")
    build += "cat > \"$S/%s\" <<'C600_EOF'\n%s\nC600_EOF\n" % (name, data)
build += '/usr/bin/python3 -I -s -B "$S/b.py" "$S" A "$S/bind.json" > "$S/build.out" 2>&1\ncat "$S/BUILD.json"\n'
write('o_build_c600.sh', build)

# Preserve the reviewed A-only fill's download flags and strict receipt checks.
pf = (HERE/'in/g400b/o_place_pull_fill10.sh').read_text()
pf = pf.replace('# place A and B (from S/BUILD.json), pull the four export parts once into A\'s a/e (no retries), fill A then B, dry checks; one nohup run',
                '# Place A, pull the four m600 parts once, fill and dry-check in one nohup run.')
pf = pf.replace('/813f42db/r10b', '/813f42db/c21a600')
for key in ('object', 'done', 'archive_sha256'):
    pf = pf.replace(str(old[key]), str(b[key]))
pf = pf.replace('--step 400', '--step 600').replace('05:00:00', WALLTIME)
pf = pf.replace('; PB=none', '').replace('; PB=$PB', '')
pf = pf.replace('  if [ $X = A ]; then p=$PA; d=$DA; h=$HA; else p=$PB; d=$DB; h=$HB; fi',
                '  p=$PA; d=$DA; h=$HA')
pf = pf.replace('  if [ \\$X = A ]; then P=\\$PA; T='+WALLTIME+'; D2=d2.py; else P=\\$PB; T=02:30:00; D2=d2b.py; fi',
                '  P=\\$PA; T='+WALLTIME+'; D2=d2.py')
pf = pf.replace(' A=$PA B=$PB', ' A=$PA')
pf = pf.replace('cat > "$S/fill.sh" <<SHELLCODE',
    '/usr/bin/python3 -I -s -B "$S/read_plan.py" "$PA" "$S/bind.json" "$S/read_plan_template.json" "$S/READ_PLAN_C600.json"\ncat > "$S/fill.sh" <<SHELLCODE')
# Keep the original pull loop and every surrounding guard byte-for-byte.
pull_start = pf.index('for i in 0 1 2 3; do\n')
pull_end = pf.index('\nfor X in A; do\n', pull_start)
pull = pf[pull_start:pull_end]
reuse_pin = {k: b[k] for k in ('object', 'archive_bytes', 'archive_sha256')}
assert b['archive_bytes'] == 4 * 5395758080
reuse = '''import hashlib
import os
import stat
import sys
from pathlib import Path

pin = %s
dest = Path(sys.argv[1])
fields = [pin['object'], str(pin['archive_bytes']), pin['archive_sha256']]
reuse = os.environ.get('REUSE_PARTS_FROM')
if reuse is None and os.environ.get('REUSE_SEARCH') == '1':
    root = Path('/project/community/jjyeung/okh7')
    with os.scandir(str(root)) as entries:
        names = sorted(e.name for e in entries if e.name.startswith('a15_cot_ap')
                       and e.is_dir(follow_symlinks=False))
    for name in names:
        source = root/name/'a/e'
        if source.resolve() == dest.resolve():
            continue
        try:
            marker = (source/'5').read_text().split()
        except FileNotFoundError:
            continue
        if marker == fields:
            reuse = str(source)
            break
if reuse is None:
    print('pull')
else:
    if not reuse:
        raise ValueError('REUSE_PARTS_FROM is empty')
    source = Path(reuse)
    if (source/'5').read_text().split() != fields:
        raise ValueError('Reuse marker differs from m600 pin')
    parts = [source/str(i) for i in range(4)]
    for part in parts:
        info = part.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size != pin['archive_bytes'] // 4:
            raise ValueError('Reuse part is not a regular file of pinned size: ' + str(part))
    digest = hashlib.sha256()
    for part in parts:
        with part.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
    if digest.hexdigest() != pin['archive_sha256']:
        raise ValueError('Reuse concatenated sha256 differs from m600 pin')
    for i in range(4):
        if os.path.lexists(str(dest/str(i))):
            raise ValueError('Reuse destination already exists: ' + str(dest/str(i)))
    for i, part in enumerate(parts):
        os.link(str(part), str(dest/str(i)), follow_symlinks=False)
    print('linked from %%s; part 0 link count %%d' %% (source, (dest/'0').stat().st_nlink))
''' % repr(reuse_pin)
fill = ('MODE=$( /usr/bin/python3 -I -s -B - "$E" <<\'REUSE_PY\'\n' + reuse +
        'REUSE_PY\n)\nif [ "$MODE" = pull ]; then\n')
# The outer, unquoted SHELLCODE heredoc must defer these expansions to fill.sh.
fill = fill.replace('$', '\\$') + pull
fill += '\n  echo "pulled; part 0 link count \\$(stat -c %h "\\$E/0")"\nelse\n  echo "\\$MODE"\nfi'
pf = pf[:pull_start] + fill + pf[pull_end:]
assert '$PB' not in pf and 'd2b' not in pf and 'm400' not in pf
write('o_place_pull_fill_c600.sh', pf)

resolve = ('S=%s\n' % S +
           'read P TOKEN < <(/usr/bin/python3 -I -s -B -c "import json;b=json.load(open(\'$S/BUILD.json\'));assert set(b)=={\'A\'};print(b[\'A\'][\'package\'],b[\'A\'][\'token\'])")')
assertions = '''import runpy
op=runpy.run_path(str(p/'a/6.py'),run_name='camera_guard')
assert op['COUNTS']==(150,150,150,0,0)
assert op['SCHEDULE']==((0,0),(0,1),(0,2))
assert op['descriptors'](str(p))==[dict(arm='tower',modes=['none'],stage1_select_rule='candidates_argmax',
    save_own_depth=False,perception_memo='on',perception_memo_modules=['g3t'],
    perception_memo_verify_ids=[],types=[0,1,2],expected=450)]
camera=['camera_displacement','camera_rotation','camera_movement_direction']
for name in ('a/0.json','a/1.json'):
    assert json.loads((p/name).read_text())['types']==camera
with tarfile.open(str(p/'0.tgz')) as archive:
    plan=json.load(archive.extractfile('9.json'))
assert plan['order'][:3]==camera and plan['export_binding']['step']==600
assert plan['export_binding']['object']=='q8/8865619b/6ed2c7aa_m600.tar'
'''
for short in ('cpu', 'sub', 'fetch'):
    text = (HERE/('in/ref/o_%s_A10b.sh' % short)).read_text()
    text = text.replace('P=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164', resolve)
    text = text.replace('/813f42db/r10b', '/813f42db/c21a600').replace('05:00:00', WALLTIME)
    text = text.replace('--job-name=a15_cot_apdc76460c3a164', '--job-name=a15_cot_ap${TOKEN}')
    if short == 'sub':
        text = text.replace("print('All CPU receipt checks passed')", assertions+"print('All CPU receipt and camera checks passed')")
    if short == 'fetch':
        text = text.replace('- "$JOB" <<', '- "$JOB" "$TOKEN" <<')
        text = text.replace("'dc76460c3a164'+format", "sys.argv[2]+format")
    assert 'dc76460c3a164' not in text
    write('o_%s_c600.sh' % short, text)
print('Wrote five A-only scripts to', OUT)
