"""fix12: assemble the n33 review packet locally from rd/<label>/ (outputs fetched from trinity-1-18).
Usage: mkpacket.py <label> <tar sha256> <mirror line> [extra notes file]"""
import sys, json, hashlib, shutil, subprocess
from pathlib import Path
L = Path('/scratch/jjyeung/orch_n30/tree_rebuild28/work'); F = L/'fix12'; label = sys.argv[1]; R = F/'rd'/label
TARSHA, MIRROR = sys.argv[2], sys.argv[3]
EXTRA = Path(sys.argv[4]).read_text() if len(sys.argv) > 4 else ''
P = F/'packet'; P.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
b = json.loads((R/'BUILD33.json').read_text()); seal = b['seal']
t1 = json.loads((R/'TEST_T1_33.json').read_text()); fu = json.loads((R/'TEST_FRAMES_33.json').read_text())
tchk = (R/'tchk.log').read_text()
# copies
def put(src, name): shutil.copyfile(src, P/name)
put(L/'fix10/DIFF.patch', 'fix10_census_DIFF.patch'); put(L/'fix11/DIFF.patch', 'fix11_frame_DIFF.patch')
put(L/'fix8/packet/DIFF_vs_9e809db4.txt', 'f1_DIFF_vs_9e809db4.txt')
for n in ('cn.py', 'sc.py', 'pf.py', 'pl.py'): put(F/'in'/n, 'merged_b_' + n)
for n, e in json.loads((F/'in/overlay.json').read_text()).items():
    if n.startswith('b/') and n[2:] not in ('cn.py', 'sc.py', 'pf.py', 'pl.py'): put(F/'in'/e['src'], 'merged_b_' + n[2:])
put(R/'j_merged.sh', 'merged_k_j.json.decoded.sh')
U='a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a'; put('/scratch/jjyeung/n30_mirror/tree_rebuild28/u/'+U, U); assert sha(P/U)==U and (P/U).stat().st_size==724
if (R/'SHA256SUMS.txt').exists(): put(R/'SHA256SUMS.txt', 'kit_SHA256SUMS.txt')
for n in ('BUILD33.json', 'TEST_T1_33.json', 'TEST_FRAMES_33.json', 'tchk.log', 'build.log'): put(R/n, 'out_' + n)
for n in ('b33.py', 'tchk33.py', 't1_33.py', 'fu33.py', 'overlay.json'): put(F/'in'/n, 'script_' + n)
for extra in sorted(R.glob('extra_*')): put(extra, 'out_' + extra.name)
# merged diff vs 489f7f0f (code files) and vs 9e809db4 (pf.py)
K0 = L/'fix11/kit/n_go'
d = []
for n in sorted(json.loads((F/'in/overlay.json').read_text())):
    if n == 'k/j.json': continue
    old = K0/n
    r = subprocess.run(['diff', '-u', '--label', 'a/' + n + ' (489f7f0f)', '--label', 'b/' + n + ' (merged)', str(old) if old.exists() else '/dev/null', str(F/'in'/json.loads((F/'in/overlay.json').read_text())[n]['src'])], capture_output=True, text=True)
    d.append(r.stdout)
r = subprocess.run(['diff', '-u', '--label', 'a/k/j.json:decoded (489f7f0f)', '--label', 'b/k/j.json:decoded (merged)', str(F/'j_old.sh'), str(R/'j_merged.sh')], capture_output=True, text=True); d.append(r.stdout)
(P/'merged_vs_489f7f0f.diff').write_text(''.join(d))
r = subprocess.run(['diff', '-u', '--label', 'a/b/pf.py (9e809db4)', '--label', 'b/b/pf.py (merged)', str(L/'fix8/kitsrc/pf_old.py'), str(F/'in/pf.py')], capture_output=True, text=True)
(P/'pf_py_vs_9e809db4.diff').write_text(r.stdout)
# member list vs 9e809db4
lines = ['# DIFF of the merged kit %s vs the installed-generation kit 9e809db4 (W/w28fix/n_go, seal %s)' % (seal, b['oldest_seal']),
         '# member  old_sha256 -> new_sha256  (mode old -> new); every other member is byte- and mode-identical', '']
for n, e in sorted(b['changed_vs_9e809db4'].items()):
    lines.append('%-16s %s -> %s  (%s -> %s)' % (n, e['old'] or '(absent)', e['new'] or '(absent)', e['mode_old'], e['mode_new']))
lines += ['', '# same list vs the F1 kit 489f7f0f (W/w30f1/n_go)']
for n, e in sorted(b['changed_vs_489f7f0f'].items()):
    lines.append('%-16s %s -> %s  (%s -> %s)' % (n, e['old'] or '(absent)', e['new'] or '(absent)', e['mode_old'], e['mode_new']))
lines += ['', '# decoded diffs: f1_DIFF_vs_9e809db4.txt (k/c.json, k/n.json, k/p.json, b/pf.py of F1), merged_vs_489f7f0f.diff (census + frame' + (' + later fixes' if len(json.loads((F/'in/overlay.json').read_text())) > 5 else '') + '), pf_py_vs_9e809db4.diff']
(P/'DIFF_vs_9e809db4.txt').write_text('\n'.join(lines) + '\n')
ch = b['changed_vs_9e809db4']
uploads = sorted(n for n in ch if n not in ('BUILD.json', 'SHA256SUMS.txt'))
inst = f"""# INSTALL n33 (merged kit {seal}); not installed by fix12

Source: trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w33n/n_go (tar W/w33n/s33n_n_go.tar sha256 {TARSHA}; {MIRROR}).

## Upload order (to Orchard, by the installer)
1. X/u/a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a (724 B, the F1 vqa receipt; copy: trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild28/u/, also in this folder). Check its sha256 on Orchard before step 2.
2. Kit members into X/n (changed vs the 9e809db4 generation; every other member is byte-identical, mode 0644 unchanged):
""" + ''.join('   - %s  %s%s\n' % (n, ch[n]['new'], '  (NEW file)' if ch[n]['old'] is None else '') for n in uploads) + f"""3. Last, so the seal flips only when every member is in place: X/n/BUILD.json {ch['BUILD.json']['new']} and X/n/SHA256SUMS.txt {ch['SHA256SUMS.txt']['new']}.
(If X/n is installed fresh instead, upload all members of the tar; the same check applies.)

## Post-install seal check (on Orchard, in X/n)
- `sha256sum -c SHA256SUMS.txt` -> every line OK ({len(open(R/'SHA256SUMS.txt').read().splitlines()) if (R/'SHA256SUMS.txt').exists() else 'all'} members; the kit's list is kit_SHA256SUMS.txt here); `sha256sum SHA256SUMS.txt` = {seal}.
- File count in X/n = SHA256SUMS lines + 2 (SHA256SUMS.txt, BUILD.json); no other file (no __pycache__).
- BUILD.json decoded (base64-json payload): kit_sha256 = {seal}, config_sha256 = {b['BUILD'].get('config_sha256')} = sha256(k/c.json).
- k/t_e047002134f979bd.tar = {b['pins']['k/t_e047002134f979bd.tar']}; k/y.json = {b['pins']['k/y.json']}; k/c.json {b['pins']['k/c.json']}; k/n.json {b['pins']['k/n.json']}; k/p.json {b['pins']['k/p.json']}.
- X/u/a7682dae... sha256 = a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a, 724 bytes.
- Every arm/install record that pins the kit seal or k/j.json (decoded a70b7551 before) must name {seal} and j decoded {b['j_decoded_sha256']}.
"""
(P/'INSTALL.md').write_text(inst)
fuok = fu['all_as_expected']
readme = f"""# n33 review packet: merged kit F1 + census + frame{EXTRA and ' + later fixes'} (fix12, lane tree_rebuild28)
Kit trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w33n/n_go, seal {seal} ({label}). Built from F1 kit 489f7f0f with the kit's support.reseal; the tree's launch_r1.build.verify(kit) == seal: {b['verify_kit_tree_equals_seal']}. Tar W/w33n/s33n_n_go.tar {TARSHA}; {MIRROR}. Not installed, not submitted.

## Merge
- fix10 DIFF.patch sha256 94d941e6135336c7dfac1e3bc0cebe88dc937287837687a73e151618f0716166 and fix11 DIFF.patch sha256 32c31d3735885136fb3f9128083d7fea32905e303af972788099f00f676a3fb6 verified before use (copies here).
- Code hunks applied with `patch` to the 489f7f0f bytes, no fuzz, no conflict: b/cn.py (new) 90b3ca6c, b/sc.py 43d4cc26, b/pf.py 5760c7df, b/pl.py ad29088a. The shared b/pl.py takes fix10's hunk at line 278 (scene publish s0=3.json, s1=a.json, s4=o.json) and fix11's at line 357 (offset 1: frames(cfg, request['frame_roots']) after pf.check in stage()); they touch different blocks, so both behaviours are kept as written. ad29088a equals fix11's own trial merge dd/pl_merge.py.
- k/j.json: decoded a70b7551 + fix11's decoded hunks = 65891ca5 (bash -n OK). support.cap cannot write a shell capsule (J.load JSON-parses the payload: {b.get('j_cap_error','')}), so the build uses fix11's tested capsule b718d5d9 after asserting its decoded payload equals 65891ca5 ({b['j_method']}). No hash was edited by hand.
- Modes: all members 0644 as in 489f7f0f (fix10's test kit w31cen had 0664 on cn/sc/pl; the bytes are equal).
{EXTRA}
## Unchanged pins (vs F1 kit 489f7f0f): {json.dumps(b['unchanged_vs_f1'])}
- tree tar k/t_e047002134f979bd.tar {b['pins']['k/t_e047002134f979bd.tar']}; k/c.json {b['pins']['k/c.json']}; k/n.json {b['pins']['k/n.json']}; k/p.json {b['pins']['k/p.json']} (no frame-fix change needed: the map lives in k/j.json); k/y.json {b['pins']['k/y.json']} (= 9e809db4's: {b['y_unchanged_vs_9e809db4']}); BUILD config_sha256 = sha256(k/c.json): {b['config_sha256_eq_cjson']}.

## F1, n_review1j criteria (1523Z item 4)
- (i) receipt a7682dae differs from e3ee51da only in division.path and equals 8091154c's division pin byte for byte: fix8 build (f1_review/README.md, BUILD_F1.json); the receipt is unchanged here (k/c.json, k/n.json, k/p.json byte-identical to F1).
- (ii) streams.vqa and r1_training.store_parameter point to a7682dae; no other key of c/n/p.json changes: fix8 decoded diff (f1_DIFF_vs_9e809db4.txt); the merge changes none of the three files.
- (iii) tree tar unchanged 5f2d77c4: above.
- (iv) division_admits on the staged bytes True: fix8 held-node T2 (f1_review/held_node_T1_T5.out); Trinity rerun on the merged kit, out_tchk.log: vqa division sub-check passes for a7682dae.
- (v) preflight b/pf.py receipts(): body unchanged from F1 (the merged pf.py adds only frames() and one docstring sentence; pf_py_vs_9e809db4.diff). Rerun on the merged kit (out_tchk.log): old 9e809db4 config {'REFUSE R1_STREAM_RECEIPT_REFUSED:vqa(division)' if 'REFUSE R1_STREAM_RECEIPT_REFUSED:vqa(division)' in tchk else 'SEE LOG'}; merged config {'PASS' if tchk.rstrip().endswith('PASS') else 'SEE LOG'}.

## Census, ORCH ANSWER 1604Z conditions (b)-(e) (RULING 1650Z A: GO on diff 94d941e6)
- (b) b/cn.py = the reviewed bytes 90b3ca6c; it recounts raw rows of the admitted population with the tree's Exclusions.expect/keep (fix10 REPORT, n_review1j 1648Z item 1b). Trinity T1 rerun on the merged kit (out_TEST_T1_33.json): T1 view equivalent {t1['T1_view_equivalent']}; T6 pool count = plain {t1['T6_pool_count_equals_plain_count']['ok']}.
- (c) tree unchanged, so coverage_report (s1_exclusions.py:319) runs as before with exact equality: T3 admitted census {t1['T3_admitted_census']}; controls T4 whole-store {t1['T4_whole_store_census_control']}; T5 planted listed row {t1['T5_leak_control']['result']}. Held node (fix10): all three call paths (:621, :657, :790) PASS with exact equality; four controls REFUSE.
- (d) whole = admitted + outside: T2 {json.dumps(t1['T2_whole_eq_admitted_plus_outside'])}; b/pl.py publishes sc/o.json as live/s4.json (merged pl.py hunk 1).
- (e) held-node run with real rows, prepare to its end: fix10 REPORT (16:26-16:37Z); n_review1j GO 1648Z on 94d941e6. The merged bytes of cn.py/sc.py equal the reviewed ones; the pl.py census hunk is unchanged.

## Frame fix tests (RULING 1650Z B: GO on diff 32c31d37)
- Static: merged decoded k/j.json = fix11's tested 65891ca5 (Q_NJ bind at /tmp/jjyeung/<ns>, five python steps on $Q_NJ, Q_E4 /data2 -> $Q_NJ/p/q/f/<sha256("$X/data2root")>); bash -n 0. fix11's job-bytes static check (o4: 0 resolve-output strings under the old q; plan request/config q-rooted) and held-node FrameAudit 301/301 per source + hash samples: fix11 REPORT; the bytes are identical here.
- Preflight unit tests on the merged kit (out_TEST_FRAMES_33.json, synthetic, tree resolve_read): all as expected = {fuok}: PASS when every source's pin lies under a root (pose/0 sample honours frame_prefix); R1_FRAME_ROOT_REFUSED for a frame outside the roots, a missing file under a root, and a symlink escaping a root; R1_FRAME_ROOT_MISSING (no roots, absent root); R1_FRAME_PREFLIGHT_DATABASE_MISSING; R1_FRAME_PIN_MISSING (no frame rows; no row with the prefix).
- Held node: fix11 t12 ran this same pf.py 5760c7df on the job's staged config: fixed PASS, 174134 mapping REFUSE R1_FRAME_ROOT_REFUSED:pointing. fix12 did not rerun it (RULING 1650Z item 2: the walk has the node).

## Build checks (out_BUILD33.json)
- py_compile every b/*.py ({len(b['py_compile'])} files): all ok = {b['py_compile_all_ok']}; bash -n every *.sh: {json.dumps(b['bash_n'])}; no __pycache__ in the kit: {b['pycache_in_kit'] == []}.
- Members added {b['members_added']}, removed {b['members_removed']}.

## Files
DIFF_vs_9e809db4.txt (member list old/new sha256), f1_DIFF_vs_9e809db4.txt, merged_vs_489f7f0f.diff, pf_py_vs_9e809db4.diff, fix10_census_DIFF.patch, fix11_frame_DIFF.patch, merged_b_*.py, merged_k_j.json.decoded.sh, out_* (build, tests), script_* (b33.py build, tchk33.py, t1_33.py, fu33.py, overlay.json), INSTALL.md, SHA256SUMS.txt.
"""
(P/'README.md').write_text(readme)
s = ''.join('%s  %s\n' % (sha(p), p.name) for p in sorted(P.iterdir()) if p.name != 'SHA256SUMS.txt')
(P/'SHA256SUMS.txt').write_text(s); print(s)
