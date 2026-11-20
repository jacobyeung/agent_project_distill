from pathlib import Path
import sys,json,hashlib,ast
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4q'
sys.path[:0]=[str(L/'out/kit_qd/b'),str(L/'out/rcj')]
import z,pc

def line(path,needle):
 return next(i for i,s in enumerate((L/path).read_text().splitlines(),1) if needle in s)
def ref(path,needle):return f'`{path}:{line(path,needle)}`'
def write(path,v):z.write(L/path,v)
cfg=z.load(L/'out/kit_qd/k/n.json');p=json.loads((L/'work/build24m4n/inputs/b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad').read_bytes())
spec=z.load(L/'out/kit_qd/k/p.json');h=cfg['extent_receipt']['sha256']
u=next(v for v in spec['uploads'] if v['sha256']==h)
manifest=json.loads((L/'work/build24m4p/PACKAGE_MANIFEST.json').read_bytes())['files']
real=[n for n,v in manifest.items() if v.get('sha256')==h]
assert not real
write('work/build24m4q/N_BINDINGS.json',dict(kit_sha256=z.sha(L/'out/kit_qd/SHA256SUMS.txt'),config=cfg,extent_upload=u,P_config_extent_receipt=p.get('extent_receipt'),authentic_extent_receipt_members=real))
model=json.loads((L/'work/build24m4n/inputs/cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7').read_bytes())
assert z.sha(L/'work/build24m4n/inputs/cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7')=='cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7'
write('work/build24m4q/ASSET_PINS.json',dict(receipt_sha256='cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7',logical_root=model['root'],files={n:v for n,v in model['files'].items() if n in pc.ASSETS}))
text=f'''N pins extent receipt `{h}` at `u/{h}` ({ref('work/build24m4q/N_BINDINGS.json','"extent_receipt":')}; encoded kit input `out/kit_qd/k/n.json:1`). The planner localizes this to `<namespace>/p/q/u/{h}` ({ref('out/kit_qd/b/pl.py','def localize')}; {ref('work/tree_r1c/launch_r1/entry.py','def stage_host')}). The kit lists a 12,061,474-byte authenticated upload, not a builder invocation ({ref('work/build24m4q/N_BINDINGS.json','"extent_upload":')}).

The supplied package has no file with that receipt hash. Its same-named fixture files are stand-ins. Its author and original row set therefore cannot be established from the supplied receipt fields; `cand_cmp.json` will publish those fields, source QID hash/count, and comparisons against P's actual database. P's authenticated config `b08fe50c…` has no `extent_receipt` field (`work/build24m4n/inputs/b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad:1`). “P's receipt” here means the pinned audit that must first prove it covers P's row content, not a pin in P's config.

`r1_handover` allows an extent-pin difference; it does not rebuild or rebind that receipt ({ref('work/tree_r1c/student_pilot/r1_handover.py',"'extent_receipt':")}; {ref('work/tree_r1c/student_pilot/r1_handover.py','def bind_target')}). `bind_target` updates continuation identities and writes a handover map. No extent rebinding is implemented by the kit's planner or mode-r entry.

C'' copies the nine top-level fields into rendered rows ({ref('work/tree_r1c/student_pilot/carrier_c1_routing.py',"for key in ('source_qid'") if "for key in ('source_qid'" in (L/'work/tree_r1c/student_pilot/carrier_c1_routing.py').read_text() else '`work/tree_r1c/student_pilot/carrier_c1_routing.py:812`'}). Native `content()` includes those fields, and `Extents.check()` refuses a different digest as `EXTENT_ROW_UNAUDITED` ({ref('work/tree_r1c/student_pilot/extent_receipt.py','def content')}; {ref('work/tree_r1c/student_pilot/extent_receipt.py','def check')}). An audit built on P's different content cannot certify those N rows. The exact production mismatch count is unmeasured locally; the CPU job records it with N's current pin, alongside the DB count and the number of rows checked.

The CPU helper captures the exact config passed from `stage_host` to `rg.regenerate`, then runs the diagnostic in `finally` when N's database exists ({ref('out/rcj/x.py','def observed')}). It constructs the native `Rows` reader over the physical stores, with the same admission settings and authenticated pins, and calls `Rows.row` for every routing SQL index ({ref('out/rcj/ch.py','def scan')}; `work/tree_r1c/student_pilot/carrier_c1_run.py:1109`). Transparent wrappers count wording, text, extents, R1, reserve and optional R2 calls; they preserve native return values, exception order and short-circuiting ({ref('out/rcj/ch.py','class Trace')}). `NOT_BOUND` and `NOT_REACHED` are distinct. `chain.json` contains full exceptions for the first ten refusals per stream and overall. Its routing status is PASS only for zero refusals with complete DB coverage.

The audit-carry candidate uses the tree's `extent_receipt.content`, `p3_provenance.digest` and canonical serializer ({ref('out/rcj/ch.py','def candidate')}). It requires P's full database hash `4e8e6c04…`, unique QIDs, and source-entry digests equal to P's corresponding rows. It selects exactly N's rows carrying native `s1_source` provenance (`work/tree_r1c/student_pilot/s1_routing.py:413`), copies each complete audit entry, and changes only `content_sha256`. `cand_cmp.json` reports source/candidate hashes, uncompressed/compressed sizes, QID-set hash/count, native N digest equality, and equal/changed counts for every entry field, including box statuses and repair hashes. `cand.json.gz` contains the candidate; no kit or config binds it, and no reader consumes it.

The literal request for an existing native receipt rebuilder remains unmet: C'' supplies the content digest and admission reader, but no audit-carry receipt builder. Its `r2_materialize.materialize` only combines existing entries ({ref('work/tree_r1c/student_pilot/r2_materialize.py','extent_pin =')}; {ref('work/tree_r1c/student_pilot/r2_materialize.py',"write(output/'extents.json'")}). The helper's small receipt composer is explicit, reports `native_receipt_builder=false`, and performs no new audit. A missing source audit, changed P digest or wrong P DB hash refuses candidate publication instead of inventing certification.

Production discovery mode q calls preparation and then `r1_population.bind_prepared` ({ref('work/tree_r1c/launch_r1/production_proof.py','produced = bind_prepared')}). That function visits every prepared row of every stream through `Rows.row`, records refusals, and builds the retained population; `produce` visits the retained rows again (`work/tree_r1c/student_pilot/r1_population.py:182`, `:122`). It is not limited to draw time. `carrier_c1_run.prepare` itself applies its preparation filters, not the complete `Rows.row` chain.

Mode r ends at `rg.regenerate` and never reaches preparation or native population binding (`out/kit_qd/b/a.py:78`; {ref('out/kit_qd/b/rg.py','def regenerate')}). The first population-producing path is `s1_admission.admit` → `carrier_c1_run.prepare` → `r1_population.bind_prepared`. `chain.json.population` therefore reports `NOT_REACHED`, null prepared count/hash, and the physical routing DB count/key-set hash beside them. It does not claim sampler equality. Timings cannot report criterion (i) PASS when this population evidence is unavailable.

Mode r stages VQA, pointing and both pose row stores through the planner's native receipt closure (`out/kit_qd/b/pl.py:93`, `:112`, `:119`, `:139`). The helper additionally checks a seed-20261124 sample of 20,000 rows from each stream, with the same check counters and first-ten refusals ({ref('out/rcj/ch.py','def stores')}; {ref('out/rcj/ch.py','def run(cfg')}). It reports whether each store is staged, the source pins, total population size, draw count and unique count. It samples without replacement when possible; smaller fixture populations use explicit replacement. No RGB is decoded.

Both processor children receive read-only metadata at the root named by their own receipt ({ref('out/rcj/pc.py','def metadata_mounts')}; {ref('out/rcj/pc.py',"cmd[at:at]=['--tmpfs',value['root']]")}). Their authenticated receipt is `cc724d5e…`; the source file is `work/build24m4n/inputs/cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7:1`. Each file comes from the existing content-pin mapping, falling back to the already authenticated `<job-root>/m/<name>` stage. `x.stage` writes that stage from `resolved.model_files` and `external_metadata`/`small_files` ({ref('out/rcj/x.py',"for name, h in resolved['model_files'].items():")}); P's planner also requests these metadata hashes (`out/kit_qd/b/pl.py:155`). No new staging, download, weight bind or comparison exception is needed.

| File bound at each receipt root | SHA256 |
| --- | --- |
'''
for name,h in sorted(model['files'].items()):
 if name in pc.ASSETS:text+=f'| `{name}` | `{h}` |\n'
text+='''
The helper publishes the chain before unrelated artifacts and retains its status in timings even when artifact enumeration fails. Chain and candidate outcomes do not change the build/refusal return code. Timing-byte accounting includes `timings.json` in both aggregate and helper totals. The existing rd0 plus P sample already exceed 5 MB, so the aggregate cap can still fail; the job reports that failure rather than omitting evidence.

Validation uses synthetic rows and metadata: 15 chain/integration tests, 11 content/type tests, 10 publication tests, real N/P sandbox loader cases (40+40 PASS, 80-row fallback PASS and deliberate mismatch FAIL), sample/command/staging/mount suites, and the unchanged qd recorder suite. The real loader fixture uses a synthetic supported processor class; it proves mount visibility and native constructor/comparison execution, not production-token parity. No production-wide chain or candidate has run locally.
'''
(L/'out/CHAIN_24M4Q.md').write_text(text)
print('documentation written')
