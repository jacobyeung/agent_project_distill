"""fix17: unit tests of b/pf.py frames() and audit_roots() on the w34 kit, with the kit tree's own resolve_read and
relocated (no frame root map set: resolve_read returns the pin path). Usage: fu34.py <kit> A|B <out json>.
A: fix12's nine fu33 cases unchanged, audit_roots stubbed to the identity (frames() logic as before).
B: run inside bwrap with one host folder bound at the namespace /tmp/q_22c714e1 and at /tmp/jjyeung/q_22c714e1
   (and a different folder over .../jjyeung/.../root3): the real audit_roots on request roots spelled under the
   namespace; pins spelled under the second name (as the map produces them) PASS, the same pins under the
   namespace spelling REFUSE (the audit compares the second name), and audit_roots refuses by name."""
import sys, json, os, sqlite3, hashlib
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); NEW = Path(sys.argv[1]); MODE = sys.argv[2]; OUTF = Path(sys.argv[3])
for k in [k for k in os.environ if 'FRAME_ROOT_MAP' in k]: del os.environ[k]
sys.path[:0] = [str(W/'w30f1/tree'), str(NEW/'b')]
import pf
from z import load
STUBBED = hasattr(pf, 'census')
if STUBBED: pf.census = lambda cfg, limit=100: {}
from student_pilot.r1_persisted import scope
NSP = load(NEW/'k/p.json')['namespace']
res = dict(mode=MODE, namespace=NSP, census_stubbed=STUBBED)
if MODE == 'A':
    pf.audit_roots = lambda roots: [str(r) for r in roots]
    D = OUTF.parent/'futmpA'; NSD = D; NJD = D
else:
    NS = Path(NSP); NJ = Path('/tmp/jjyeung')/NS.name
    D = NS/'p/q/fu'; NSD = D; NJD = NJ/'p/q/fu'
    assert os.stat(NS).st_ino == os.stat(NJ).st_ino, 'bind missing'
D.mkdir(parents=True, exist_ok=MODE == 'B'); R1 = D/'root1'; R2 = D/'root2'; OUTSIDE = D/'elsewhere'
for d in (R1, R2, OUTSIDE): d.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def obj(name, v):
    p = D/name; p.write_text(json.dumps(v, sort_keys=True)); return dict(path=str(p), sha256=sha(p))
def db(name, rows):
    p = D/name; c = sqlite3.connect(str(p)); c.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT)')
    c.executemany('INSERT INTO rows VALUES (?,?)', [(i, json.dumps(r)) for i, r in enumerate(rows)]); c.commit(); c.close()
    return dict(path=str(p), sha256=sha(p))
def frame(d, rel, spell=None):
    p = d/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'png' + rel.encode())
    return str((spell or NSD)/p.relative_to(D))
def row(*paths): return dict(student_input=dict(frames=[dict(path=x) for x in paths]))
def receipt(name, dbpin): return obj(name + '.json', dict(schema='c1-stream-v1', stream=name, database=dbpin))
def run(streams, rts):
    try:
        with scope({}):
            return 'PASS ' + json.dumps(pf.frames(dict(streams=streams), rts), sort_keys=True)
    except ValueError as e:
        return 'REFUSE ' + str(e)
def cases(spell, tag):
    fa = frame(R1, 'k6tk/a.png', spell); fb = frame(R2, 'u/b.png', spell); fo = frame(OUTSIDE, 'k6tk/o.png', spell); fp = frame(R1, 'k7pd/p.png', spell)
    link = R1/'k6tk/link.png'
    if not link.is_symlink(): link.symlink_to(OUTSIDE/'k6tk/o.png')
    lk = str(spell/link.relative_to(D))
    good = dict(pointing=receipt(tag + 'pointing', db(tag + 'p.sqlite', [dict(x=1), row(fa)])),
                vqa=receipt(tag + 'vqa', db(tag + 'v.sqlite', [row(fb)])),
                mdg=dict(path=str(D/'absent_mdg.json'), sha256='0'*64))
    pose_db = db(tag + 'pose.sqlite', [row(fo), row(fp)])
    good['pose'] = obj(tag + 'mix.json', dict(schema='c1-pose-mix-v1', sources=[dict(kind='rows', receipt=receipt(tag + 'pose0', pose_db), frame_prefix=str(spell/'root1/k7pd')),
                                                                          dict(kind='rows', receipt=receipt(tag + 'pose1', db(tag + 'pose1.sqlite', [row(fa)])))]))
    roots = [str(R1), str(R2)]
    r = {}
    r['U1_all_sources_under_roots (expect PASS, pose/0 sample honours frame_prefix)'] = run(good, roots)
    r['U2_pointing_frame_outside_roots (expect R1_FRAME_ROOT_REFUSED:pointing)'] = run(dict(good, pointing=receipt(tag + 'pointing2', db(tag + 'p2.sqlite', [row(fo)]))), roots)
    r['U3a_no_roots (expect R1_FRAME_ROOT_MISSING)'] = run(good, [])
    r['U3b_root_absent (expect R1_FRAME_ROOT_MISSING)'] = run(good, [str(R1), str(D/'nope')])
    r['U4_database_absent (expect R1_FRAME_PREFLIGHT_DATABASE_MISSING:vqa)'] = run(dict(good, vqa=receipt(tag + 'vqa4', dict(path=str(D/'none.sqlite'), sha256='1'*64))), roots)
    r['U5_no_frame_rows (expect R1_FRAME_PIN_MISSING:vqa)'] = run(dict(good, vqa=receipt(tag + 'vqa5', db(tag + 'v5.sqlite', [dict(a=1), dict(student_input=dict(frames=[]))]))), roots)
    r['U6_frame_file_missing_under_root (expect R1_FRAME_ROOT_REFUSED:vqa)'] = run(dict(good, vqa=receipt(tag + 'vqa6', db(tag + 'v6.sqlite', [row(str(spell/'root2/u/missing.png'))]))), roots)
    r['U7_symlink_under_root_to_outside (expect R1_FRAME_ROOT_REFUSED:vqa)'] = run(dict(good, vqa=receipt(tag + 'vqa7', db(tag + 'v7.sqlite', [row(lk)]))), roots)
    r['U8_prefix_with_no_matching_row (expect R1_FRAME_PIN_MISSING:pose/0)'] = run(dict(good, pose=obj(tag + 'mix8.json', dict(schema='c1-pose-mix-v1', sources=[dict(kind='rows', receipt=receipt(tag + 'pose8', pose_db), frame_prefix=str(spell/'zz'))]))), roots)
    exp = ['PASS', 'R1_FRAME_ROOT_REFUSED:pointing:', 'R1_FRAME_ROOT_MISSING', 'R1_FRAME_ROOT_MISSING', 'R1_FRAME_PREFLIGHT_DATABASE_MISSING:vqa',
           'R1_FRAME_PIN_MISSING:vqa', 'R1_FRAME_ROOT_REFUSED:vqa:', 'R1_FRAME_ROOT_REFUSED:vqa:', 'R1_FRAME_PIN_MISSING:pose/0']
    return r, exp, good, roots
def check(r, exp): return [(e == 'PASS' and v.startswith('PASS')) or (e != 'PASS' and v.startswith('REFUSE ' + e)) for e, v in zip(exp, r.values())]
ok = []
if MODE == 'A':
    r, exp, _, _ = cases(NSD, 'a_'); res['cases'] = r; ok += check(r, exp)
else:
    r, exp, good, roots = cases(NJD, 'j_'); res['cases_pins_second_name'] = r; ok += check(r, exp)
    rc, _, goodc, _ = cases(NSD, 'n_')
    res['C1_control_pins_namespace_spelling (expect R1_FRAME_ROOT_REFUSED:pointing)'] = v = run(goodc, roots)
    ok.append(v.startswith('REFUSE R1_FRAME_ROOT_REFUSED:pointing:'))
    def ar(x):
        try: return 'PASS ' + json.dumps(pf.audit_roots(x))
        except ValueError as e: return 'REFUSE ' + str(e)
    (D/'afile').write_text('x'); (D/'adir').mkdir(exist_ok=True)
    if not (D/'alink').is_symlink(): (D/'alink').symlink_to(D/'adir')
    a = {}
    a['A1_two_roots (expect PASS, second-name spellings)'] = v = ar(roots); ok.append(v == 'PASS ' + json.dumps([str(NJD/'root1'), str(NJD/'root2')]))
    for name, x, e in (('A2_namespace_itself', str(NS), 'R1_FRAME_ROOT_NAME_REFUSED:'), ('A3_missing_dir', str(D/'nope'), 'R1_FRAME_ROOT_MISSING:'),
                       ('A4_root_already_second_name', str(NJD/'root1'), 'R1_FRAME_ROOT_NAME_REFUSED:'), ('A5_dotdot', str(D/'root1/../root2'), 'R1_FRAME_ROOT_NAME_REFUSED:'),
                       ('A6_outside_namespace', str(W), 'R1_FRAME_ROOT_NAME_REFUSED:'), ('A7_file', str(D/'afile'), 'R1_FRAME_ROOT_NAME_REFUSED:'),
                       ('A8_symlink_dir', str(D/'alink'), 'R1_FRAME_ROOT_NAME_REFUSED:'), ('A9_twin_other_inode', str(D/'root3'), 'R1_FRAME_ROOT_NAME_REFUSED:')):
        a[name + ' (expect ' + e + ')'] = v = ar([str(R1), x]); ok.append(v.startswith('REFUSE ' + e))
    res['audit_roots'] = a
res['per_case_ok'] = ok; res['all_as_expected'] = all(ok)
OUTF.write_text(json.dumps(res, indent=1) + '\n'); print(json.dumps(res, indent=1))
