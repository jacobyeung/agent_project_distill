from pathlib import Path
import json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23'
uploads=json.loads((B/'UPLOADS.json').read_text());kit=json.loads((D/'KIT.json').read_text())
p=B/'OPERATOR.md';s=p.read_text()
a=s.index('Mode q also requires') if 'Mode q also requires' in s else s.index('Mode q uses the explicit')
b=s.index('\n\nThe scanner checks',a)
s=s[:a]+'''Mode q uses the explicit pinned declaration `r1_training.routing_slices: "deferred_first_boundary"`.
The resolver binds P's step-400 routing receipt and preserves N's non-routing inputs. The request's
`routing_base` must match the config. Native admission regenerates S1 and keeps that output as
`streams.routing`. No routing envelope may be supplied under this declaration.
The card assigns 64 routing slots to the regenerated base and zero to every deferred routing cell.
The initial population is explicitly incomplete and cannot supply training batches. Native
population binding must replace it with complete filtered rows before admission.
Recovery, new absolute-distance rows, units, both coverage families and camera wording enter at
the first boundary. P's existing absolute-distance rows stay in the base.
The production stores, frames and large model remain required. Native authentication and all
row removals, wording exclusions, room/K1 checks and component-evidence boundaries remain active.
The source patch and build-22 merge instructions are in `../../out/MINIMAL_TREE.patch` and
`../../out/MINIMAL_MERGE_NOTES.md`. The kit's new upload list is `../../out/UPLOADS_NEW.json`.
''' + s[b:]
s=s.replace('`../build21g/SCAN.json` and `../build21g/UPLOAD_DIFF.json`','`../build23/SCAN.json` and `../build23/UPLOAD_DIFF.json`')
s=s.replace('Those earlier binds succeeded in job 173051. Their values and every ordered destination are in','Their values and every ordered destination are in')
a=s.index('Upload total:')
s=s[:a]+f'''Upload total: {uploads['total_bytes']} bytes in {len(uploads['files'])} files (source: `UPLOADS.json`).

The tree seal is `{kit['tree_seal']}`. The kit q seal is `{kit['kit_seal']}`.
The inherited r1 kit retains its base seal; this delivery certifies q only.
`../build23/rebuild_kit.py` regenerates MINIMAL q from its retained authenticated base inventory.
`../build23/metadata.py` records the exact changed uploads and invariant checks.

Run the focused suites with `B21C_PORTABLE=1` and the supplied CPU environment.
The packaged dependency map redirects authenticated fixture bytes without changing their identities.
The synthetic constant-readout fixture is included. `../build23/PACKAGE_ORIGIN.json` records the
origin for relocating generated fixture paths. The capacity script is `../build23/native23.py`;
it reconstructs its own synthetic databases and model payloads, which the package omits.
See `../../out/BUILD23_REPORT.md` for validation and the production boundaries that remain.
'''
p.write_text(s)
(D/'PACKAGE_ORIGIN.json').write_text(json.dumps(dict(workspace=str(L)),indent=2)+'\n')
