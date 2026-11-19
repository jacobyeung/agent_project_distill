"""Keep the inherited report entry point bound to the current evidence writer."""
from pathlib import Path
B=Path(__file__).resolve().parent
(B/'report.py').write_text('"""Publish the build-8 final evidence."""\nimport runpy\nfrom pathlib import Path\nrunpy.run_path(str(Path(__file__).with_name("report8.py")),run_name="__main__")\n')
with (B/'DECISIONS.md').open('a') as f:
 f.write('\n- Packet setup options: retain broken relocated references, copy the row slices, or reference their existing lane-local source files. Default: use read-only symlinks with the existing hashes, and use a fresh pytest directory so retained process IDs cannot collide. Run the corrected packet once before package groups; retain the failed setup evidence. No assertion changes.\n')
 f.write('\n- The dense-pose admission predicate still binds the legacy all_frames32 contract. Options: invent a longer-clip contract, or retain the guard pending its admitted source manifest. Default: retain the guard and name FRAME64_DENSE_POSE_ADMISSION_UNQUALIFIED.\n')
