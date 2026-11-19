from pathlib import Path
import difflib,hashlib,json,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build23b';T=L/'work/tree_r1';A=L/'attic/build23'
base=json.loads((A/'PACKAGE_MANIFEST.json').read_text())['files']
changed={name.removeprefix('work/tree_r1/'):L/name for name,v in base.items() if name.startswith('work/tree_r1/') and hashlib.sha256((L/name).read_bytes()).hexdigest()!=v['sha256']}
assert len(changed)==7,changed
archive_path=next((A/'q/k').glob('t_b262e7a7*.tar'))
diff=[];old={}
with tarfile.open(archive_path,'r:gz') as archive:
 for name,p in sorted(changed.items()):
  raw=archive.extractfile(name).read().decode();old[name]=raw
  diff.extend(difflib.unified_diff(raw.splitlines(True),p.read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(L/'out/MINIMAL_TREE.patch').write_text(''.join(diff))
(D/'BASE_SOURCES.json').write_text(json.dumps(old))
(D/'TREE_CHANGES.json').write_text(json.dumps(dict(base_tree='b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8',files=sorted(changed)),indent=2)+'\n')
(L/'out/MINIMAL_MERGE_NOTES.md').write_text('''The pinned MINIMAL declaration is `r1_training.routing_slices: "deferred_first_boundary"`.
Apply MINIMAL_TREE.patch against tree b262e7a7. It changes seven files listed in work/build23b/TREE_CHANGES.json.
The central check is `r1_coverage.deferred`. It returns immediately for FULL and validates every MINIMAL binding before native row readers run.

Refused fields:
- Config and request `row_slice_inputs`: only an empty mapping is allowed; every named entry refuses.
- Config and request `routing_inputs`: even an empty or null supplied field refuses.
- Config and request `row_sources`: every entry except the two non-routing audit entries refuses. This includes all SLICE_CELLS, coverage PINS, camera wording, EXTRA_PINS, and unknown future slice names.
- Config and request `source_membership.sources`, population membership, and composed membership attached to `streams.routing` or `routing_base`: refuse before source rows are read.
- The training mix, sampler card, and request card: every deferred cell must have zero rows and zero ceiling. Counts and indices must also be zero, including deferred cells absent from the card.
- Source membership supplied directly to population production receives the same central check.
The refusal prefix is `R1_MINIMAL_SLICE_BOUND:<field>:<name>`. Existing base-identity and invalid-declaration refusals remain.

Only `row_sources.room` and `row_sources.room_programs_excluded` remain as audit provenance. FULL never composes these entries.
The empty source-membership catalog carries no QIDs. Wording exclusions, removal lists, room authority, component evidence, P's S1 catalog, and staged hash inventories retain their own checks; they do not select new routing slices.
The kit's active source catalog must omit routing entries. Its room audit binds that catalog and has an empty slices map while preserving the unchanged store certification.
The request and config must bind the same authenticated P routing base. Native S1 regeneration supplies the retained routing stream.
The routing_base cell receives 64 slots per step. P's existing distance rows remain in that base.

Merge build 22 as follows:
- Preserve its EXTRA_PINS and wording exclusions. The central check dynamically includes EXTRA_PINS and rejects every unknown catalog entry except the two named audit entries.
- Preserve its FULL camera composition and membership logic. MINIMAL must reach the central check before enumerating or composing sources.
- Preserve direction twins, reviewed relative counts, the 109-row removal list, K1 rules, source-key checks, removal ordering, and all store/room checks.
- Keep every camera/coverage/recovery/distance/units cell at zero in MINIMAL, even if relabeled into another stream.
- Keep the central check at production_proof, both entry paths, s1_admission, both population paths, both room paths, and build before it replaces row_slice_inputs.
- Entry checks inline fields before staging and authenticated metadata after localization; native row readers run only after both checks.
Regenerate the merged catalogs, room audit, card, source archive, and kit seals. A changed VQA store requires its own room audit.
The resolver's identity checks, P opener rows, step-544 lineage, and DEFERRED official boundary remain unchanged.
GO remains false. Production frame-host and GPU execution remain required.
''')
print(json.dumps(dict(files=len(changed),patch_bytes=(L/'out/MINIMAL_TREE.patch').stat().st_size)))
