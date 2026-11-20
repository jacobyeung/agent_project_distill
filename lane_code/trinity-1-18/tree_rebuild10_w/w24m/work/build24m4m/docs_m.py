from common import *
t=J.load(D/'TREE_CPRIME.json');s=J.load(D/'SEALS.json');u=J.load(L/'out/UPLOADS_24M4M.json')
replace(L/'out/TREE_CPRIME2.md',f'''C″ has seal `{t['after']}` and 945 files, computed by the tree's own `source_seal.inventory` and `p3_provenance.digest`.

C′ has seal `{t['before']}`. The exact Cursor test patch has SHA256 `{t['patch_sha256']}`; it applies without fuzz or offsets. Only `tests/test_host24j.py` differs from C′. The fixture uses null pixel fields and explicitly tests refusal of non-null legacy pixel fields.

The four differences from tree C (`0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de`) are `launch_r1/entry.py`, `student_pilot/carrier_c1_run.py`, `tests/test_host24j.py` and `tests/test_r1_processor_compat.py`. The original processor patch has SHA256 `{t['original_patch_sha256']}`. No other tree file changed.

The native host suite passes 15/15, including its untouched-tree comparison; processor compatibility passes 3/3. There are no skips or errors in the final runs. `work/build24m4m/TREE_TESTS.json` records results; `TREE_CPRIME.json` records the inventory and `TREE_DIFF.patch` records the sole change from C′. The untouched comparison tree is available at `work/tree_r1_base`.

Each kit changes exactly nine tree-dependent files: its archive, `k/7.json`, `k/c0.json`, `k/p.json`, `k/c.json`, `k/n.json`, `k/a.json`, `SHA256SUMS.txt` and `BUILD.json`. `EXACT_KIT_DELTA.json` verifies all other decoded fields and files are unchanged; `DEPENDENT_PINS.json` and `PIN_AUDIT.json` verify the dependent identities and archives. The runtime source record is `u/92493d10ec22cc089aac5bbd98a45f4e6d39ac271bd4970488b4831c016247b9`.

The independent review's verdict is GO AFTER FIXES; its required fixture edit and recommended refusal test are both applied. These CPU fixtures do not establish production-row equivalence or a real processor/GPU forward pass.
''')
p=L/'out/ARM_ROUTING_USAGE.md'
replace(p,p.read_text().replace('/w24l','/w24m').replace('build24m4l','build24m4m').replace('24M4L','24M4M').replace('24m4l','24m4m'))
p=L/'out/RCJ_USAGE.md';s=p.read_text();first=s.index('\n\n')
s=f'''The CPU helper supports `b` for P-only reconstruction and `r` for the sealed kit's native regeneration path. Apply `UPLOADS_24M4M.json/.list` against q/n/qd seals `72bf8930`, `1015612f`, `259c14de`, `rcj/x.py` SHA256 `7b9d646994904cca6f9bf22c94b8a30bbd5ff08287d7b7c16dc2e7a99f33947f` and `rcj/rcj.sh` SHA256 `b23393f2db4dfe65bbd91a771fb7c5d34f51a5669b820c33b6158fb68f9f5e8c`. The ordinary delta contains {u['total_files']} files and {u['total_bytes']} bytes. `rcj.sh` is byte-identical to its baseline. `UPLOADS_24M4M_GO.json` separately overlays the new n seal.'''+s[first:]
s=s.replace('q24lr','q24mr').replace('q24l','q24m').replace('C′','C″')
s=s.replace('Both launch mount fixes remain: the runtime path exists before binding, and the job namespace is installed before `/tmp` is remounted read-only.', 'Mode r builds its root with `host_root()`, preserving host top-level directories and symlinks while leaving `/scratch`, `/tmp`, `/proc` and `/dev` for explicit mounts. The runtime path exists before binding, and the job namespace is installed before `/tmp` is remounted read-only. The mode-r `rdiff()` sandbox also uses `host_root()`. Processor N/P child sandboxes already construct an empty root through `rb.command()` and need no change. Mode-b commands are byte-identical to 24m4l for plan, run and check.')
s=s.replace('`RCJ_L_TESTS.json`,', '`work/build24m4m/COMMAND_TESTS.json`, `RCJ_L_TESTS.json`,')
s+='\nThe local rdiff mount fixture binds the interpreter roots because Trinity installs Python under `/scratch`; its staged tree is a real copy inside the job root. It reaches the production database-hash refusal through the real comparison script. The new root builder is also checked with mocked host entries, including a host without `/scratch`. `FAILURES.json` retains the setup failures and their outputs.\n'
replace(p,s)
print('Tree, CPU helper and arming usage documents written')
