import datetime
import hashlib
import json
from pathlib import Path
import re

L = Path(__file__).resolve().parents[1]
OUT = L / 'out'
M = OUT / 'measurements'
sim = json.loads((M / 'simulation.json').read_text())
live = json.loads((M / 'dry-new-lanes.json').read_text())
recovery = json.loads((M / 'review-recovery.json').read_text())
evidence = json.loads((M / 'rule-evidence.json').read_text())
oldstats = (M / 'dry-old.stats').read_text().strip()
newstats = (M / 'dry-new.stats').read_text().strip()
tests = (L / 'work/all-tests-round1.txt').read_text()
(M / 'tests.txt').write_text(tests)
oldbytes = int(re.search(r'bytes=(\d+)', oldstats)[1])
newbytes = live['bytes']
parts = []


def write(text):
    parts.append(text.strip() + '\n\n')


def table(headers, rows):
    def fmt(x):
        return '{:,}'.format(x) if isinstance(x, int) else str(x)
    write('| ' + ' | '.join(headers) + ' |\n|' + '|'.join(['---'] * len(headers)) + '|\n' +
          '\n'.join('| ' + ' | '.join(fmt(x) for x in row) + ' |' for row in rows))


write('VERDICT: DONE All requested review fixes pass regression and package tests; the local scan keeps {:,} of {:,} bytes.'.format(newbytes, oldbytes))
write('The package replaces `tools/lane_code_filter.py` and `tools/dry_count.py`. It preserves authored kits and all 52 inventoried codex run-record directories, excludes the identified generated outputs, and restricts root-lane protection to node labels. Both scanner paths use the same predicates. DEDUP gzip headers remain deterministic. The preserved input package is `../out_round1/`.')
write('## Review round 1: finding -> fix -> test')
table(['Finding', 'Fix', 'Regression test and evidence'], [
    ['1: suffix false positives', 'Exempt word-plus-number endings with one to three digits from the generic suffix rule; keep the explicit tempfile families and 32-hex rule.', '`test_finding1_word_number`: kit_parity50, so_reads228 and h_shell400 stay eligible; explicit driver and random mixed suffixes remain excluded.'],
    ['1: run records', 'Protect each direct codex_runs child directory, except repository metadata, and mirror that protection in dry_count.', '`test_finding1_run_records` and `test_finding6_default_ancestor_gate`: both requested timestamped records survive; generated children remain excluded.'],
    ['2 and 3: root context', 'Only labels matching trinity-<n>-<n> protect all root children. Lane, kit, tools and briefs labels receive ordinary root gates.', '`test_findings2_3_context`: real fixture scans agree between node and lane contexts, including a 2,002-entry directory; kit output/cache/environment directories are excluded. The original reviewer probe reports hourly=3 and dry_count_view=3 in both modes.'],
    ['4: Python source files', 'Remove /lib/python from SUBSTR; add directory-only PATHRE /lib/python[0-9][^/]*/.', '`test_finding4_directory_python`: python_compat.py and python3_compat.py survive; Python 2.7/3.12 library directories are excluded.'],
    ['5: clear by-products', 'Exclude work/{fcopy,scopy,lcopy,pcopy} and the four observed pytest output names below work/ or out/.', '`test_finding5_proven_outputs`: generated copies and pytest trees are excluded; work/base, replay*, pytest_helpers, and source pytest_kit remain eligible.'],
    ['6: default dry_count mode', 'Document unconditional ancestor gating in this report and GIT_OWNER.md.', '`test_finding6_default_documented` checks both documents; `test_finding6_default_ancestor_gate` exercises an unset environment.'],
    ['7: existing regex anchor', 'Keep $ on the pre-existing DIRRE alternatives; new alternatives use \\Z.', '`test_finding7_old_anchor`: results\\n and tmp_x\\n remain excluded; the new test_runs alternative does not accept a trailing newline.'],
])
write('All eight regression methods fail against the preserved package (13 assertion/subtest failures) and pass against the replacement package. The tests adapt the reviewer\'s context, kit, and fixture probes. Full evidence is in [review-before.txt](measurements/review-before.txt), [review-after.txt](measurements/review-after.txt), and [reviewer-probes.txt](measurements/reviewer-probes.txt). The comparison intentionally retains before/after evidence because the task requires failing regressions before each fix.')
write('Ancestor gates apply even when `LCS_REVIEW2_FIXES` is unset. This changes dry_count\'s default mode from checking only the selected directory to checking its ancestors too. Its main function remains byte-identical to `in/tools/dry_count.py`. The existing environment flag still controls cross-boundary substring filtering and the deduplication ambiguity guard. Node-wide and per-folder deduplication can yield different counts even when their path gates agree.')
write('`land_kit.py` runs the filter with label `kit`, so its root receives normal name/path/MAXDIR gates. Newly excluded classes include generated test outputs, temporary and 32-hex directories, attic/sandbox/rehearsal/fixtry trees, versioned Python libraries, payload environments, extracted archives, nested lane copies, and generated build work/review/integration directories. Kit landing refuses skipped members unless the owner passes `--allow-skips`; the package includes [GIT_OWNER.md](GIT_OWNER.md) as an accompanying note, not an installed replacement.')
write('## Rule decisions from the inventories')
write('The additional pytest rule names only `pytest_kit`, `pytest_dry`, `pytest_dry_verified`, and `pytest_patched` beneath a `work/` or `out/` ancestor. Their listed descendants are test-case directories containing synthetic packages, generated JSON, and shell stubs. A global pytest-prefix rule could discard source helpers, so other pytest-prefixed names remain eligible. The nested copy rule names only the four requested direct children of work/.')
table(['Rule', 'Matching file observations', 'Matching listed bytes'],
      [[name, evidence['rules'][name]['files'], evidence['rules'][name]['bytes']]
       for name in ('Named pytest output trees', 'Nested lane copies')])
write('These evidence counts can overlap other exclusions. [review-recovery.json](measurements/review-recovery.json) records the incremental path decisions for each commit. All nine kit_parity50 trees survive. All 52 codex run-record directories survive, including the six identified by the reviewer. These checks cover inventoried prompt.md, final_message.md and meta.json files.')
write('`work/base` and `replay*` stay eligible as requested. The inventories show source and source-test trees under base; the replay trees are repeated but their names alone do not establish that every member is a generated output. Runtime, vendor, ordinary build directories, and other ambiguous names also stay eligible. [RULES.md](RULES.md) records all accepted and rejected rules and their evidence.')
write('## Measured live scan on trinity-2-28')
write('Both robust scans exited 0 with no manifest argument, stdout redirected to /dev/null, nice -n 10, and timeout 600. The old scan took 11 seconds; the new scan took 2 seconds (wall-clock measurements rounded to whole seconds). Both reported zero timeout, I/O and changed-file skips. The new scan selected {:.2f}% fewer bytes. These are observations of a changing live tree, which includes the preserved package and review fixtures, not a frozen-snapshot comparison.'.format(100.0 * (oldbytes-newbytes)/oldbytes))
write('```text\n' + oldstats + '\n' + newstats + '\n```')
write('The meter forwards the filter\'s output to /dev/null and stats each selected file. Its totals exactly match STATS; it reports no stat errors or incomplete output records. The table lists up to 20 lanes after global content deduplication.')
table(['Top-level lane', 'Kept files, measured', 'Kept bytes, measured'], live['lanes'][:20])
write('The exact commands were the same scan commands as the input package, with fresh output filenames:\n\n```bash\ncd /scratch/jjyeung/orch_n30\nexport CUDA_VISIBLE_DEVICES="" LCS_ROBUST_SYNC=1\nnice -n 10 timeout 600 /usr/bin/python3 -I -s -B - trinity-2-28 < /scratch/jjyeung/orch_n30/sm_filter/in/tools/lane_code_filter.py > /dev/null 2> /scratch/jjyeung/orch_n30/sm_filter/work/dry-old-round1.stats\nnice -n 10 timeout 600 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/sm_filter/out/tests/meter_scan.py /scratch/jjyeung/orch_n30/sm_filter/out/tools/lane_code_filter.py trinity-2-28 /scratch/jjyeung/orch_n30/sm_filter/work/dry-new-round1-lanes.json > /dev/null 2> /scratch/jjyeung/orch_n30/sm_filter/work/dry-new-round1.stats\n```')
write('The sandbox refused tmux socket access before either scan started; the managed command session ran both scans sequentially. No killed scan was retried.')
write('## Inventory simulation')
write('The before columns sum all listed files in the eight inventories. The after columns are path-only estimates computed exactly from those inventories: size limits, extension gates, MAXDIR, filesystem state and deduplication are not simulated. Historical DEDUP blobs retain their listed sizes. The replay applies root protection according to each label, including tools and briefs. The independent reviewer replay agrees on every commit and label.')
table(['Commit', 'Before files', 'Before bytes', 'After files, estimated', 'After bytes, estimated'],
      [[c]+v for c,v in sorted(sim['totals'].items())])
write('Six commits keep fewer than 40,000,000 listed bytes. The two larger commits contain the following retained groups. The package preserves their sources, kits and delivery folders; no future deduplication savings are assumed.')
for c,v in sorted(sim['totals'].items()):
    if v[3] > 40000000:
        write('Retained groups in `{}` ({:,} bytes total):'.format(c,v[3]))
        table(['Directory group', 'Listed bytes kept'], sim['groups'][c]['kept'][:12])
write('Per-label counts include zero rows and a repository label for updates outside lane_code/.')
table(['Commit', 'Label', 'Before files', 'Before bytes', 'After files', 'After bytes'], sim['rows'])
write('The largest input commit is `{}`. The following top-30 groups use label plus up to five directory components, so rows do not double-count files.'.format(sim['largest_commit']))
for kind in ('kept','excluded'):
    write('Top 30 {} directory groups:'.format(kind))
    table(['Directory group', 'Listed bytes, path-only'], sim['groups'][sim['largest_commit']][kind][:30])
write('## Tests and reproduction')
write('Run all package tests from the workspace:\n\n```bash\nnice -n 10 bash out/tests/run_all.sh\n```\n\nExact output:\n\n```text\n'+tests.rstrip()+'\n```')
write('The fixture suite checks exact NUL-separated traversal output, shared robust/legacy rules, FIFO and symlink handling, MAXDIR, protected source and delivery directories, deterministic gzip bytes, and unchanged dry_count main. Installer tests exercise hostname/lock/checksum/preimage guards, staged syntax checks, backup verification, rollback and partial-install recovery entirely below work/tmp_*.')
write('The review regression comparison and simulation commands are:\n\n```bash\nROUND1_TARGET=/scratch/jjyeung/orch_n30/sm_filter/out_round1 nice -n 10 /usr/bin/python3 -I -s -B out/tests/test_round1.py\nnice -n 10 /usr/bin/python3 -I -s -B out/tests/test_round1.py\nnice -n 10 /usr/bin/python3 -I -s -B out/tests/simulate.py in/commits\nnice -n 10 /usr/bin/python3 -I -s -B work/tmp_review/review_sim_round1.py\nnice -n 10 /usr/bin/python3 -I -s -B work/tmp_review/review_tests.py\n```')
write('The first command deliberately exits 1 (eight methods, 13 failures); the second exits 0 (eight methods, OK). Full exact outputs are linked above. The simulation commands emit the JSON in measurements/simulation.json and measurements/reviewer-simulation.json; the reviewer probe output is preserved in measurements/reviewer-probes.txt. Python 3.11 and 3.12 are unavailable on PATH; all executable tests ran on /usr/bin/python3 3.6.8.')
write('## Owner package')
write('Complete replacements are in tools/; unified diffs against in/tools/ are in patches/. PREIMAGE.sha256 contains the two supplied input hashes with tools/ prefixes. POSTIMAGE.sha256 names the same replacements. SHA256SUMS covers every package file except itself. The patches apply to copied inputs and reproduce the replacement bytes. The package and preserved out_round1 checksums verify.')
write('On trinity-3-30, from this package directory:\n\n```bash\nB=<orch_n30-dir> S=<sync-state-dir> bash -eu install.sh\n# Roll back using the backup path printed by installation:\nB=<orch_n30-dir> S=<sync-state-dir> bash -eu rollback.sh <backup-dir>\n```')
write('Installation takes the existing nonblocking sync lock (exit 3 if held), verifies package and preimage hashes, saves and verifies a preimage archive, stages and syntax-checks both files, replaces them, and checks POSTIMAGE. The filter is installed before dry_count. Rollback uses the same hostname gate and lock, accepts either image after a partial installation, and refuses unrelated manual edits. Both commands preserve robust mode. The package has not been installed.')
write('## Limits and remaining work')
write('A source directory with another temporary-looking name can still match the generic rules. The word-plus-number exemption also admits some random temporary names. File extensions, size limits, cache rules and deduplication still apply inside protected folders. Generated children and excluded ancestors can suppress a nested deliverable. Protected directories bypass MAXDIR; monitor STATS and scan duration after installation, especially skipped_timeout under the production 144-second scan budget.')
write('Only trinity-2-28 has a fresh live scan. Other nodes have inventory coverage; their runtime remains unmeasured. Deterministic gzip prevents header-only changes, but changing any duplicate pair still changes the large manifest. Future hourly growth and actual manifest savings are unmeasured. The owner still needs to review and install the package; no Git, SSH, production writes, or deletion ran for this task.')
write('The requested review mapping and before/after regression evidence are retained despite the no-archaeology writing rule because the user explicitly requested them. No other superseded measurements are presented as current results.')
(OUT / 'REPORT.md').write_text(''.join(parts))
print('Wrote report with current tests, scan data, and simulation tables')
