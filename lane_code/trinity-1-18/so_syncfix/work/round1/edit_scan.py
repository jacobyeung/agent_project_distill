from pathlib import Path
p=Path('work/round1/tools/lane_code_scan.py')
s=p.read_text()
fragment=Path('work/round1/scan_fragment.py').read_text()
s=s.replace('stage, dest, flagout = sys.argv[1:4]',fragment+'stage, dest, flagout = sys.argv[1:4]',1)
s=s.replace('flags = []; copied = 0; same = 0; scanned = 0',"if os.environ.get('LCS_ROBUST_SYNC', '0') == '1':\n    robust_copy_scan(stage, dest, flagout)\n    sys.exit(0)\n\nflags = []; copied = 0; same = 0; scanned = 0",1)
p.write_text(s)
