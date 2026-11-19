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
